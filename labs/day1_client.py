# Day 1: Benchmark Runner Script

# Day 1: Concurrent client to measure blocking vs non-blocking

import asyncio
import time
import httpx

BASE_URL = "http://127.0.0.1:8000"
CONCURRENCY = 3


async def measure(path: str) -> float:
    url = f"{BASE_URL}{path}"

    # default timeout 5s hai; blocking case 6s lega, isliye bada rakha
    async with httpx.AsyncClient(timeout=30.0) as client:
        start = time.perf_counter()
        responses = await asyncio.gather(
            *[client.get(url) for _ in range(CONCURRENCY)]
        )
        elapsed = time.perf_counter() - start

    print(f"{path:15} {CONCURRENCY} requests -> {elapsed:.2f}s "
          f"(status codes: {[r.status_code for r in responses]})")
    return elapsed


async def main():
    await measure("/blocking")
    await measure("/nonblocking")


if __name__ == "__main__":
    asyncio.run(main())
