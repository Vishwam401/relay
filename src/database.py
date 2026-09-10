from collections.abc import AsyncGenerator
from dotenv import load_dotenv

load_dotenv()

import os
import sys
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DATABASE_URL = os.environ["DATABASE_URL"]

# Application name resolution for pg_stat_activity attribution
process_name = os.environ.get("RELAY_PROCESS_NAME")
if not process_name:
    cmd = " ".join(sys.argv)
    if "sink" in cmd:
        process_name = "sink"
    elif "worker" in cmd:
        process_name = "worker"
    elif "reaper" in cmd:
        process_name = "reaper"
    elif "dispatcher" in cmd:
        process_name = "dispatcher"
    elif "uvicorn" in cmd:
        process_name = "api"
    else:
        process_name = "relay"

connect_args = {
    "server_settings": {
        "application_name": process_name
    }
}

pool_size = int(os.environ.get("RELAY_POOL_SIZE", "5"))
max_overflow = int(os.environ.get("RELAY_MAX_OVERFLOW", "10"))
pool_timeout = float(os.environ.get("RELAY_POOL_TIMEOUT", "30.0"))

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_size=pool_size,
    max_overflow=max_overflow,
    pool_timeout=pool_timeout,
    connect_args=connect_args,
)
print(f"resolved_db={engine.url.database} app_name={process_name} pool={pool_size}+{max_overflow}", flush=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()