import asyncio
import sys
from fastapi import FastAPI, Header, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI(title="Fake LLM Provider")

print("fake_provider listening=127.0.0.1:8002 ledger=in_memory", flush=True)

ledger = {"calls": 0}


class CompleteRequest(BaseModel):
    prompt: str = ""


@app.get("/v1/ledger")
async def get_ledger():
    return {"calls": ledger["calls"]}


@app.post("/v1/complete")
async def complete(
    req: CompleteRequest,
    x_fake_mode: str = Header(default="ok"),
):
    ledger["calls"] += 1
    tokens_in = len(req.prompt.split())
    tokens_out = 10

    if x_fake_mode == "429":
        return Response(
            content='{"error": "rate_limited"}',
            status_code=429,
            headers={"retry-after": "2"},
            media_type="application/json",
        )

    if x_fake_mode == "500":
        return Response(
            content='{"error": "internal_server_error"}',
            status_code=500,
            media_type="application/json",
        )

    if x_fake_mode == "400":
        return Response(
            content='{"error": "bad_request"}',
            status_code=400,
            media_type="application/json",
        )

    if x_fake_mode == "401":
        return Response(
            content='{"error": "unauthorized"}',
            status_code=401,
            media_type="application/json",
        )

    if x_fake_mode == "slow_below":
        await asyncio.sleep(3.0)
        return {
            "text": "fake completion",
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
        }

    if x_fake_mode == "slow_above":
        await asyncio.sleep(7.0)
        return {
            "text": "fake completion",
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
        }

    if x_fake_mode == "hang":
        await asyncio.sleep(30.0)
        return {
            "text": "fake completion",
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
        }

    if x_fake_mode == "trickle":
        async def trickle_gen():
            chunks = [
                '{"text":',
                ' "fake ',
                'trickle ',
                'chunked ',
                'response"',
                ', "tokens_in": 4',
                ', "tokens_out": 10',
                '}',
            ]
            for i, chunk in enumerate(chunks):
                if i > 0:
                    await asyncio.sleep(1.2)
                yield chunk.encode("utf-8")

        return StreamingResponse(trickle_gen(), media_type="application/json")

    return {
        "text": "fake completion",
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
    }
