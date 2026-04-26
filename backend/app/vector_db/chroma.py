from __future__ import annotations

from typing import Any

import chromadb

from app.vector_db.base import SearchResult, VectorChunk


class ChromaVectorStore:
    def __init__(self, host: str = "localhost", port: int = 8001) -> None:
        self._client = chromadb.AsyncHttpClient(host=host, port=port)

    async def create_collection(self, name: str, dimension: int) -> None:
        await self._client.get_or_create_collection(name=name)

    async def collection_exists(self, name: str) -> bool:
        try:
            await self._client.get_collection(name)
            return True
        except Exception:
            return False

    async def drop_collection(self, name: str) -> None:
        await self._client.delete_collection(name)

    async def upsert(self, collection: str, chunks: list[VectorChunk]) -> None:
        col = await self._client.get_or_create_collection(collection)
        await col.upsert(
            ids=[c.id for c in chunks],
            embeddings=[c.embedding for c in chunks],
            documents=[c.text for c in chunks],
            metadatas=[{**c.metadata, "modality": c.modality} for c in chunks],
        )

    async def search(
        self,
        collection: str,
        query_embedding: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        col = await self._client.get_collection(collection)
        where = filters or None
        results = await col.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        output = []
        for i, doc_id in enumerate(results["ids"][0]):
            doc = results["documents"][0][i]
            meta = results["metadatas"][0][i]
            dist = results["distances"][0][i]
            output.append(
                SearchResult(
                    chunk=VectorChunk(
                        id=doc_id,
                        text=doc,
                        embedding=[],
                        metadata={k: v for k, v in meta.items() if k != "modality"},
                        modality=meta.get("modality", "text"),
                    ),
                    score=1.0 - dist,  # chroma uses L2 distance
                )
            )
        return output

    async def delete(self, collection: str, ids: list[str]) -> None:
        col = await self._client.get_collection(collection)
        await col.delete(ids=ids)
