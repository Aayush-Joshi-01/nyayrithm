from __future__ import annotations

import hashlib
from typing import Any
from uuid import UUID

from app.rag.chunker import RecursiveTextChunker, TimeWindowChunker
from app.rag.embedder_factory import get_embedder_for_modality
from app.vector_db.base import VectorChunk, VectorStore


class EvidenceIndexer:
    """Chunks evidence text/transcriptions, embeds, and upserts into the vector store."""

    def __init__(self, vector_store: VectorStore) -> None:
        self.vector_store = vector_store
        self.text_chunker = RecursiveTextChunker(max_tokens=512, overlap=50)
        self.time_chunker = TimeWindowChunker(window_seconds=30, overlap_seconds=5)

    async def index_evidence(
        self,
        case_id: UUID,
        evidence_id: UUID,
        modality: str,
        mime_type: str,
        text: str | None,
        segments: list[dict] | None = None,  # for audio/video
        extra_metadata: dict | None = None,
    ) -> int:
        """Returns the number of chunks indexed."""
        collection = str(case_id)
        embedder = get_embedder_for_modality(modality, mime_type)

        base_meta: dict[str, Any] = {
            "evidence_id": str(evidence_id),
            "case_id": str(case_id),
            "modality": modality,
            **(extra_metadata or {}),
        }

        # Ensure collection exists
        await self.vector_store.create_collection(collection, embedder.dimension)

        if modality in ("audio", "video") and segments:
            raw_chunks = self.time_chunker.chunk(segments, base_metadata=base_meta)
        elif text:
            raw_chunks = self.text_chunker.chunk(text, base_metadata=base_meta)
        else:
            return 0

        vector_chunks = []
        for chunk in raw_chunks:
            embedding = await embedder.embed_text(chunk.text)
            chunk_id = _make_chunk_id(evidence_id, chunk.index)
            vector_chunks.append(VectorChunk(
                id=chunk_id,
                text=chunk.text,
                embedding=embedding,
                metadata=chunk.metadata,
                modality=modality,
            ))

        if vector_chunks:
            await self.vector_store.upsert(collection, vector_chunks)

        return len(vector_chunks)

    async def delete_evidence(self, case_id: UUID, evidence_id: UUID, chunk_count: int) -> None:
        collection = str(case_id)
        ids = [_make_chunk_id(evidence_id, i) for i in range(chunk_count)]
        await self.vector_store.delete(collection, ids)


def _make_chunk_id(evidence_id: UUID, chunk_index: int) -> str:
    raw = f"{evidence_id}:{chunk_index}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]
