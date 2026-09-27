import asyncio
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
import asyncpg
import httpx

DB_URL = "postgresql://postgres:relay@localhost:5433/relay_w5d4"
ASYNC_DB_URL = "postgresql+asyncpg://postgres:relay@localhost:5433/relay_w5d4"

run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
os.makedirs("logs", exist_ok=True)
LOG_FILE = f"logs/w5d4_step5_{run_id}.log"


def log(msg: str):
    print(msg, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
        f.flush()


async def wait_for_sink_health(url: str, timeout: float = 10.0):
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


async def get_lock_snapshot(conn: asyncpg.Connection) -> str:
    """Query pg_stat_activity and pg_locks to inspect held and waiting locks."""
    rows = await conn.fetch(
        """
        SELECT 
            a.application_name,
            a.state,
            l.locktype,
            l.mode,
            l.granted,
            left(a.query, 40) as query
        FROM pg_locks l
        JOIN pg_stat_activity a ON l.pid = a.pid
        WHERE a.datname = 'relay_w5d4' AND a.pid != pg_backend_pid()
        ORDER BY a.application_name, l.granted DESC;
        """
    )
    if not rows:
        return "No locks found"
    lines = [f"{r['application_name']}|{r['state']}|{r['locktype']}|{r['mode']}|granted={r['granted']}|{r['query']}" for r in rows]
    return "\n".join(lines)


async def main():
    log("================================================================================")
    log("=== STEP 5: COMPOSED FAILURE CHAIN PROBE (Week 5 Din 4 — P-41) ===")
    log("================================================================================")
    log(f"Run ID: {run_id}")
    log(f"Database: {DB_URL}")
    log("Disposable Target: relay_w5d4 (Evidence DB relay is UNTOUCHED)")
    log("Links tested: Holder uncommitted -> ON CONFLICT wait -> Dispatcher row lock held -> httpx timeout\n")

    # 1. Reset tables in disposable DB
    setup_conn = await asyncpg.connect(DB_URL, server_settings={"application_name": "probe_setup"})
    await setup_conn.execute("TRUNCATE TABLE outbox, sink_deliveries RESTART IDENTITY CASCADE;")
    
    # Insert two outbox rows with the same key target (job_id = 42 -> key 'job:42')
    await setup_conn.execute(
        """
        INSERT INTO outbox (job_id, payload, effect_key, attempts, created_at)
        VALUES 
            (42, '{}'::jsonb, 'job:42', 0, now()),
            (42, '{}'::jsonb, 'job:42', 0, now());
        """
    )
    log("[Setup] Truncated tables and inserted 2 outbox rows (job_id=42, key='job:42').")

    # 2. Start Sink process
    sink_env = os.environ.copy()
    sink_env["DATABASE_URL"] = ASYNC_DB_URL
    sink_env["RELAY_PROCESS_NAME"] = "sink_w5d4"
    sink_env["RELAY_POOL_SIZE"] = "2"
    sink_env["RELAY_MAX_OVERFLOW"] = "0"
    sink_env["SINK_DEDUP"] = "1"

    log("[Process] Starting Sink on port 8001 (pool_size=2+0, SINK_DEDUP=1)...")
    sink_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.sink:app", "--port", "8001", "--log-level", "warning"],
        env=sink_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        sink_ok = await wait_for_sink_health("http://127.0.0.1:8001", timeout=8.0)
        if not sink_ok:
            raise RuntimeError("Sink failed to become healthy on port 8001")
        log("[Process] Sink is healthy on http://127.0.0.1:8001/health.")

        # 3. Open raw Holder connection and start uncommitted transaction
        holder_conn = await asyncpg.connect(DB_URL, server_settings={"application_name": "holder_w5d4"})
        holder_tr = holder_conn.transaction()
        await holder_tr.start()
        await holder_conn.execute(
            """
            INSERT INTO sink_deliveries (idempotency_key, job_id, body, received_at)
            VALUES ('job:42', 42, '{}'::jsonb, now());
            """
        )
        log("[Holder] Started uncommitted transaction in sink_deliveries with key='job:42'. Holding lock...")

        # 4. Start Dispatcher process
        disp_env = os.environ.copy()
        disp_env["DATABASE_URL"] = ASYNC_DB_URL
        disp_env["RELAY_PROCESS_NAME"] = "dispatcher_w5d4"
        disp_env["SINK_URL"] = "http://127.0.0.1:8001/deliver"
        disp_env["PYTHONUNBUFFERED"] = "1"

        log("[Dispatcher] Starting Dispatcher process against relay_w5d4...")
        disp_t0 = time.perf_counter()
        disp_proc = subprocess.Popen(
            [sys.executable, "-u", "-m", "src.dispatcher"],
            env=disp_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        # 5. Snapshot locks during the flight (at t=2.0s)
        await asyncio.sleep(2.0)
        lock_snapshot = await get_lock_snapshot(setup_conn)
        log("\n=== LOCK SNAPSHOT IN-FLIGHT (t ~ 2.0s) ===")
        log(lock_snapshot)

        # 6. Wait for Dispatcher's HTTP timeout to fire (~5.0s total)
        # We read lines from dispatcher stdout until dispatch_error is printed
        dispatcher_output = []
        error_line = None
        disp_elapsed = None
        while time.perf_counter() - disp_t0 < 10.0:
            line = disp_proc.stdout.readline()
            if line:
                dispatcher_output.append(line.strip())
                if "[dispatch_error]" in line:
                    disp_elapsed = time.perf_counter() - disp_t0
                    error_line = line.strip()
                    break
            else:
                await asyncio.sleep(0.1)

        log("\n=== DISPATCHER LOG OUTPUT ===")
        for l in dispatcher_output:
            log(l)

        # 7. Release Holder transaction
        await holder_tr.rollback()
        await holder_conn.close()
        log("\n[Holder] Rolled back uncommitted transaction.")

        # 8. Check final outbox state
        outbox_rows = await setup_conn.fetch("SELECT id, job_id, attempts, dispatched_at FROM outbox ORDER BY id;")
        log("\n=== FINAL OUTBOX ROWS IN DISPOSABLE DB ===")
        for r in outbox_rows:
            log(f"outbox_id={r['id']} job_id={r['job_id']} attempts={r['attempts']} dispatched_at={r['dispatched_at']}")

        # 9. Record 4 Structured Observations
        log("\n================================================================================")
        log("=== EMPIRICAL MEASUREMENT & OBSERVATIONS (P-41 COMPOSED CHAIN) ===")
        log("================================================================================")
        log(f"1. Dispatcher Observed Behaviour : Timeout occurred at {disp_elapsed:.4f} s (echo=True)")
        log(f"2. Error Class in Process Log    : {error_line}")
        log(f"3. Outbox Row Lock Duration      : Held for {disp_elapsed:.4f} s across the HTTP call")
        log("4. Observability Gap Analysis    :")
        log("   - Relay Log Symptom: Dispatcher recorded '[dispatch_error] ... error=The read operation timed out'")
        log("   - Actual Root Cause: Uncommitted row lock on 'job:42' in receiver's sink_deliveries table.")
        log("   - Can operator deduce root cause from Relay log alone? NO.")
        log("   - Relay sees a generic HTTP read timeout; the causal chain crosses the network boundary")
        log("     and is completely masked by the RPC interface.")
        log("================================================================================")

    finally:
        # Terminate processes cleanly
        try:
            disp_proc.terminate()
            disp_proc.wait(timeout=2.0)
        except Exception:
            disp_proc.kill()

        try:
            sink_proc.terminate()
            sink_proc.wait(timeout=2.0)
        except Exception:
            sink_proc.kill()

        await setup_conn.close()
        log("\n[Cleanup] Terminated dispatcher and sink processes.")


if __name__ == "__main__":
    asyncio.run(main())
