from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4


@dataclass
class Simulation:
    case_id: UUID
    title: str
    mode: str  # courtroom | deposition | strategy
    created_by: str
    id: UUID = field(default_factory=uuid4)
    status: str = "draft"  # draft | running | paused | completed | failed
    current_turn: int = 0
    max_turns: int = 50
    turn_order: list[str] = field(default_factory=list)  # agent IDs, mutable
    config: dict[str, Any] = field(default_factory=dict)
    started_at: datetime | None = None
    ended_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
