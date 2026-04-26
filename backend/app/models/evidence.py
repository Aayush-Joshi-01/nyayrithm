from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4


@dataclass
class Evidence:
    case_id: UUID
    title: str
    evidence_type: str  # pdf|docx|audio|video|text|image|witness_statement|confession|deposition
    file_path: str
    mime_type: str
    modality: str  # text | audio | video | image | multimodal
    uploaded_by: str
    id: UUID = field(default_factory=uuid4)
    description: str = ""
    file_size: int = 0
    raw_text: str | None = None
    transcription: str | None = None
    embedder_used: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending | processing | indexed | error
    linked_participants: list[str] = field(default_factory=list)
    vector_collection: str | None = None
    chunk_count: int = 0
    tags: list[str] = field(default_factory=list)
    error_message: str | None = None
    indexed_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
