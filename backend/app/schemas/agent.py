from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.agent import VALID_ROLES


class AgentCreate(BaseModel):
    role: str
    name: str = Field(..., min_length=1, max_length=120)
    llm_provider: str | None = None
    llm_model: str | None = None
    persona: dict[str, Any] = {}
    knowledge_scope: dict[str, Any] = {}
    initial_instruction: str | None = None

    @field_validator("role")
    @classmethod
    def _known_role(cls, v: str) -> str:
        if v not in VALID_ROLES:
            raise ValueError(f"role must be one of {sorted(VALID_ROLES)}")
        return v


class AgentResponse(BaseModel):
    id: UUID
    simulation_id: UUID
    parent_agent_id: UUID | None
    spawn_reason: str | None
    is_predefined: bool
    role: str
    name: str
    llm_provider: str
    llm_model: str
    persona: dict[str, Any]
    knowledge_scope: dict[str, Any]
    status: str
    spawned_at: datetime

    model_config = {"from_attributes": True}


class SpawnRequestSchema(BaseModel):
    role: str
    name: str = ""
    persona: dict[str, Any] = {}
    reason: str
    llm_provider: str | None = None
    llm_model: str | None = None
    initial_instruction: str = ""
