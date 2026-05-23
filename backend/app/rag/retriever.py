from __future__ import annotations

from typing import Any
from uuid import UUID

from app.rag.embedder_factory import get_embedder
from app.vector_db.base import SearchResult, VectorStore


ROLE_KNOWLEDGE_RESTRICTIONS: dict[str, dict[str, Any]] = {
    "witness": {
        # Witnesses can only access evidence they're linked to
        "linked_only": True,
    },
    "accused": {
        "exclude_types": ["confession"],  # can't access their own sealed confession during sim
    },
    "judge": {
        # Judge sees everything admitted to record
    },
    "prosecutor": {},
    "defense": {},
    "plaintiff": {},
    "investigator": {},
    "expert_witness": {},
    "custom": {},
}


class EvidenceRetriever:
    """RAG retrieval per agent per turn, scoped to role knowledge constraints."""

    def __init__(self, vector_store: VectorStore) -> None:
        self.vector_store = vector_store
        self.embedder = get_embedder()

    async def retrieve_for_agent(
        self,
        role: str,
        query: str,
        case_id: UUID,
        top_k: int = 5,
        modality_filter: str | None = None,
        extra_filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        query_embedding = await self.embedder.embed_text(query)
        collection = str(case_id)

        filters: dict[str, Any] = {}
        if modality_filter:
            filters["modality"] = modality_filter
        if extra_filters:
            filters.update(extra_filters)

        restrictions = ROLE_KNOWLEDGE_RESTRICTIONS.get(role, {})
        if restrictions.get("exclude_types"):
            # In a real system, pre-filter by metadata. For now, filter post-retrieval.
            pass

        results = await self.vector_store.search(
            collection=collection,
            query_embedding=query_embedding,
            top_k=top_k,
            filters=filters or None,
        )

        # Post-filter for role restrictions
        if restrictions.get("exclude_types"):
            excluded = set(restrictions["exclude_types"])
            results = [r for r in results if r.chunk.metadata.get("evidence_type") not in excluded]

        return results[:top_k]

    async def search_case(
        self,
        query: str,
        case_id: UUID,
        top_k: int = 5,
        modality: str | None = None,
    ) -> list[SearchResult]:
        """Unrestricted search — for the /search API endpoint."""
        return await self.retrieve_for_agent(
            role="judge",  # judge sees everything
            query=query,
            case_id=case_id,
            top_k=top_k,
            modality_filter=modality,
        )
