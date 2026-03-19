from __future__ import annotations

import asyncio
import os
import socket
import time

import httpx
from fastapi import FastAPI

SERVICE_NAME = os.getenv("SERVICE_NAME", "echo-service").strip()
INSTANCE_ID = os.getenv("INSTANCE_ID", f"{SERVICE_NAME}-{socket.gethostname()}").strip()
REGISTRY_URL = os.getenv("REGISTRY_URL", "http://registry:8000").strip().rstrip("/")
SERVICE_URL = os.getenv("SERVICE_URL", "").strip().rstrip("/")
TTL_SECONDS = int(os.getenv("TTL_SECONDS", "15"))


app = FastAPI(title=SERVICE_NAME, version="1.0.0")


async def _register(client: httpx.AsyncClient) -> None:
    if not SERVICE_URL:
        raise RuntimeError("SERVICE_URL env var is required (e.g. http://service1:5001)")
    await client.post(
        f"{REGISTRY_URL}/register",
        json={
            "service": SERVICE_NAME,
            "instance_id": INSTANCE_ID,
            "url": SERVICE_URL,
            "ttl_seconds": TTL_SECONDS,
            "meta": {"hostname": socket.gethostname()},
        },
        timeout=5,
    )


async def _heartbeat_loop(stop: asyncio.Event) -> None:
    async with httpx.AsyncClient() as client:
        backoff = 1.0
        while not stop.is_set():
            try:
                await _register(client)
                backoff = 1.0
            except Exception:
                backoff = min(backoff * 2, 10.0)

            try:
                await asyncio.wait_for(stop.wait(), timeout=max(1.0, TTL_SECONDS / 3))
            except asyncio.TimeoutError:
                pass

            try:
                await client.post(
                    f"{REGISTRY_URL}/heartbeat/{SERVICE_NAME}/{INSTANCE_ID}",
                    timeout=5,
                )
                backoff = 1.0
            except Exception:
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 10.0)


@app.on_event("startup")
async def on_startup() -> None:
    app.state.stop_event = asyncio.Event()
    app.state.hb_task = asyncio.create_task(_heartbeat_loop(app.state.stop_event))


@app.on_event("shutdown")
async def on_shutdown() -> None:
    stop_event: asyncio.Event = app.state.stop_event
    stop_event.set()
    task: asyncio.Task = app.state.hb_task
    task.cancel()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": SERVICE_NAME, "instance_id": INSTANCE_ID}


@app.get("/hello")
def hello() -> dict[str, str]:
    return {
        "message": "hello",
        "service": SERVICE_NAME,
        "instance_id": INSTANCE_ID,
        "service_url": SERVICE_URL,
        "unix": str(time.time()),
    }
