from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class CitationSchema(BaseModel):
    evidence_id: str
    chunk_index: int
    chunk_text: str
    score: float
    evidence_title: str | None = None
    modality: str = "text"


class TurnResponse(BaseModel):
    id: UUID
    simulation_id: UUID
    agent_id: UUID
    turn_number: int
    content: str
    content_edited: str | None
    citations: list[CitationSchema]
    spawned_agents: list[str]
    is_human_override: bool
    token_count: int
    latency_ms: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TurnEditRequest(BaseModel):
    content: str


class TurnListResponse(BaseModel):
    items: list[TurnResponse]
    total: int
    page: int
    size: int


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    modality: str | None = None
    evidence_type: str | None = None


class SearchResultSchema(BaseModel):
    chunk_id: str
    evidence_id: str
    evidence_title: str
    text: str
    modality: str
    score: float
    metadata: dict[str, Any]
