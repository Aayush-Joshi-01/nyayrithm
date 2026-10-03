from __future__ import annotations

from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings


@lru_cache
def _make_engine():
    settings = get_settings()
    # PostgreSQL in every real deployment; the tests point DATABASE_URL at SQLite.
    return create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG, pool_pre_ping=True)


@lru_cache
def _make_session_factory():
    return async_sessionmaker(_make_engine(), expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with _make_session_factory()() as session:
        yield session
