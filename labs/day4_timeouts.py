import asyncio
import socket
import time
import httpx
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import uvicorn
import threading

# Experiment A: Connect Timeout on Unreachable IP (Blackhole)
async def exp_a_blackhole():
    print("\n========================================================")
    print("EXP A: Connect Timeout (Unreachable IP: 10.255.255.1)")
    print("========================================================")
    async with httpx.AsyncClient(timeout=httpx.Timeout(connect=1.0, read=5.0, write=5.0, pool=5.0)) as client:
        start = time.time()
        try:
            await client.get("http://10.255.255.1")
            return ("Exp A (Blackhole)", 0, "No Error")
        except Exception as e:
            elapsed = time.time() - start
            err_class = f"{type(e).__module__}.{type(e).__name__}"
            print(f"Time Taken  : {elapsed:.3f}s")
            print(f"Error Type  : {err_class}")
            print(f"Error Msg   : {e}")
            return ("Exp A (Blackhole IP)", elapsed, err_class)

# Experiment B: Connection Refused (Closed Port)
async def exp_b_refused():
    print("\n========================================================")
    print("EXP B: Connection Refused (Closed Port: 127.0.0.1:9999)")
    print("========================================================")
    async with httpx.AsyncClient(timeout=httpx.Timeout(connect=1.0, read=5.0, write=5.0, pool=5.0)) as client:
        start = time.time()
        try:
            await client.get("http://127.0.0.1:9999")
            return ("Exp B (Closed Port)", 0, "No Error")
        except Exception as e:
            elapsed = time.time() - start
            err_class = f"{type(e).__module__}.{type(e).__name__}"
            print(f"Time Taken  : {elapsed:.3f}s")
            print(f"Error Type  : {err_class}")
            print(f"Error Msg   : {e}")
            return ("Exp B (Closed Port)", elapsed, err_class)

# Experiment C: Read Timeout on Slow Endpoint
async def exp_c_read_timeout(endpoint_url="http://localhost:8000/blocking"):
    print("\n========================================================")
    print(f"EXP C: Read Timeout (Read=0.5s on slow endpoint: {endpoint_url})")
    print("========================================================")
    async with httpx.AsyncClient(timeout=httpx.Timeout(connect=5.0, read=0.5, write=5.0, pool=5.0)) as client:
        start = time.time()
        try:
            await client.get(endpoint_url)
            return ("Exp C (Read Timeout)", 0, "No Error")
        except Exception as e:
            elapsed = time.time() - start
            err_class = f"{type(e).__module__}.{type(e).__name__}"
            print(f"Time Taken  : {elapsed:.3f}s")
            print(f"Error Type  : {err_class}")
            print(f"Error Msg   : {e}")
            return ("Exp C (Read Timeout)", elapsed, err_class)

# Experiment E: Total Deadline Trap (Slow Drip Server)
# Server sends 1 byte every 0.3s. Read timeout=0.5s NEVER fires! Total timeout (2s) catches it!
slow_app = FastAPI()

@slow_app.get("/slow-drip")
async def slow_drip():
    async def generate_bytes():
        for i in range(10):
            await asyncio.sleep(0.3) # Gap 0.3s is less than read_timeout 0.5s!
            yield f"data: chunk {i}\n"
    return StreamingResponse(generate_bytes())

def run_slow_server():
    uvicorn.run(slow_app, host="127.0.0.1", port=8001, log_level="warning")

async def exp_e_total_deadline_trap():
    print("\n========================================================")
    print("EXP E: Total Deadline Trap (Slow Drip Server 0.3s gap vs Read=0.5s)")
    print("========================================================")
    
    # Start slow drip server in daemon thread
    t = threading.Thread(target=run_slow_server, daemon=True)
    t.start()
    await asyncio.sleep(1.0) # Wait for server to start

    # Test 1: Only read timeout (0.5s) -> Read timeout NEVER fires because 0.3s < 0.5s!
    print("--- Test E1: Per-byte read timeout 0.5s (No total deadline) ---")
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(connect=5.0, read=0.5, write=5.0, pool=5.0)) as client:
            res = await client.get("http://127.0.0.1:8001/slow-drip")
            elapsed = time.time() - start
            print(f"Outcome: Request completed after {elapsed:.2f}s! Read timeout NEVER fired!")
    except Exception as e:
        elapsed = time.time() - start
        print(f"Outcome: Failed after {elapsed:.2f}s with {type(e).__name__}")

    # Test 2: Total overall deadline (1.0s) -> Catches the slow drip trap!
    print("\n--- Test E2: Overall total deadline 1.0s (Total timeout set) ---")
    start = time.time()
    try:
        # Set overall total timeout = 1.0s
        async with httpx.AsyncClient(timeout=httpx.Timeout(1.0, connect=5.0, read=0.5)) as client:
            res = await client.get("http://127.0.0.1:8001/slow-drip")
            elapsed = time.time() - start
            print(f"Outcome: Completed after {elapsed:.2f}s")
    except Exception as e:
        elapsed = time.time() - start
        print(f"Outcome: Total Timeout caught slow drip after {elapsed:.2f}s! Error: {type(e).__name__}")

if __name__ == "__main__":
    print("--- DAY 4: COMPREHENSIVE EXPERIMENTS (A, B, C, D, E) ---")
    res_a = asyncio.run(exp_a_blackhole())
    res_b = asyncio.run(exp_b_refused())
    
    # Exp D: Side-by-Side Summary
    print("\n========================================================")
    print("EXP D: Error Types Side-by-Side Comparison")
    print("========================================================")
    print(f"{'Experiment':<25} | {'Time (s)':<10} | {'Exact Error Class'}")
    print("-" * 60)
    print(f"{res_a[0]:<25} | {res_a[1]:<10.3f} | {res_a[2]}")
    print(f"{res_b[0]:<25} | {res_b[1]:<10.3f} | {res_b[2]}")

    # Exp E: Total Deadline Trap Demonstration
    asyncio.run(exp_e_total_deadline_trap())
