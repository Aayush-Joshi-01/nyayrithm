from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from typing import Literal

from pydantic import BaseModel, Field

from app.legal.disclaimer import DISCLAIMER


class SimulationCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    mode: Literal["courtroom", "deposition", "strategy"] = "courtroom"
    max_turns: int = Field(50, ge=1, le=500)
    config: dict[str, Any] = {}


class SimulationResponse(BaseModel):
    id: UUID
    case_id: UUID
    title: str
    mode: str
    status: str
    current_turn: int
    max_turns: int
    turn_order: list[str]
    config: dict[str, Any]
    started_at: datetime | None
    ended_at: datetime | None
    created_at: datetime
    disclaimer: str = DISCLAIMER

    model_config = {"from_attributes": True}


class AgentGraphNode(BaseModel):
    id: str
    role: str
    name: str
    status: str
    is_predefined: bool
    llm_provider: str
    llm_model: str
    parent_id: str | None


class AgentGraphEdge(BaseModel):
    source: str
    target: str
    reason: str | None


class AgentGraphResponse(BaseModel):
    nodes: list[AgentGraphNode]
    edges: list[AgentGraphEdge]
