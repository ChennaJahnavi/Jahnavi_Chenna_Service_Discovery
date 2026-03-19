from __future__ import annotations

import os
import random
import time
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query

REGISTRY_URL = os.getenv("REGISTRY_URL", "http://registry:8000").strip().rstrip("/")

app = FastAPI(title="client", version="1.0.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


async def _discover(service: str) -> list[dict[str, Any]]:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{REGISTRY_URL}/discover/{service}", timeout=5)
        r.raise_for_status()
        data = r.json()
        return data.get("instances", [])


async def _call(url: str, path: str) -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{url}{path}", timeout=5)
        r.raise_for_status()
        return r.json()


@app.get("/call")
async def call(
    service: str = Query(default="echo-service", min_length=1),
    path: str = Query(default="/hello", min_length=1),
) -> dict[str, Any]:
    instances = await _discover(service)
    if not instances:
        raise HTTPException(status_code=503, detail=f"no instances for service '{service}'")

    chosen = random.choice(instances)
    target_url = chosen["url"].rstrip("/")
    started = time.time()
    payload = await _call(target_url, path)
    return {
        "service": service,
        "chosen_instance_id": chosen["instance_id"],
        "chosen_url": target_url,
        "response": payload,
        "elapsed_ms": int((time.time() - started) * 1000),
        "known_instances": [i["instance_id"] for i in instances],
    }
