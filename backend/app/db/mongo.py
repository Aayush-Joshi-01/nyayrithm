from __future__ import annotations

"""MongoDB access: turns, extracted evidence text and LLM usage events."""

from functools import lru_cache
from typing import Any

import structlog

from app.config import get_settings

logger = structlog.get_logger()


@lru_cache
def _client():
    from motor.motor_asyncio import AsyncIOMotorClient

    # tz_aware so datetimes round-trip as UTC rather than naive values.
    return AsyncIOMotorClient(get_settings().MONGODB_URI, tz_aware=True)


def get_mongo_db() -> Any:
    return _client()[get_settings().MONGODB_DB]


async def ensure_indexes(db: Any | None = None) -> None:
    """Create the indexes the app relies on. Idempotent; safe to call on every start."""
    db = db if db is not None else get_mongo_db()
    await db["turns"].create_index([("simulation_id", 1), ("turn_number", 1)])
    await db["turns"].create_index("id", unique=True)
    await db["evidence_content"].create_index("evidence_id")
    await db["llm_usage"].create_index([("org_id", 1), ("created_at", -1)])
    await db["llm_usage"].create_index([("provider", 1), ("model", 1), ("created_at", -1)])
    await db["llm_usage"].create_index("simulation_id")
    await db["llm_usage"].create_index("created_at")
    await db["llm_prices"].create_index([("provider", 1), ("model", 1)], unique=True)


async def ping() -> bool:
    try:
        await get_mongo_db().command("ping")
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("mongo_ping_failed", error=str(exc))
        return False
