from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable
from uuid import UUID

import structlog

from app.agents.graph.agent_graph import AgentGraph
from app.agents.orchestrator import AgentOrchestrator
from app.models.agent import AgentDefinition
from app.models.simulation import Simulation
from app.models.turn import Turn
from app.vector_db.factory import get_vector_store

logger = structlog.get_logger()

_ACTIVE_STATUSES = ("running",)


class SimulationEngine:
    """
    Top-level engine that:
    1. Builds the AgentGraph from persisted AgentDefinitions
    2. Creates the AgentOrchestrator (rehydrating prior turns for continuity)
    3. Runs the turn loop to completion, honouring pause/stop
    4. Persists Turn records and simulation progress to DB
    """

    def __init__(self) -> None:
        self.vector_store = get_vector_store()

    async def build_orchestrator(
        self,
        simulation: Simulation,
        agent_definitions: list[AgentDefinition],
        case_metadata: dict[str, Any],
        turn_repo,
        agent_repo,
        prior_turns: list[Turn] | None = None,
        broadcast_fn: Callable | None = None,
    ) -> AgentOrchestrator:
        graph = AgentGraph(
            case_id=UUID(str(simulation.case_id)),
            simulation_id=simulation.id,
        )

        predefined = [
            a for a in agent_definitions if a.is_predefined and a.parent_agent_id is None
        ]
        for defn in predefined:
            graph.add_root_agent(defn)

        # Re-add previously spawned agents, preserving their identity + parent link.
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
            parent_id = str(defn.parent_agent_id) if defn.parent_agent_id else None
            if parent_id and parent_id in graph.nodes:
                graph.spawn_agent(sr, parent_id=parent_id, auto=False, agent_id=defn.id)

        agent_name_by_id = {str(a.id): (a.name, a.role) for a in agent_definitions}

        # ── Rehydrate conversation history so agents have continuity ──────────
        recent: list[dict[str, Any]] = []
        for t in prior_turns or []:
            name, role = agent_name_by_id.get(str(t.agent_id), ("Unknown", "custom"))
            recent.append({
                "agent_id": str(t.agent_id),
                "agent_name": name,
                "role": role,
                "content": t.content_edited or t.content,
                "citations": t.citations or [],
                "turn_number": t.turn_number,
            })

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

        async def persist_agent(node, parent_id: str, spawn_req):
            defn = node.agent.definition
            row = AgentDefinition(
                id=UUID(node.agent_id),
                simulation_id=simulation.id,
                parent_agent_id=UUID(parent_id) if parent_id else None,
                spawn_reason=spawn_req.reason,
                is_predefined=False,
                role=defn.role,
                name=defn.name,
                llm_provider=defn.llm_provider,
                llm_model=defn.llm_model,
                system_prompt="",
                persona=defn.persona,
                initial_instruction=defn.initial_instruction,
                status="spawned",
            )
            await agent_repo.create(row)

        return AgentOrchestrator(
            simulation=simulation,
            graph=graph,
            case_metadata=case_metadata,
            vector_store=self.vector_store,
            turn_persist_fn=persist_turn,
            broadcast_fn=broadcast_fn,
            agent_persist_fn=persist_agent,
            initial_turns=recent,
        )

    async def run_simulation(
        self,
        simulation_id: str,
        broadcast_fn: Callable | None = None,
    ) -> None:
        """Run the full turn loop until max_turns, pause, or stop."""
        import asyncio

        from app.config import get_settings
        from app.db.session import get_session
        from app.db.factory import get_repository

        turn_delay = get_settings().SIMULATION_TURN_DELAY_SECONDS

        async def _with_session(fn):
            gen = get_session()
            session = await gen.__anext__()
            try:
                return await fn(session)
            finally:
                await gen.aclose()

        # Load static case metadata once.
        async def _load(session):
            sim_repo = get_repository("simulation", session)
            case_repo = get_repository("case", session)
            simulation = await sim_repo.get(simulation_id)
            if not simulation or simulation.status not in _ACTIVE_STATUSES:
                return None
            case = await case_repo.get(str(simulation.case_id))
            return {
                "title": case.title if case else "",
                "country": case.country if case else "",
                "jurisdiction": case.jurisdiction if case else "",
                "legal_system": (case.legal_system if case else "") or "common_law",
                "_max_turns": simulation.max_turns,
            }

        case_metadata = await _with_session(_load)
        if case_metadata is None:
            return
        max_turns = case_metadata.pop("_max_turns")

        # ── Turn loop ────────────────────────────────────────────────────────
        async def _one_turn(session) -> str:
            """Returns 'continue' | 'stop' | 'done'."""
            sim_repo = get_repository("simulation", session)
            agent_repo = get_repository("agent", session)
            turn_repo = get_repository("turn", session)

            simulation = await sim_repo.get(simulation_id)
            if not simulation:
                return "stop"
            if simulation.status != "running":
                if broadcast_fn and simulation.status == "paused":
                    await broadcast_fn("simulation.paused", {
                        "simulation_id": simulation_id,
                        "turn_number": simulation.current_turn,
                    })
                return "stop"
            if simulation.current_turn >= max_turns:
                return "done"

            agent_defs, _ = await agent_repo.list(
                filters={"simulation_id": str(simulation.id)},
                size=200, order_by="spawned_at",
            )
            if not agent_defs:
                await sim_repo.update(simulation_id, {"status": "failed"})
                if broadcast_fn:
                    await broadcast_fn("error", {
                        "message": "Simulation has no agents. Add agents before starting.",
                    })
                    await broadcast_fn("simulation.completed", {
                        "simulation_id": simulation_id, "total_turns": 0,
                    })
                return "stop"

            prior_turns, _ = await turn_repo.list(
                filters={"simulation_id": str(simulation.id)},
                size=500, order_by="turn_number",
            )

            orchestrator = await self.build_orchestrator(
                simulation=simulation,
                agent_definitions=agent_defs,
                case_metadata=case_metadata,
                turn_repo=turn_repo,
                agent_repo=agent_repo,
                prior_turns=prior_turns,
                broadcast_fn=broadcast_fn,
            )

            try:
                result = await orchestrator.run_next_turn()
            except Exception as exc:  # noqa: BLE001
                # A turn failed even after the provider's own retries. Park the
                # simulation as 'paused' so it can be resumed (state is on disk).
                logger.error("turn_errored_pausing", simulation_id=simulation_id, error=str(exc))
                await sim_repo.update(simulation_id, {"status": "paused"})
                if broadcast_fn:
                    await broadcast_fn("error", {
                        "message": f"Turn failed ({exc}). Simulation paused — press Resume to continue.",
                    })
                    await broadcast_fn("simulation.paused", {
                        "simulation_id": simulation_id,
                        "turn_number": simulation.current_turn,
                    })
                return "stop"

            if result is None:
                return "done"

            await sim_repo.update(simulation_id, {
                "current_turn": orchestrator.simulation.current_turn,
                "updated_at": datetime.now(timezone.utc),
            })
            return "continue"

        while True:
            outcome = await _with_session(_one_turn)
            if outcome != "continue":
                break
            if turn_delay > 0:
                await asyncio.sleep(turn_delay)

        if outcome == "stop":
            return

        async def _finish(session) -> int:
            sim_repo = get_repository("simulation", session)
            final = await sim_repo.get(simulation_id)
            total = final.current_turn if final else 0
            await sim_repo.update(simulation_id, {
                "status": "completed",
                "ended_at": datetime.now(timezone.utc),
            })
            return total

        total = await _with_session(_finish)
        if broadcast_fn:
            await broadcast_fn("simulation.completed", {
                "simulation_id": simulation_id, "total_turns": total,
            })
