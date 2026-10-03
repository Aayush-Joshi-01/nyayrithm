from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.repository_base import BaseRepository

T = TypeVar("T")


def _serialize(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value  # stays a BSON date so it sorts, range-queries and aggregates
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialize(v) for v in value]
    return value


class MongoRepository(BaseRepository[T], Generic[T]):
    """
    Motor (async pymongo) adapter.

    Subclasses must set:
      collection_name: str
      model_cls: type[T]
    """

    collection_name: str
    model_cls: type[T]

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db

    @property
    def col(self):
        return self.db[self.collection_name]

    def _doc_to_model(self, doc: dict) -> T:
        doc.pop("_id", None)
        return self._from_dict(doc)

    async def get(self, id: str) -> T | None:
        doc = await self.col.find_one({"id": id})
        return self._doc_to_model(doc) if doc else None

    async def list(
        self,
        filters: dict[str, Any] | None = None,
        page: int = 1,
        size: int = 20,
        order_by: str | None = None,
    ) -> tuple[list[T], int]:
        query = filters or {}
        total = await self.col.count_documents(query)
        # Same convention as the SQL adapter: "field" ascends, "field DESC" descends, and
        # no order_by means newest first.
        if order_by:
            parts = order_by.split()
            sort_field = parts[0]
            direction = -1 if len(parts) > 1 and parts[1].upper() == "DESC" else 1
        else:
            sort_field, direction = "created_at", -1
        cursor = self.col.find(query).sort(sort_field, direction).skip((page - 1) * size).limit(size)
        docs = await cursor.to_list(length=size)
        return [self._doc_to_model(d) for d in docs], total

    async def create(self, entity: T) -> T:
        doc = {k: _serialize(v) for k, v in asdict(entity).items()}  # type: ignore
        await self.col.insert_one(doc)
        return entity

    async def update(self, id: str, data: dict[str, Any]) -> T:
        serialized = {k: _serialize(v) for k, v in data.items()}
        await self.col.update_one({"id": id}, {"$set": serialized})
        updated = await self.get(id)
        if updated is None:
            raise ValueError(f"Record {id} not found after update")
        return updated

    async def delete(self, id: str) -> bool:
        result = await self.col.delete_one({"id": id})
        return result.deleted_count > 0

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        return await self.col.count_documents(filters or {})

    async def delete_where(self, filters: dict[str, Any]) -> int:
        """Delete every document matching all ``filters``; returns the number removed."""
        if not filters:
            raise ValueError("delete_where requires at least one filter")
        result = await self.col.delete_many(filters)
        return result.deleted_count

    async def query(self, raw_query: Any, **kwargs) -> list[T]:
        cursor = self.col.find(raw_query)
        docs = await cursor.to_list(length=None)
        return [self._doc_to_model(d) for d in docs]
