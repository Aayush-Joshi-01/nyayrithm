from __future__ import annotations

import structlog

logger = structlog.get_logger()


async def on_startup() -> None:
    logger.info("nyayrithm_starting")
    # Connection pools and vector store clients are created lazily. MongoDB indexes are
    # ensured here; a Mongo outage at boot must not stop the API from starting.
    from app.db.mongo import ensure_indexes

    try:
        await ensure_indexes()
    except Exception as exc:  # noqa: BLE001
        logger.warning("mongo_indexes_failed", error=str(exc))



async def on_shutdown() -> None:
    logger.info("nyayrithm_shutting_down")
