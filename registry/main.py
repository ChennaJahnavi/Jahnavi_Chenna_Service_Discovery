from __future__ import annotations

import time
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="service-registry", version="1.0.0")


class RegisterRequest(BaseModel):
    service: str = Field(min_length=1, examples=["echo-service"])
    instance_id: str = Field(min_length=1, examples=["echo-1"])
    url: str = Field(min_length=1, examples=["http://service1:5001"])
    ttl_seconds: int = Field(default=15, ge=5, le=300)
    meta: dict[str, Any] = Field(default_factory=dict)


class InstanceRecord(BaseModel):
    service: str
    instance_id: str
    url: str
    ttl_seconds: int
    meta: dict[str, Any] = Field(default_factory=dict)
    last_seen_unix: float


REGISTRY: dict[str, dict[str, InstanceRecord]] = {}


def _now() -> float:
    return time.time()


def _purge_expired(service: str) -> None:
    now = _now()
    service_map = REGISTRY.get(service)
    if not service_map:
        return
    expired = [
        instance_id
        for instance_id, rec in service_map.items()
        if now - rec.last_seen_unix > rec.ttl_seconds
    ]
    for instance_id in expired:
        del service_map[instance_id]
    if not service_map:
        REGISTRY.pop(service, None)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/register")
def register(req: RegisterRequest) -> dict[str, Any]:
    service = req.service.strip()
    instance_id = req.instance_id.strip()
    url = req.url.strip().rstrip("/")

    rec = InstanceRecord(
        service=service,
        instance_id=instance_id,
        url=url,
        ttl_seconds=req.ttl_seconds,
        meta=req.meta,
        last_seen_unix=_now(),
    )

    REGISTRY.setdefault(service, {})[instance_id] = rec
    return {"registered": True, "record": rec.model_dump()}


@app.post("/heartbeat/{service}/{instance_id}")
def heartbeat(service: str, instance_id: str) -> dict[str, Any]:
    service = service.strip()
    instance_id = instance_id.strip()
    service_map = REGISTRY.get(service)
    if not service_map or instance_id not in service_map:
        raise HTTPException(status_code=404, detail="instance not registered")
    rec = service_map[instance_id]
    rec.last_seen_unix = _now()
    service_map[instance_id] = rec
    return {"ok": True, "last_seen_unix": rec.last_seen_unix}


@app.get("/discover/{service}")
def discover(service: str) -> dict[str, Any]:
    service = service.strip()
    _purge_expired(service)
    instances = list(REGISTRY.get(service, {}).values())
    return {"service": service, "count": len(instances), "instances": [i.model_dump() for i in instances]}


@app.delete("/deregister/{service}/{instance_id}")
def deregister(service: str, instance_id: str) -> dict[str, Any]:
    service = service.strip()
    instance_id = instance_id.strip()
    service_map = REGISTRY.get(service)
    if not service_map or instance_id not in service_map:
        return {"deleted": False}
    del service_map[instance_id]
    if not service_map:
        REGISTRY.pop(service, None)
    return {"deleted": True}
