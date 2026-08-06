# Day 1: Process, Thread, and Async Experiment

from fastapi import FastAPI
import time
import asyncio

app = FastAPI()

@app.get("/blocking")
async def blocking_endpoint():
    time.sleep(2)
    return {"status" : "done"}


@app.get("/nonblocking")
async def nonblocking_endpoint():
    await asyncio.sleep(2)
    return {"status" : "done"}