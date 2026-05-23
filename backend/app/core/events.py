from __future__ import annotations

import structlog

logger = structlog.get_logger()


async def on_startup() -> None:
    logger.info("nyayrithm_starting")
    # DB connection pools, vector store clients, etc. are initialized lazily
    # via dependency injection — no eager init needed here.


async def on_shutdown() -> None:
    logger.info("nyayrithm_shutting_down")
