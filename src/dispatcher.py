import asyncio
import os
import signal
import sys
from typing import Any
import httpx
from sqlalchemy import func, select
from src.database import async_session
from src.models import Outbox

POLL_INTERVAL_SECONDS = 2.0
SINK_URL = os.environ.get("SINK_URL", "http://127.0.0.1:8001/deliver")
DISPATCHER_ID = f"dispatcher-{os.getpid()}"
SHUTDOWN_REQUESTED = False


def request_shutdown(signum: int, frame: Any) -> None:
    global SHUTDOWN_REQUESTED
    sig_name = signal.Signals(signum).name
    print(
        f"\n[{DISPATCHER_ID}] Signal {sig_name} received. Finishing current dispatch before shutdown..."
    )
    sys.stdout.flush()
    SHUTDOWN_REQUESTED = True


async def run_dispatcher() -> None:
    print(f"[{DISPATCHER_ID}] Starting dispatcher process (PID: {os.getpid()})...")
    sys.stdout.flush()

    signal.signal(signal.SIGINT, request_shutdown)
    signal.signal(signal.SIGTERM, request_shutdown)

    async with httpx.AsyncClient(timeout=5.0) as client:
        while not SHUTDOWN_REQUESTED:
            dispatched = False

            async with async_session() as session:
                async with session.begin():
                    query = (
                        select(Outbox)
                        .where(Outbox.dispatched_at.is_(None))
                        .order_by(Outbox.created_at, Outbox.id)
                        .limit(1)
                        .with_for_update(skip_locked=True)
                    )
                    result = await session.execute(query)
                    outbox_row = result.scalars().first()

                    if outbox_row:
                        dispatched = True
                        key = outbox_row.effect_key or f"job:{outbox_row.job_id}"
                        payload_data = {
                            "idempotency_key": key,
                            "job_id": outbox_row.job_id,
                            "body": outbox_row.payload or {},
                        }

                        print(
                            f"[{DISPATCHER_ID}] Attempting dispatch: job_id={outbox_row.job_id} outbox_id={outbox_row.id} key={key}..."
                        )
                        sys.stdout.flush()

                        try:
                            response = await client.post(SINK_URL, json=payload_data)
                            if response.status_code == 200:
                                # Check crash hook
                                crash_env = os.environ.get("CRASH_AT")
                                if crash_env == "none":
                                    crash_at_flag = None
                                else:
                                    crash_at_flag = crash_env or (outbox_row.payload or {}).get("crash_at")
                                if crash_at_flag == "after_http":
                                    print(
                                        f"[{DISPATCHER_ID}] [crash_at] Triggering after_http crash for job_id={outbox_row.job_id} outbox_id={outbox_row.id}."
                                    )
                                    sys.stdout.flush()
                                    os._exit(1)

                                outbox_row.dispatched_at = func.now()
                                outbox_row.attempts = outbox_row.attempts + 1
                                print(
                                    f"[{DISPATCHER_ID}] [dispatch] job_id={outbox_row.job_id} outbox_id={outbox_row.id} status=dispatched attempts={outbox_row.attempts}"
                                )
                                sys.stdout.flush()
                            else:
                                outbox_row.attempts = outbox_row.attempts + 1
                                print(
                                    f"[{DISPATCHER_ID}] [dispatch_failed] job_id={outbox_row.job_id} outbox_id={outbox_row.id} status_code={response.status_code} attempts={outbox_row.attempts}"
                                )
                                sys.stdout.flush()
                        except Exception as exc:
                            outbox_row.attempts = outbox_row.attempts + 1
                            print(
                                f"[{DISPATCHER_ID}] [dispatch_error] job_id={outbox_row.job_id} outbox_id={outbox_row.id} error={exc} attempts={outbox_row.attempts}"
                            )
                            sys.stdout.flush()

            if not dispatched:
                await asyncio.sleep(POLL_INTERVAL_SECONDS)

    print(f"[{DISPATCHER_ID}] Clean shutdown complete.")
    sys.stdout.flush()


if __name__ == "__main__":
    asyncio.run(run_dispatcher())
