from __future__ import annotations

from typing import Any
from uuid import UUID

from app.agents.base import BaseAgent, SpawnRequest
from app.agents.graph.edge import AgentEdge
from app.agents.graph.node import AgentNode
from app.agents.memory.combined import CombinedAgentMemory
from app.llm.factory import build_llm_provider
from app.models.agent import AgentDefinition


class AgentGraph:
    """
    Dynamic directed graph of agents.
    Root agents are predefined; spawned agents are added at runtime.
    """

    def __init__(self, case_id: UUID, simulation_id: UUID) -> None:
        self.case_id = case_id
        self.simulation_id = simulation_id
        self.nodes: dict[str, AgentNode] = {}
        self.edges: list[AgentEdge] = []
        self.root_agents: list[str] = []
        self._turn_order: list[str] = []

    def add_root_agent(self, definition: AgentDefinition) -> AgentNode:
        node = self._instantiate(definition)
        self.root_agents.append(str(definition.id))
        self._turn_order.append(str(definition.id))
        return node

    def spawn_agent(
        self,
        spawn_request: SpawnRequest,
        parent_id: str,
        auto: bool = False,
        persist_fn=None,  # async callable to persist AgentDefinition to DB
        agent_id: UUID | None = None,  # preserve identity when reconstructing from DB
    ) -> AgentNode:
        from app.agents.roles import ROLE_AGENT_MAP
        from uuid import uuid4

        agent_id = agent_id or uuid4()

        # Fall back to the role's configured default provider/model, not a
        # hardcoded one, so spawned agents run on the same stack as the roster.
        from app.llm.registry import ROLE_PROVIDER_MAP
        role_provider, role_model = ROLE_PROVIDER_MAP.get(
            spawn_request.role, ("gemini", "gemini-flash-lite-latest")
        )
        provider = spawn_request.llm_provider or role_provider
        model = spawn_request.llm_model or role_model

        definition = AgentDefinition(
            id=agent_id,
            simulation_id=self.simulation_id,
            parent_agent_id=UUID(parent_id),
            spawn_reason=spawn_request.reason,
            is_predefined=False,
            role=spawn_request.role,
            name=spawn_request.name or f"{spawn_request.role.title()} #{len(self.nodes)+1}",
            persona=spawn_request.persona,
            llm_provider=provider,
            llm_model=model,
            system_prompt="",  # will be built dynamically
            initial_instruction=spawn_request.initial_instruction,
        )

        node = self._instantiate(definition)

        # Insert into turn order right after parent
        if parent_id in self._turn_order:
            idx = self._turn_order.index(parent_id)
            self._turn_order.insert(idx + 1, str(agent_id))
        else:
            self._turn_order.append(str(agent_id))

        # Link in parent
        if parent_id in self.nodes:
            self.nodes[parent_id].children.append(str(agent_id))

        self.edges.append(AgentEdge(
            source_id=parent_id,
            target_id=str(agent_id),
            reason=spawn_request.reason,
            auto=auto,
        ))

        return node

    def _instantiate(self, definition: AgentDefinition) -> AgentNode:
        from app.agents.roles import ROLE_AGENT_MAP

        llm = build_llm_provider(
            role=definition.role,
            override_provider=definition.llm_provider or None,
            override_model=definition.llm_model or None,
        )
        memory = CombinedAgentMemory(
            case_id=self.case_id,
            agent_id=definition.id,
        )

        agent_cls = ROLE_AGENT_MAP.get(definition.role, ROLE_AGENT_MAP["custom"])
        agent: BaseAgent = agent_cls(definition=definition, llm=llm, memory=memory)

        node = AgentNode(
            agent_id=str(definition.id),
            role=definition.role,
            name=definition.name,
            agent=agent,
            is_predefined=definition.is_predefined,
        )
        self.nodes[str(definition.id)] = node
        return node

    def get_turn_order(self) -> list[str]:
        return list(self._turn_order)

    def to_json(self) -> dict[str, Any]:
        return {
            "nodes": [
                {
                    "id": nid,
                    "role": n.role,
                    "name": n.name,
                    "is_predefined": n.is_predefined,
                    "parent_id": next(
                        (e.source_id for e in self.edges if e.target_id == nid), None
                    ),
                    "llm_provider": n.agent.llm.provider_name,
                    "llm_model": n.agent.llm.model_name,
                    "status": n.agent.definition.status,
                }
                for nid, n in self.nodes.items()
            ],
            "edges": [
                {"source": e.source_id, "target": e.target_id, "reason": e.reason, "auto": e.auto}
                for e in self.edges
            ],
        }
