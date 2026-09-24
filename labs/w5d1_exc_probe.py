import asyncio
import os
import socket
import sys
import time
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:relay@localhost:5433/relay_w5d1"
)

def is_db_down(port: int = 5433) -> bool:
    try:
        s = socket.create_connection(("127.0.0.1", port), timeout=0.5)
        s.close()
        return False
    except OSError:
        return True

def print_exception_details(e: Exception, label: str):
    print(f"\n=======================================================", flush=True)
    print(f"[{label}] Caught Exception: {type(e).__module__}.{type(e).__name__}", flush=True)
    print(f"Message: {e}", flush=True)
    print(f"\nSQLAlchemy Exception MRO:", flush=True)
    for idx, cls in enumerate(type(e).__mro__):
        print(f"  {idx}: {cls.__module__}.{cls.__name__}", flush=True)
    
    orig = getattr(e, "orig", None)
    if orig is not None:
        print(f"\nUnderlying Driver Exception (e.orig): {type(orig).__module__}.{type(orig).__name__}", flush=True)
        print(f"Driver Exception Message: {orig}", flush=True)
        print(f"Driver Exception MRO:", flush=True)
        for idx, cls in enumerate(type(orig).__mro__):
            print(f"  {idx}: {cls.__module__}.{cls.__name__}", flush=True)
    else:
        print("\nNo underlying e.orig found.", flush=True)
    print(f"=======================================================\n", flush=True)

async def probe_stale():
    print("[PROBE-STALE] Starting Case A: Stale connection in pool", flush=True)
    engine = create_async_engine(DATABASE_URL, pool_size=1, max_overflow=0)
    
    # 1. Warm up connection
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT 1"))
        print(f"[PROBE-STALE] Warmup query successful: {res.scalar()}", flush=True)
    print("[PROBE-STALE] Connection returned to pool. Waiting for DB to go DOWN...", flush=True)

    # Wait for DB to stop
    while not is_db_down():
        await asyncio.sleep(0.5)
    print("[PROBE-STALE] Detected DB is DOWN! Attempting query on stale pooled connection...", flush=True)

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            print("[PROBE-STALE] UNEXPECTED: Query succeeded!", flush=True)
    except Exception as e:
        print_exception_details(e, "CASE A: STALE POOLED CONNECTION")
    finally:
        await engine.dispose()

async def probe_fresh():
    print("[PROBE-FRESH] Starting Case B: Fresh process / new connection while DB is DOWN", flush=True)
    if not is_db_down():
        print("[PROBE-FRESH] WARNING: DB is currently UP! Case B requires DB to be DOWN.", flush=True)
    
    engine = create_async_engine(DATABASE_URL, pool_size=1, max_overflow=0)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            print("[PROBE-FRESH] UNEXPECTED: Query succeeded!", flush=True)
    except Exception as e:
        print_exception_details(e, "CASE B: FRESH CONNECTION ATTEMPT (REFUSED)")
    finally:
        await engine.dispose()

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "stale"
    if mode == "stale":
        asyncio.run(probe_stale())
    elif mode == "fresh":
        asyncio.run(probe_fresh())
    else:
        print(f"Unknown mode: {mode}. Use 'stale' or 'fresh'.")

if __name__ == "__main__":
    main()
