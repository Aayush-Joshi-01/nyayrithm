from __future__ import annotations

from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.http.exceptions import UnexpectedResponse

from app.vector_db.base import SearchResult, VectorChunk


class QdrantVectorStore:
    def __init__(self, url: str, api_key: str | None = None) -> None:
        self.client = AsyncQdrantClient(url=url, api_key=api_key)

    async def create_collection(self, name: str, dimension: int) -> None:
        if await self.collection_exists(name):
            return
        try:
            await self.client.create_collection(
                collection_name=name,
                vectors_config=qmodels.VectorParams(
                    size=dimension,
                    distance=qmodels.Distance.COSINE,
                ),
            )
        except UnexpectedResponse as exc:
            # Several workers ingesting a new case's first files all reach this point at once;
            # the losers of the race get 409 "already exists", which is exactly what we want.
            if exc.status_code != 409 and not await self.collection_exists(name):
                raise

    async def collection_exists(self, name: str) -> bool:
        try:
            await self.client.get_collection(name)
            return True
        except Exception:
            return False

    async def drop_collection(self, name: str) -> None:
        await self.client.delete_collection(name)

    async def upsert(self, collection: str, chunks: list[VectorChunk]) -> None:
        points = [
            qmodels.PointStruct(
                id=chunk.id,
                vector=chunk.embedding,
                payload={
                    "text": chunk.text,
                    "modality": chunk.modality,
                    **chunk.metadata,
                },
            )
            for chunk in chunks
        ]
        await self.client.upsert(collection_name=collection, points=points)

    async def search(
        self,
        collection: str,
        query_embedding: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        qdrant_filter = None
        if filters:
            conditions = [
                qmodels.FieldCondition(key=k, match=qmodels.MatchValue(value=v))
                for k, v in filters.items()
            ]
            qdrant_filter = qmodels.Filter(must=conditions)

        if not await self.collection_exists(collection):
            # No evidence has been ingested for this case yet — nothing to retrieve.
            return []

        response = await self.client.query_points(
            collection_name=collection,
            query=query_embedding,
            limit=top_k,
            query_filter=qdrant_filter,
            with_payload=True,
        )

        return [
            SearchResult(
                chunk=VectorChunk(
                    id=str(r.id),
                    text=r.payload.get("text", ""),
                    embedding=[],  # not returned from search
                    metadata={k: v for k, v in r.payload.items() if k not in ("text", "modality")},
                    modality=r.payload.get("modality", "text"),
                ),
                score=r.score,
            )
            for r in response.points
        ]

    async def delete(self, collection: str, ids: list[str]) -> None:
        await self.client.delete(
            collection_name=collection,
            points_selector=qmodels.PointIdsList(points=ids),
        )
