from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4


@dataclass
class Case:
    title: str
    description: str
    country: str
    jurisdiction: str
    legal_system: str  # common_law | civil_law | sharia | hybrid
    created_by: str
    id: UUID = field(default_factory=uuid4)
    status: str = "open"  # open | in_simulation | closed | archived
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
