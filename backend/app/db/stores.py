from __future__ import annotations

"""The two data stores a request or task works with, opened together.

PostgreSQL holds relational, transactional state; MongoDB holds documents and events.
``get_repository(model, stores)`` picks the right one per model.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import mongo
from app.db.session import _make_session_factory


@dataclass
class Stores:
    pg: AsyncSession
    mongo: Any  # AsyncIOMotorDatabase (or a test double with the same surface)


@asynccontextmanager
async def open_stores() -> AsyncGenerator[Stores, None]:
    """Open both stores for a unit of work outside FastAPI (tasks, the engine)."""
    async with _make_session_factory()() as session:
        yield Stores(pg=session, mongo=mongo.get_mongo_db())


async def get_stores() -> AsyncGenerator[Stores, None]:
    """FastAPI dependency."""
    async with open_stores() as stores:
        yield stores
