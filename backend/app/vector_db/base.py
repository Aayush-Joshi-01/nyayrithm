from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class VectorChunk:
    id: str
    text: str
    embedding: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)
    modality: str = "text"  # text | image | audio | video


@dataclass
class SearchResult:
    chunk: VectorChunk
    score: float


@runtime_checkable
class VectorStore(Protocol):
    """Abstract vector store. Implementations: qdrant, chroma, pinecone, weaviate, pgvector."""

    async def upsert(self, collection: str, chunks: list[VectorChunk]) -> None: ...

    async def search(
        self,
        collection: str,
        query_embedding: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]: ...

    async def delete(self, collection: str, ids: list[str]) -> None: ...

    async def create_collection(self, name: str, dimension: int) -> None: ...

    async def drop_collection(self, name: str) -> None: ...

    async def collection_exists(self, name: str) -> bool: ...
