import asyncio
import os
import re
import time
from datetime import datetime, timezone
import httpx

API_URL = "http://127.0.0.1:8000/slow-hold?seconds=8"
API_LOG_FILE = "logs/w5d4_step1_api.log"

run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
os.makedirs("logs", exist_ok=True)
LOG_FILE = f"logs/w5d4_step2_{run_id}.log"


def log(msg: str):
    print(msg, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
        f.flush()


def extract_api_error_class() -> str:
    """Find the most recent exception class from API log."""
    if not os.path.exists(API_LOG_FILE):
        return "api log not found"
    try:
        with open(API_LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        for line in reversed(lines):
            if "TimeoutError" in line:
                return line.strip()
            if "Exception:" in line or "Error:" in line:
                return line.strip()
    except Exception as e:
        return f"error reading log: {e}"
    return "no exception found in api log"


async def send_request(client: httpx.AsyncClient, req_id: int):
    t0 = time.perf_counter()
    try:
        resp = await client.get(API_URL, timeout=15.0)
        t1 = time.perf_counter()
        elapsed = t1 - t0
        return {
            "req_id": req_id,
            "status": resp.status_code,
            "elapsed_s": elapsed,
            "error": None if resp.status_code == 200 else f"HTTP {resp.status_code}",
        }
    except Exception as e:
        t1 = time.perf_counter()
        elapsed = t1 - t0
        return {
            "req_id": req_id,
            "status": "CLIENT_ERR",
            "elapsed_s": elapsed,
            "error": f"{type(e).__name__}: {e}",
        }


async def main():
    log("================================================================================")
    log("=== STEP 2: POOL SATURATION TIMEOUT PROBE (Week 5 Din 4) ===")
    log("================================================================================")
    log(f"Run ID: {run_id}")
    log(f"Target: {API_URL}")
    log("Database Setting: echo=True (hardcoded in src/database.py, all latencies carry echo=True)\n")

    log("Firing 3 concurrent requests to /slow-hold?seconds=8...")
    async with httpx.AsyncClient() as client:
        tasks = [send_request(client, i) for i in range(1, 4)]
        results = await asyncio.gather(*tasks)

    log("\n=== EMPIRICAL MEASUREMENT RESULTS (per request) ===")
    log(f"{'Req #':<8} | {'HTTP Status':<12} | {'Elapsed Time (echo=True)':<25} | {'Observed Result'}")
    log("-" * 80)
    for r in sorted(results, key=lambda x: x["elapsed_s"]):
        log(f"Req {r['req_id']:<4} | {str(r['status']):<12} | {r['elapsed_s']:<18.4f} s    | {r['error'] or 'Completed (200 OK)'}")
    log("-" * 80)

    # Extract backend exception class
    api_exc = extract_api_error_class()
    log("\n=== BACKEND EXCEPTION CLASS (from logs/w5d4_step1_api.log) ===")
    log(f"Backend Exception: {api_exc}")

    # Latency decomposition analysis
    failed_reqs = [r for r in results if r["status"] != 200]
    if failed_reqs:
        failed_elapsed = failed_reqs[0]["elapsed_s"]
        log("\n=== SATURATION TIMEOUT SUMMARY ===")
        log(f"Observed timeout latency: {failed_elapsed:.4f} s (echo=True)")


if __name__ == "__main__":
    asyncio.run(main())
