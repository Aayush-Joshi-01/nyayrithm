from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AgentEdge:
    source_id: str   # parent agent ID
    target_id: str   # spawned agent ID
    reason: str      # why the spawn happened
    auto: bool = False  # True = orchestrator-initiated
