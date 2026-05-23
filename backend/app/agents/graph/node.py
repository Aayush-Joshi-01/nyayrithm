from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.agents.base import BaseAgent


@dataclass
class AgentNode:
    agent_id: str
    role: str
    name: str
    agent: "BaseAgent"
    is_predefined: bool = True
    children: list[str] = field(default_factory=list)  # child agent IDs
