from __future__ import annotations

"""SQLite adapter — thin wrapper over PostgresRepository using aiosqlite + SQLAlchemy Core.
Same interface, different engine URL (sqlite+aiosqlite:///<path>).
"""

from app.db.adapters.postgres import PostgresRepository  # noqa: F401

# SQLite uses the same SQLAlchemy Core adapter; the engine URL difference is
# handled at session creation time (see db/session.py).
# This module exists so that DB_BACKEND=sqlite maps cleanly to a named symbol.
SQLiteRepository = PostgresRepository
