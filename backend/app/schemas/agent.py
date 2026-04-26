from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class AgentCreate(BaseModel):
    role: str
    name: str
    llm_provider: str | None = None
    llm_model: str | None = None
    persona: dict[str, Any] = {}
    knowledge_scope: dict[str, Any] = {}
    initial_instruction: str | None = None


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
