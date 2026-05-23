from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class EvidenceResponse(BaseModel):
    id: UUID
    case_id: UUID
    title: str
    description: str
    evidence_type: str
    modality: str
    file_path: str
    file_size: int
    mime_type: str
    status: str
    chunk_count: int
    tags: list[str]
    linked_participants: list[str]
    metadata: dict[str, Any]
    embedder_used: str | None
    indexed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EvidenceListResponse(BaseModel):
    items: list[EvidenceResponse]
    total: int
    page: int
    size: int


class EvidenceChunkResponse(BaseModel):
    id: str
    text: str
    modality: str
    metadata: dict[str, Any]
    chunk_index: int
