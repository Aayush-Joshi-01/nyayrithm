from __future__ import annotations

"""Health of every component the platform depends on, for the admin portal."""

import asyncio
import time
from typing import Any

import httpx
from sqlalchemy import text

from app.config import get_settings
from app.db import mongo
from app.db.stores import Stores


async def _timed(name: str, fn) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        detail = await asyncio.wait_for(fn(), timeout=4.0)
        return {"name": name, "ok": True, "latency_ms": round((time.perf_counter() - started) * 1000),
                "detail": detail or ""}
    except Exception as exc:  # noqa: BLE001
        return {"name": name, "ok": False,
                "latency_ms": round((time.perf_counter() - started) * 1000),
                "detail": f"{type(exc).__name__}: {exc}"[:200]}


async def _http_ok(url: str) -> str:
    async with httpx.AsyncClient(timeout=3.0) as client:
        resp = await client.get(url)
        if resp.status_code >= 400:
            raise RuntimeError(f"HTTP {resp.status_code}")
    return f"HTTP {resp.status_code}"


async def check_all(stores: Stores) -> list[dict[str, Any]]:
    s = get_settings()

    async def postgres() -> str:
        await stores.pg.execute(text("SELECT 1"))
        return ""

    async def mongo_ping() -> str:
        await mongo.get_mongo_db().command("ping")
        return s.MONGODB_DB

    async def redis_ping() -> str:
        import redis.asyncio as aioredis

        client = aioredis.from_url(s.REDIS_URL)
        try:
            await client.ping()
        finally:
            await client.aclose()
        return ""

    async def qdrant() -> str:
        return await _http_ok(f"{s.QDRANT_URL.rstrip('/')}/readyz")

    async def keycloak() -> str:
        return await _http_ok(
            f"{s.KEYCLOAK_URL.rstrip('/')}/realms/{s.NEXT_PUBLIC_KEYCLOAK_REALM}"
            "/.well-known/openid-configuration")

    async def celery() -> str:
        from app.tasks.celery_app import celery_app

        def ping() -> dict | None:
            return celery_app.control.inspect(timeout=1.5).ping()

        workers = await asyncio.get_running_loop().run_in_executor(None, ping)
        if not workers:
            raise RuntimeError("no worker answered")
        return f"{len(workers)} worker(s)"

    async def legal_packs() -> str:
        from app.legal.corpus import get_corpus

        packs = get_corpus().list()
        return ", ".join(f"{p['id']} ({p['provision_count']} provisions, {p['status']})"
                         for p in packs)

    checks = [("PostgreSQL", postgres), ("MongoDB", mongo_ping), ("Redis", redis_ping),
              ("Qdrant", qdrant), ("Keycloak", keycloak), ("Celery workers", celery),
              ("Legal packs", legal_packs)]
    return await asyncio.gather(*(_timed(n, f) for n, f in checks))
