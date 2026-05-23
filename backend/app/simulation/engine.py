from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, AsyncIterator, Callable
from uuid import UUID

import structlog

from app.agents.graph.agent_graph import AgentGraph
from app.agents.orchestrator import AgentOrchestrator
from app.models.agent import AgentDefinition
from app.models.simulation import Simulation
from app.models.turn import Turn
from app.vector_db.factory import get_vector_store

logger = structlog.get_logger()


class SimulationEngine:
    """
    Top-level engine that:
    1. Builds the AgentGraph from persisted AgentDefinitions
    2. Creates the AgentOrchestrator
    3. Runs turns (one-shot or streamed)
    4. Persists Turn records to DB
    """

    def __init__(self) -> None:
        self.vector_store = get_vector_store()

    async def build_orchestrator(
        self,
        simulation: Simulation,
        agent_definitions: list[AgentDefinition],
        case_metadata: dict[str, Any],
        turn_repo,
        broadcast_fn: Callable | None = None,
    ) -> AgentOrchestrator:
        graph = AgentGraph(
            case_id=UUID(str(simulation.case_id)),
            simulation_id=simulation.id,
        )

        # Separate predefined from spawned (spawned are reconstructed in order)
        predefined = [a for a in agent_definitions if a.is_predefined and a.parent_agent_id is None]
        for defn in predefined:
            graph.add_root_agent(defn)

        # Re-add spawned agents (preserving parent relationships)
        spawned = [a for a in agent_definitions if not a.is_predefined]
        for defn in sorted(spawned, key=lambda a: a.spawned_at):
            from app.agents.base import SpawnRequest
            sr = SpawnRequest(
                role=defn.role,
                name=defn.name,
                persona=defn.persona,
                reason=defn.spawn_reason or "",
                llm_provider=defn.llm_provider,
                llm_model=defn.llm_model,
                initial_instruction=defn.initial_instruction or "",
            )
            graph.spawn_agent(sr, parent_id=str(defn.parent_agent_id), auto=False)

        async def persist_turn(result, agent_id: str, sim_id: str):
            turn = Turn(
                simulation_id=UUID(sim_id),
                agent_id=UUID(agent_id),
                turn_number=simulation.current_turn,
                content=result.response.content,
                citations=result.response.citations,
                spawned_agents=[s.name for s in result.spawns],
                token_count=result.response.token_count,
                latency_ms=result.response.latency_ms,
                reasoning_trace=result.response.reasoning_trace,
            )
            await turn_repo.create(turn)

        return AgentOrchestrator(
            simulation=simulation,
            graph=graph,
            case_metadata=case_metadata,
            vector_store=self.vector_store,
            turn_persist_fn=persist_turn,
            broadcast_fn=broadcast_fn,
        )

    async def run_next_turn(
        self,
        simulation_id: str,
        broadcast_fn: Callable | None = None,
    ) -> dict[str, Any] | None:
        """Entry point for Celery tasks — loads sim from DB and runs one turn."""
        from app.db.session import get_session
        from app.db.factory import get_repository

        async for session in get_session():
            sim_repo = get_repository("simulation", session)
            agent_repo = get_repository("agent", session)
            turn_repo = get_repository("turn", session)
            case_repo = get_repository("case", session)

            simulation = await sim_repo.get(simulation_id)
            if not simulation or simulation.status not in ("running",):
                return None

            case = await case_repo.get(str(simulation.case_id))
            case_metadata = {
                "title": case.title if case else "",
                "country": case.country if case else "",
                "jurisdiction": case.jurisdiction if case else "",
                "legal_system": case.legal_system if case else "",
            }

            agent_defs, _ = await agent_repo.list(
                filters={"simulation_id": str(simulation.id)}, size=100
            )

            orchestrator = await self.build_orchestrator(
                simulation=simulation,
                agent_definitions=agent_defs,
                case_metadata=case_metadata,
                turn_repo=turn_repo,
                broadcast_fn=broadcast_fn,
            )

            result = await orchestrator.run_next_turn()

            # Persist updated turn count
            await sim_repo.update(simulation_id, {
                "current_turn": simulation.current_turn,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })

            if simulation.current_turn >= simulation.max_turns:
                await sim_repo.update(simulation_id, {
                    "status": "completed",
                    "ended_at": datetime.now(timezone.utc).isoformat(),
                })
                if broadcast_fn:
                    await broadcast_fn("simulation.completed", {"simulation_id": simulation_id})

            return result.response.__dict__ if result else None
