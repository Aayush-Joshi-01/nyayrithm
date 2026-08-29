from __future__ import annotations

import json
from typing import Any, AsyncIterator

import structlog

from app.config import get_settings

logger = structlog.get_logger()

_CHANNEL_PREFIX = "sim:events:"


def _channel(simulation_id: str) -> str:
    return f"{_CHANNEL_PREFIX}{simulation_id}"


def _redis_client():
    """A fresh async Redis client bound to the current event loop.

    Callers create one per publish / per subscription so a client is never
    shared across the uvicorn and Celery-worker processes (or across the
    per-turn ``asyncio.run()`` loops in the worker).
    """
    import redis.asyncio as aioredis

    settings = get_settings()
    return aioredis.from_url(settings.REDIS_URL, decode_responses=True)


async def publish(simulation_id: str, event_type: str, payload: dict[str, Any]) -> None:
    """Publish a simulation event. Safe to call from any process."""
    message = json.dumps({"event": event_type, "data": payload})
    client = _redis_client()
    try:
        await client.publish(_channel(simulation_id), message)
    except Exception as exc:  # never let a broadcast failure abort a turn
        logger.warning("event_bus_publish_failed", error=str(exc), event=event_type)
    finally:
        await client.aclose()


async def subscribe(simulation_id: str) -> AsyncIterator[dict[str, Any]]:
    """Yield decoded event frames for a simulation until the caller stops iterating."""
    client = _redis_client()
    pubsub = client.pubsub()
    await pubsub.subscribe(_channel(simulation_id))
    try:
        async for raw in pubsub.listen():
            if raw is None or raw.get("type") != "message":
                continue
            try:
                yield json.loads(raw["data"])
            except (json.JSONDecodeError, TypeError):
                continue
    finally:
        try:
            await pubsub.unsubscribe(_channel(simulation_id))
            await pubsub.aclose()
        finally:
            await client.aclose()


def make_broadcast_fn(simulation_id: str):
    """Return an ``async fn(event_type, payload)`` bound to this simulation."""

    async def _broadcast(event_type: str, payload: dict) -> None:
        await publish(simulation_id, event_type, payload)

    return _broadcast
