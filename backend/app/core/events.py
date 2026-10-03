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

    # Default plans everywhere; the dev firm and accounts only when explicitly enabled.
    from app.config import get_settings
    from app.db.stores import open_stores
    from app.seed import ensure_default_plans, seed_dev_data

    try:
        async with open_stores() as stores:
            await ensure_default_plans(stores)
            if get_settings().SEED_DEV_DATA:
                await seed_dev_data(stores)
    except Exception as exc:  # noqa: BLE001
        logger.warning("startup_seed_failed", error=str(exc))



async def on_shutdown() -> None:
    logger.info("nyayrithm_shutting_down")
