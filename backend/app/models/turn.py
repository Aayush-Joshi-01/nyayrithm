from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4


@dataclass
class Turn:
    simulation_id: UUID
    agent_id: UUID
    turn_number: int
    content: str
    id: UUID = field(default_factory=uuid4)
    content_edited: str | None = None
    reasoning_trace: dict[str, Any] = field(default_factory=dict)
    citations: list[dict[str, Any]] = field(default_factory=list)
    retrieved_chunks: list[dict[str, Any]] = field(default_factory=list)
    spawned_agents: list[str] = field(default_factory=list)
    is_human_override: bool = False
    token_count: int = 0
    latency_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
