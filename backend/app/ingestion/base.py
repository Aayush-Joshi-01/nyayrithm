from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class IngestionResult:
    raw_text: str
    transcription: str | None = None
    segments: list[dict] | None = None  # time-stamped segments for audio/video
    metadata: dict[str, Any] = field(default_factory=dict)
    modality: str = "text"


@runtime_checkable
class EvidenceIngester(Protocol):
    """Abstract ingester for a specific evidence type."""

    supported_mime_types: list[str]

    async def ingest(self, file_path: str) -> IngestionResult: ...
