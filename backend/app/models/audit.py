from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4


@dataclass
class AuditEvent:
    """One link in a simulation's tamper-evident log (see app/legal/audit.py)."""

    simulation_id: UUID
    seq: int
    event_type: str
    actor: str
    payload: dict[str, Any]
    prev_hash: str
    hash: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
