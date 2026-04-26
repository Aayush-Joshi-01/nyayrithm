from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class SimulationCreate(BaseModel):
    title: str
    mode: str = "courtroom"  # courtroom | deposition | strategy
    max_turns: int = 50
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
