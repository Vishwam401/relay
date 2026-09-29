import argparse
import asyncio
from datetime import datetime, timezone
import json
import os
import re
import statistics
import subprocess
import sys
import time
from typing import Optional
import asyncpg
import httpx

# Pre-parse DATABASE_URL from .env
def get_db_urls():
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    url = "postgresql+asyncpg://postgres:relay@localhost:5433/relay_w5d5"
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("DATABASE_URL="):
                    val = line.strip().split("=", 1)[1]
                    url = re.sub(r"/relay$", "/relay_w5d5", val)
                    break
    if os.environ.get("DATABASE_URL"):
        url = re.sub(r"/relay$", "/relay_w5d5", os.environ["DATABASE_URL"])
    
    asyncpg_url = url.replace("postgresql+asyncpg://", "postgresql://").replace("postgresql+psycopg://", "postgresql://")
    sqlalchemy_url = "postgresql+asyncpg://" + asyncpg_url.split("://", 1)[1]
    return asyncpg_url, sqlalchemy_url


ASYNCPG_DB_URL, SQLALCHEMY_DB_URL = get_db_urls()

def now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


class ProbeLogger:
    def __init__(self, filepath: str):
        self.filepath = filepath
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self.f = open(filepath, "a", encoding="utf-8")

    def log(self, msg: str):
        line = f"[{now_ts()}] {msg}"
        print(line, flush=True)
        self.f.write(line + "\n")
        self.f.flush()

    def close(self):
        self.f.close()


async def wait_for_sink_health(url: str, timeout: float = 8.0) -> bool:
    start = time.perf_counter()
    async with httpx.AsyncClient() as client:
        while time.perf_counter() - start < timeout:
            try:
                resp = await client.get(f"{url}/health", timeout=1.0)
                if resp.status_code == 200:
                    return True
            except Exception:
                await asyncio.sleep(0.2)
    return False


def kill_process_tree(pid: Optional[int]):
    if pid is None:
        return
    try:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(pid)], capture_output=True, text=True)
    except Exception:
        pass


def count_relay_python() -> int:
    try:
        res = subprocess.run(
            ["powershell", "-Command", "(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -like '*PROJECTS\\relay*' -and $_.ProcessId -ne " + str(os.getpid()) + " } | Measure-Object).Count"],
            capture_output=True,
            text=True
        )
        return int(res.stdout.strip() or "0")
    except Exception:
        return 0


async def run_poller(poll_log_path: str, stop_event: asyncio.Event):
    poll_conn = await asyncpg.connect(ASYNCPG_DB_URL, server_settings={"application_name": "poller_w5d5"})
    with open(poll_log_path, "a", encoding="utf-8") as f:
        while not stop_event.is_set():
            t_str = now_ts()
            # 1. pg_stat_activity
            act_rows = await poll_conn.fetch(
                """
                SELECT 
                    application_name, 
                    pid, 
                    state, 
                    wait_event_type, 
                    wait_event, 
                    pg_blocking_pids(pid) as blockers,
                    now() - query_start as query_duration,
                    left(query, 40) as query_snippet
                FROM pg_stat_activity
                WHERE datname = 'relay_w5d5'
                  AND application_name IN ('sink_w5d5', 'dispatcher_w5d5', 'holder_w5d5')
                ORDER BY application_name, pid;
                """
            )
            # 2. pg_locks for outbox
            lock_rows = await poll_conn.fetch(
                """
                SELECT 
                    a.application_name,
                    l.mode,
                    l.granted
                FROM pg_locks l
                JOIN pg_stat_activity a ON l.pid = a.pid
                WHERE a.datname = 'relay_w5d5'
                  AND l.relation = 'outbox'::regclass
                ORDER BY a.application_name;
                """
            )

            if not act_rows and not lock_rows:
                f.write(f"[{t_str}] rows=0\n")
            else:
                for r in act_rows:
                    blockers_str = ",".join(str(b) for b in r['blockers']) if r['blockers'] else "none"
                    f.write(f"[{t_str}] [act] app={r['application_name']}|pid={r['pid']}|state={r['state']}|wait_type={r['wait_event_type']}|wait_event={r['wait_event']}|blockers=[{blockers_str}]|dur={r['query_duration']}|query={r['query_snippet']}\n")
                for lr in lock_rows:
                    f.write(f"[{t_str}] [lock] app={lr['application_name']}|mode={lr['mode']}|granted={lr['granted']}\n")
            f.flush()
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=0.25)
            except asyncio.TimeoutError:
                pass
    await poll_conn.close()


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=["A", "B", "C"], required=True)
    parser.add_argument("--hold", type=float, required=True)
    args = parser.parse_args()

    arm = args.arm
    hold_sec = args.hold
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")

    os.makedirs("logs", exist_ok=True)
    probe_log_file = f"logs/w5d5_{arm}_{run_id}_probe.log"
    sink_log_file = f"logs/w5d5_{arm}_{run_id}_sink.log"
    disp_log_file = f"logs/w5d5_{arm}_{run_id}_dispatcher.log"
    poll_log_file = f"logs/w5d5_{arm}_{run_id}_poll.log"

    logger = ProbeLogger(probe_log_file)
    logger.log(f"=== CHAIN PROBE START: ARM {arm} (hold={hold_sec}s, run_id={run_id}) ===")

    # Requirement 3: Pre-flight check on current_database()
    setup_conn = await asyncpg.connect(ASYNCPG_DB_URL, server_settings={"application_name": "probe_setup"})
    curr_db = await setup_conn.fetchval("SELECT current_database();")
    logger.log(f"current_database={curr_db}")
    if curr_db != "relay_w5d5":
        logger.log(f"ERROR: Expected relay_w5d5, got {curr_db}. Exiting.")
        sys.exit(1)

    # Requirement 4: Setup truncate & insert outbox if Arm B/C
    await setup_conn.execute("TRUNCATE outbox, sink_deliveries RESTART IDENTITY CASCADE;")
    logger.log("TRUNCATE outbox, sink_deliveries RESTART IDENTITY completed")
    if arm in ("B", "C"):
        await setup_conn.execute(
            """
            INSERT INTO outbox (job_id, payload, effect_key, attempts, created_at)
            VALUES 
                (42, '{}'::jsonb, 'job:42', 0, now()),
                (42, '{}'::jsonb, 'job:42', 0, now());
            """
        )
        logger.log("Inserted 2 outbox rows: job_id=42, effect_key='job:42'")

    # Requirement 5: Start Sink subprocess with stdout+stderr in sink_log_file
    sink_env = os.environ.copy()
    sink_env["RELAY_PROCESS_NAME"] = "sink_w5d5"
    sink_env["RELAY_POOL_SIZE"] = "2"
    sink_env["RELAY_MAX_OVERFLOW"] = "0"
    sink_env["RELAY_POOL_TIMEOUT"] = "3.0"
    sink_env["SINK_DEDUP"] = "1"
    sink_env["PYTHONUNBUFFERED"] = "1"
    sink_env["DATABASE_URL"] = SQLALCHEMY_DB_URL

    sink_log_handle = open(sink_log_file, "a", encoding="utf-8")
    sink_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.sink:app", "--port", "8001"],
        env=sink_env,
        stdout=sink_log_handle,
        stderr=subprocess.STDOUT,
        text=True
    )
    logger.log(f"Started sink_w5d5 subprocess pid={sink_proc.pid}")

    sink_ok = await wait_for_sink_health("http://127.0.0.1:8001", timeout=8.0)
    if not sink_ok:
        logger.log("FATAL: Sink failed to become healthy on port 8001")
        kill_process_tree(sink_proc.pid)
        sys.exit(1)
    logger.log("Sink healthy on /health")

    # Read resolved_db from sink log
    sink_log_handle.flush()
    with open(sink_log_file, "r", encoding="utf-8", errors="replace") as sf:
        for sline in sf:
            if "resolved_db=" in sline:
                logger.log(f"sink_log: {sline.strip()}")
                break

    disp_proc = None
    disp_log_handle = None
    poller_task = None
    poller_stop = asyncio.Event()

    try:
        # Requirement 6: Arm A preamble (10 uncontended sequential calls)
        if arm == "A":
            logger.log("=== ARM A PREAMBLE: 10 UNCONTENDED POST /deliver ===")
            latencies = []
            async with httpx.AsyncClient() as client:
                for i in range(1, 11):
                    key = f"pre:{run_id}:{i}"
                    t0 = time.perf_counter()
                    resp = await client.post("http://127.0.0.1:8001/deliver", json={"idempotency_key": key, "job_id": i}, timeout=5.0)
                    elapsed = time.perf_counter() - t0
                    latencies.append(elapsed)
                    logger.log(f"uncontended_req={i}|key={key}|status={resp.status_code}|elapsed_s={elapsed:.4f}")
            first_lat = latencies[0]
            rest_median = statistics.median(latencies[1:])
            max_lat = max(latencies)
            logger.log(f"uncontended_summary: first_s={first_lat:.4f}|median_remaining_s={rest_median:.4f}|max_s={max_lat:.4f}")

        # Requirement 7: Start raw Holder
        holder_conn = await asyncpg.connect(ASYNCPG_DB_URL, server_settings={"application_name": "holder_w5d5"})
        holder_pid = await holder_conn.fetchval("SELECT pg_backend_pid();")
        holder_tr = holder_conn.transaction()
        await holder_tr.start()
        await holder_conn.execute(
            """
            INSERT INTO sink_deliveries (idempotency_key, job_id, body, received_at)
            VALUES ('job:42', 42, '{}'::jsonb, now());
            """
        )
        t_holder_start = time.perf_counter()
        logger.log(f"holder_start: pid={holder_pid}|key=job:42")

        # Start Poller
        poller_task = asyncio.create_task(run_poller(poll_log_file, poller_stop))

        # Requirement 8 & 9: Arm A background POST vs Arms B/C Dispatcher
        if arm == "A":
            anchor_time = t_holder_start
            logger.log("anchor: set_to_holder_start")

            async def arm_a_contended_post():
                t0 = time.perf_counter()
                async with httpx.AsyncClient() as client:
                    resp = await client.post("http://127.0.0.1:8001/deliver", json={"idempotency_key": "job:42", "job_id": 42}, timeout=15.0)
                elapsed = time.perf_counter() - t0
                return resp.status_code, elapsed

            contended_task = asyncio.create_task(arm_a_contended_post())

            # Wait until hold expires
            sleep_duration = max(0.0, (anchor_time + hold_sec) - time.perf_counter())
            await asyncio.sleep(sleep_duration)

            # Rollback holder
            await holder_tr.rollback()
            await holder_conn.close()
            logger.log("holder_end: rolled_back")

            # Wait for contended POST to complete
            post_status, post_elapsed = await contended_task
            logger.log(f"contended_post_result: status={post_status}|elapsed_s={post_elapsed:.4f}")

        else:
            # Arms B and C: Dispatcher
            disp_env = os.environ.copy()
            disp_env["RELAY_PROCESS_NAME"] = "dispatcher_w5d5"
            disp_env["SINK_URL"] = "http://127.0.0.1:8001/deliver"
            disp_env["PYTHONUNBUFFERED"] = "1"
            disp_env["DATABASE_URL"] = SQLALCHEMY_DB_URL

            disp_log_handle = open(disp_log_file, "a", encoding="utf-8")
            disp_proc = subprocess.Popen(
                [sys.executable, "-u", "-m", "src.dispatcher"],
                env=disp_env,
                stdout=disp_log_handle,
                stderr=subprocess.STDOUT,
                text=True
            )
            logger.log(f"Started dispatcher_w5d5 subprocess pid={disp_proc.pid}")

            # Monitor dispatcher log until first "Attempting dispatch" appears (Anchor)
            anchor_time = None
            start_wait = time.perf_counter()
            while time.perf_counter() - start_wait < 10.0:
                disp_log_handle.flush()
                with open(disp_log_file, "r", encoding="utf-8", errors="replace") as df:
                    content = df.read()
                    if "Attempting dispatch:" in content:
                        anchor_time = time.perf_counter()
                        logger.log("anchor: first_attempting_dispatch_observed")
                        break
                await asyncio.sleep(0.05)

            if anchor_time is None:
                anchor_time = time.perf_counter()
                logger.log("anchor: fallback_timeout_after_10s")

            # Sleep until anchor + hold_sec
            sleep_dur = max(0.0, (anchor_time + hold_sec) - time.perf_counter())
            await asyncio.sleep(sleep_dur)

            # Rollback holder
            await holder_tr.rollback()
            await holder_conn.close()
            logger.log("holder_end: rolled_back")

        # Requirement 12: Wait until holder_end + 8s for tail activity
        logger.log("waiting_8s_tail_after_holder_end")
        await asyncio.sleep(8.0)

        # Stop poller
        poller_stop.set()
        if poller_task:
            await poller_task

        # Requirement 12: Read final state
        outbox_rows = await setup_conn.fetch("SELECT id, attempts, dispatched_at FROM outbox ORDER BY id;")
        for ob in outbox_rows:
            logger.log(f"final_outbox: id={ob['id']}|attempts={ob['attempts']}|dispatched_at={ob['dispatched_at']}")

        sink_rows = await setup_conn.fetch("SELECT id, received_at FROM sink_deliveries WHERE idempotency_key='job:42' ORDER BY id;")
        for sr in sink_rows:
            logger.log(f"final_sink_deliveries: id={sr['id']}|received_at={sr['received_at']}")

        # Census of sink log
        sink_log_handle.flush()
        result_counts = {}
        exception_counts = {}
        access_lines_count = 0
        with open(sink_log_file, "r", encoding="utf-8", errors="replace") as sf:
            for sline in sf:
                if 'HTTP/' in sline:
                    access_lines_count += 1
                res_match = re.search(r"result=(\w+)", sline)
                if res_match:
                    res_val = res_match.group(1)
                    result_counts[res_val] = result_counts.get(res_val, 0) + 1
                if "Error" in sline or "Exception" in sline:
                    exc_match = re.search(r"([\w\.]+(?:Error|Exception))", sline)
                    if exc_match:
                        exc_name = exc_match.group(1)
                        exception_counts[exc_name] = exception_counts.get(exc_name, 0) + 1

        logger.log(f"sink_census: access_lines={access_lines_count}|results={json.dumps(result_counts)}|exceptions={json.dumps(exception_counts)}")

    finally:
        # Requirement 13: Clean kill
        poller_stop.set()
        kill_process_tree(sink_proc.pid)
        if sink_log_handle:
            sink_log_handle.close()

        if disp_proc:
            kill_process_tree(disp_proc.pid)
        if disp_log_handle:
            disp_log_handle.close()

        await setup_conn.close()
        remaining_py = count_relay_python()
        logger.log(f"cleanup: remaining_relay_python={remaining_py}")
        logger.close()


if __name__ == "__main__":
    asyncio.run(main())
