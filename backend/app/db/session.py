from __future__ import annotations

from functools import lru_cache
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings


@lru_cache
def _make_engine():
    settings = get_settings()
    if settings.DB_BACKEND == "sqlite":
        url = f"sqlite+aiosqlite:///{settings.SQLITE_PATH}"
    else:
        url = settings.DATABASE_URL
    return create_async_engine(url, echo=settings.DEBUG, pool_pre_ping=True)


@lru_cache
def _make_session_factory():
    return async_sessionmaker(_make_engine(), expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with _make_session_factory()() as session:
        yield session


async def get_mongo_db():
    """Yields a Motor database for MongoDB backends."""
    from motor.motor_asyncio import AsyncIOMotorClient

    settings = get_settings()
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    yield client[settings.MONGODB_DB]
    client.close()
