import asyncio
import os
import sys

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from src.database import async_session
from src.models import Job

async def main():
    async with async_session() as session:
        async with session.begin():
            job = Job(type="effect", payload={"seconds": 5.0})
            session.add(job)
    print("SEEDED_EFFECT_JOB_SUCCESS", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
