from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository_base import BaseRepository

T = TypeVar("T")


def _serialize(value: Any) -> Any:
    """Make values safe for asyncpg binding."""
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (dict, list)):
        return json.dumps(value, default=str)
    return value


class PostgresRepository(BaseRepository[T], Generic[T]):
    """
    Thin SQLAlchemy Core adapter.

    Subclasses must set:
      table_name: str
      model_cls: type[T]
    """

    table_name: str
    model_cls: type[T]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _row_to_model(self, row: Any) -> T:
        data = dict(row._mapping)
        # JSON columns come back as strings in some drivers
        for k, v in data.items():
            if isinstance(v, str):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, (dict, list)):
                        data[k] = parsed
                except (json.JSONDecodeError, TypeError):
                    pass
        return self._from_dict(data)

    async def get(self, id: str) -> T | None:
        result = await self.session.execute(
            text(f"SELECT * FROM {self.table_name} WHERE id = :id"),
            {"id": id},
        )
        row = result.fetchone()
        return self._row_to_model(row) if row else None

    async def list(
        self,
        filters: dict[str, Any] | None = None,
        page: int = 1,
        size: int = 20,
        order_by: str | None = None,
    ) -> tuple[list[T], int]:
        where, params = self._build_where(filters or {})
        order = f"ORDER BY {order_by}" if order_by else "ORDER BY created_at DESC"
        offset = (page - 1) * size

        count_result = await self.session.execute(
            text(f"SELECT COUNT(*) FROM {self.table_name}{where}"), params
        )
        total: int = count_result.scalar() or 0

        result = await self.session.execute(
            text(f"SELECT * FROM {self.table_name}{where} {order} LIMIT :limit OFFSET :offset"),
            {**params, "limit": size, "offset": offset},
        )
        rows = result.fetchall()
        return [self._row_to_model(r) for r in rows], total

    async def create(self, entity: T) -> T:
        data = {k: _serialize(v) for k, v in asdict(entity).items()}  # type: ignore
        cols = ", ".join(data.keys())
        vals = ", ".join(f":{k}" for k in data.keys())
        await self.session.execute(
            text(f"INSERT INTO {self.table_name} ({cols}) VALUES ({vals})"), data
        )
        await self.session.commit()
        return entity

    async def update(self, id: str, data: dict[str, Any]) -> T:
        serialized = {k: _serialize(v) for k, v in data.items()}
        sets = ", ".join(f"{k} = :{k}" for k in serialized.keys())
        await self.session.execute(
            text(f"UPDATE {self.table_name} SET {sets} WHERE id = :id"),
            {**serialized, "id": id},
        )
        await self.session.commit()
        updated = await self.get(id)
        if updated is None:
            raise ValueError(f"Record {id} not found after update")
        return updated

    async def delete(self, id: str) -> bool:
        result = await self.session.execute(
            text(f"DELETE FROM {self.table_name} WHERE id = :id"), {"id": id}
        )
        await self.session.commit()
        return result.rowcount > 0

    async def query(self, raw_query: Any, **kwargs) -> list[T]:
        result = await self.session.execute(text(str(raw_query)), kwargs)
        return [self._row_to_model(r) for r in result.fetchall()]

    def _build_where(self, filters: dict[str, Any]) -> tuple[str, dict]:
        if not filters:
            return "", {}
        clauses = [f"{k} = :{k}" for k in filters.keys()]
        return " WHERE " + " AND ".join(clauses), dict(filters)
