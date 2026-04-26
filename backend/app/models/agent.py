from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4


VALID_ROLES = frozenset([
    "judge", "prosecutor", "defense", "plaintiff",
    "accused", "witness", "investigator", "expert_witness", "custom",
])


@dataclass
class AgentDefinition:
    simulation_id: UUID
    role: str  # one of VALID_ROLES
    name: str
    llm_provider: str
    llm_model: str
    system_prompt: str
    id: UUID = field(default_factory=uuid4)
    parent_agent_id: UUID | None = None
    spawn_reason: str | None = None
    is_predefined: bool = True  # False = AI-spawned
    persona: dict[str, Any] = field(default_factory=dict)
    knowledge_scope: dict[str, Any] = field(default_factory=dict)
    jurisdiction_context: dict[str, Any] = field(default_factory=dict)
    status: str = "active"  # active | suspended | dismissed | spawned
    initial_instruction: str | None = None
    spawned_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
