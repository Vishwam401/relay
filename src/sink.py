import json
import os
import sys
from contextlib import asynccontextmanager
from typing import Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from src.database import async_session


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure sink_deliveries table exists on startup
    async with async_session() as session:
        await session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS sink_deliveries (
                    id bigserial PRIMARY KEY,
                    idempotency_key text NOT NULL,
                    job_id bigint NOT NULL DEFAULT 0,
                    received_at timestamptz NOT NULL DEFAULT now(),
                    body jsonb NOT NULL DEFAULT '{}'::jsonb
                );
                """
            )
        )
        await session.commit()
    yield


app = FastAPI(title="External Sink Service", lifespan=lifespan)


class DeliverRequest(BaseModel):
    idempotency_key: str
    job_id: int = 0
    body: dict[str, Any] = Field(default_factory=dict)


@app.get("/health")
async def health_check():
    return {"ok": True, "service": "sink"}


@app.post("/deliver")
async def deliver(req: DeliverRequest):
    if not req.idempotency_key or req.idempotency_key.strip() == "":
        raise HTTPException(status_code=400, detail="idempotency_key is required and cannot be empty")

    dedup_enabled = os.environ.get("SINK_DEDUP", "1").lower() in ("1", "true", "yes")

    async with async_session() as session:
        if dedup_enabled:
            # Check if this idempotency_key has already been delivered
            check_stmt = text(
                "SELECT id FROM sink_deliveries WHERE idempotency_key = :k LIMIT 1"
            )
            res = await session.execute(check_stmt, {"k": req.idempotency_key})
            if res.first() is not None:
                print(f"[deliver] idempotency_key={req.idempotency_key} result=duplicate")
                sys.stdout.flush()
                return {
                    "result": "duplicate",
                    "idempotency_key": req.idempotency_key,
                }

        # Insert delivery
        insert_stmt = text(
            """
            INSERT INTO sink_deliveries (idempotency_key, job_id, body)
            VALUES (:k, :job_id, CAST(:body AS jsonb))
            """
        )
        await session.execute(
            insert_stmt,
            {
                "k": req.idempotency_key,
                "job_id": req.job_id,
                "body": json.dumps(req.body),
            },
        )
        await session.commit()

        print(f"[deliver] idempotency_key={req.idempotency_key} result=applied")
        sys.stdout.flush()
        return {
            "result": "applied",
            "idempotency_key": req.idempotency_key,
        }
