from __future__ import annotations

"""Document-shaped records that live in MongoDB."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class EvidenceContent:
    """What ingestion extracted from an evidence file: text, transcript, segments."""

    evidence_id: UUID
    case_id: UUID
    id: UUID = field(default_factory=uuid4)
    raw_text: str | None = None
    transcription: str | None = None
    segments: list[dict[str, Any]] | None = None
    created_at: datetime = field(default_factory=_now)


@dataclass
class LlmUsage:
    """One model call. Written for every chat, embedding and vision request."""

    kind: str  # chat | embedding | vision
    provider: str
    model: str
    org_id: str | None = None
    user_id: str | None = None
    simulation_id: str | None = None
    agent_role: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    estimated: bool = False  # tokens were estimated, not reported by the provider
    cost_usd: float = 0.0
    latency_ms: int = 0
    ttft_ms: int | None = None  # time to first token (streaming only)
    status: str = "ok"  # ok | error
    error_code: str | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=_now)


@dataclass
class LlmPrice:
    """Admin override of the built-in price table (USD per million tokens)."""

    provider: str
    model: str
    input_per_mtok: float
    output_per_mtok: float
    id: UUID = field(default_factory=uuid4)
    updated_by: str = ""
    created_at: datetime = field(default_factory=_now)
