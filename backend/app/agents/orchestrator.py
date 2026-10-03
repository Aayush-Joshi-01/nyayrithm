from __future__ import annotations

import asyncio
from typing import AsyncIterator, Callable, Any
from uuid import UUID

import structlog

from app.agents.base import TurnContext, TurnResult
from app.agents.graph.agent_graph import AgentGraph
from app.legal.audit import sha256_text
from app.legal.procedure import ProcedureEngine
from app.legal.review import LegalReviewer, correction_note_from
from app.models.simulation import Simulation

logger = structlog.get_logger()


class AgentOrchestrator:
    """
    Central controller managing:
    - Agent lifecycle and turn-taking
    - Spawn request processing
    - Conflict detection and resolution
    - Conversation state
    """

    def __init__(
        self,
        simulation: Simulation,
        graph: AgentGraph,
        case_metadata: dict[str, Any],
        vector_store=None,
        turn_persist_fn: Callable | None = None,   # async fn(turn_result, agent_id, sim_id)
        broadcast_fn: Callable | None = None,       # async fn(event_type, payload)
        agent_persist_fn: Callable | None = None,   # async fn(node, parent_id, spawn_request)
        initial_turns: list[dict[str, Any]] | None = None,
        procedure: ProcedureEngine | None = None,   # who speaks when, and the current stage
        reviewer: LegalReviewer | None = None,       # citation verification + applicable-law context
        audit_fn: Callable | None = None,            # async fn(event_type, actor, payload)
    ) -> None:
        self.simulation = simulation
        self.graph = graph
        self.case_metadata = case_metadata
        self.vector_store = vector_store
        self.turn_persist_fn = turn_persist_fn
        self.broadcast_fn = broadcast_fn
        self.agent_persist_fn = agent_persist_fn
        self.procedure = procedure
        self.reviewer = reviewer
        self.audit_fn = audit_fn
        self._recent_turns: list[dict[str, Any]] = list(initial_turns or [])
        # Resume turn-taking rotation where the prior run left off.
        self._current_turn_index = len(self._recent_turns)

    def _next_agent_id(self) -> str | None:
        order = self.graph.get_turn_order()
        if not order:
            return None
        if self.procedure is not None:
            picked = self._procedural_speaker(order)
            if picked:
                return picked
        idx = self._current_turn_index % len(order)
        return order[idx]

    def _procedural_speaker(self, order: list[str]) -> str | None:
        """The procedure engine names a role; pick that role's least-recently-used agent."""
        assert self.procedure is not None
        last = self._recent_turns[-1] if self._recent_turns else None
        role = self.procedure.next_speaker_role(
            self.simulation.current_turn, last, self._available_roles()
        )
        if role is None:
            return None
        candidates = [a for a in order if a in self.graph.nodes and self.graph.nodes[a].role == role]
        if not candidates:
            return None
        spoken = {a: sum(1 for t in self._recent_turns if t.get("agent_id") == a) for a in candidates}
        return min(candidates, key=lambda a: (spoken[a], candidates.index(a)))

    def _available_roles(self) -> set[str]:
        return {n.role for n in self.graph.nodes.values()}

    async def _audit(self, event_type: str, actor: str, payload: dict[str, Any]) -> None:
        """An audit failure must never abort a turn that has already happened."""
        if not self.audit_fn:
            return
        try:
            await self.audit_fn(event_type, actor, payload)
        except Exception as exc:  # noqa: BLE001
            logger.error("audit_append_failed", event_type=event_type, error=str(exc))

    def _is_complete(self) -> bool:
        return (
            self.simulation.status in ("completed", "failed", "paused")
            or self.simulation.current_turn >= self.simulation.max_turns
        )

    def _turn_extras(self, agent_id: str) -> dict[str, Any]:
        """Applicable law, the procedural directive and any registry correction for a turn."""
        extra: dict[str, Any] = {}
        meta = self.case_metadata
        role = self.graph.nodes[agent_id].role
        last = self._recent_turns[-1] if self._recent_turns else None

        if self.reviewer is not None:
            query = " ".join([
                meta.get("title", ""), meta.get("description", ""),
                *(t.get("content", "")[:300] for t in self._recent_turns[-3:]),
            ])
            context, refs = self.reviewer.context_for(
                query, meta.get("country"), meta.get("jurisdiction")
            )
            if context:
                extra["legal_context"] = context
                extra["legal_context_refs"] = refs
            mine = next(
                (t for t in reversed(self._recent_turns) if t.get("agent_id") == agent_id), None
            )
            note = correction_note_from(mine.get("legal_review")) if mine else ""
            if note:
                extra["corrections"] = note

        if self.procedure is not None:
            extra["procedure_directive"] = self.procedure.directive(
                self.simulation.current_turn, role, last, self._available_roles()
            )
        return extra

    def _review(self, result: TurnResult, role: str) -> tuple[dict | None, dict | None]:
        """Verify the turn's legal citations and check it against courtroom procedure."""
        review_dict = None
        if self.reviewer is not None:
            meta = self.case_metadata
            review_dict = self.reviewer.review(
                result.response.content, meta.get("country"), meta.get("jurisdiction")
            ).to_dict()
        procedure_dict = None
        if self.procedure is not None:
            last = self._recent_turns[-1] if self._recent_turns else None
            procedure_dict = self.procedure.review_turn(
                self.simulation.current_turn, role, result.response.content, last
            ).to_dict()
        return review_dict, procedure_dict

    async def _build_context(self, agent_id: str) -> TurnContext:
        return TurnContext(
            simulation_id=self.simulation.id,
            case_id=UUID(str(self.simulation.case_id)),
            turn_number=self.simulation.current_turn,
            mode=self.simulation.mode,
            recent_turns=list(self._recent_turns[-15:]),
            case_metadata=self.case_metadata,
            active_agent_ids=self.graph.get_turn_order(),
            extra=self._turn_extras(agent_id),
        )

    async def _process_spawns(self, agent_id: str, result: TurnResult) -> list[str]:
        new_ids = []
        for spawn_req in result.spawns:
            logger.info("agent_spawn", parent=agent_id, role=spawn_req.role, reason=spawn_req.reason)
            node = self.graph.spawn_agent(spawn_request=spawn_req, parent_id=agent_id)
            new_ids.append(node.agent_id)

            if self.agent_persist_fn:
                await self.agent_persist_fn(node, agent_id, spawn_req)

            if self.broadcast_fn:
                await self.broadcast_fn("agent.spawned", {
                    "agent_id": node.agent_id,
                    "role": node.role,
                    "name": node.name,
                    "parent_id": agent_id,
                    "reason": spawn_req.reason,
                })
        return new_ids

    async def _maybe_auto_spawn(self) -> None:
        """
        Proactive orchestrator spawn: if forensic/expert evidence is referenced
        but no expert_witness agent exists, auto-spawn one.
        """
        has_expert = any(n.role == "expert_witness" for n in self.graph.nodes.values())
        if not has_expert and len(self._recent_turns) >= 2:
            recent_text = " ".join(t.get("content", "") for t in self._recent_turns[-3:]).lower()
            if any(k in recent_text for k in ("forensic", "ballistic", "dna", "toxicology", "digital evidence")):
                from app.agents.base import SpawnRequest
                spawn_req = SpawnRequest(
                    role="expert_witness",
                    name="Court-Appointed Forensic Expert",
                    persona={"specialty": "forensics", "neutral": True},
                    reason="Orchestrator auto-spawned: forensic topic detected without expert present",
                    initial_instruction="You are a neutral court-appointed forensic expert. Provide unbiased technical analysis.",
                )
                parent_id = (
                    self.graph.root_agents[0]
                    if self.graph.root_agents
                    else list(self.graph.nodes.keys())[0]
                )
                node = self.graph.spawn_agent(
                    spawn_request=spawn_req, parent_id=parent_id, auto=True
                )
                if self.agent_persist_fn:
                    await self.agent_persist_fn(node, parent_id, spawn_req)
                if self.broadcast_fn:
                    await self.broadcast_fn("agent.spawned", {
                        "agent_id": node.agent_id,
                        "role": node.role,
                        "name": node.name,
                        "parent_id": parent_id,
                        "reason": spawn_req.reason,
                    })
                logger.info("orchestrator_auto_spawned_expert")

    async def _check_contradiction(self, result: TurnResult, agent_id: str) -> None:
        """
        Simple contradiction detector: flag if two agents make contradictory
        factual claims about the same evidence chunk.
        """
        if len(self._recent_turns) < 2:
            return

        content = result.response.content.lower()
        # Check last 5 turns for factual contradiction signals
        for prev in self._recent_turns[-5:]:
            prev_content = prev.get("content", "").lower()
            # If both reference the same evidence but with opposite signals
            common_refs = set(c["evidence_id"] for c in result.response.citations) & \
                          set(c["evidence_id"] for c in prev.get("citations", []))
            if common_refs and prev.get("agent_id") != agent_id:
                negation_words = {"not", "never", "false", "incorrect", "disagree", "contradict"}
                if negation_words & set(content.split()):
                    if self.broadcast_fn:
                        await self.broadcast_fn("conflict.detected", {
                            "agent_id": agent_id,
                            "conflicting_agent_id": prev.get("agent_id"),
                            "evidence_ids": list(common_refs),
                            "turn_number": self.simulation.current_turn,
                        })

    async def run_next_turn(self) -> TurnResult | None:
        """Execute exactly one turn. Returns None if simulation is complete."""
        if self._is_complete():
            return None

        agent_id = self._next_agent_id()
        if not agent_id or agent_id not in self.graph.nodes:
            return None

        node = self.graph.nodes[agent_id]
        context = await self._build_context(agent_id)

        if self.broadcast_fn:
            await self.broadcast_fn("turn.started", {
                "turn_number": self.simulation.current_turn,
                "agent_id": agent_id,
                "agent_name": node.name,
                "role": node.role,
            })

        # Stream callback wires tokens to WebSocket
        async def stream_cb(token: str):
            if self.broadcast_fn:
                await self.broadcast_fn("turn.token", {"agent_id": agent_id, "token": token})

        try:
            result = await node.agent.run_turn(
                context=context,
                vector_store=self.vector_store,
                stream_callback=stream_cb,
            )
        except Exception as exc:
            logger.error("turn_failed", agent_id=agent_id, error=str(exc))
            if self.broadcast_fn:
                await self.broadcast_fn("error", {
                    "message": f"{node.name} ({node.role}) failed to respond: {exc}",
                    "turn_number": self.simulation.current_turn,
                })
            raise

        review_dict, procedure_dict = self._review(result, node.role)
        if review_dict:
            result.response.metadata["legal_review"] = review_dict
        if procedure_dict:
            result.response.metadata["procedure"] = procedure_dict

        # Persist turn
        if self.turn_persist_fn:
            await self.turn_persist_fn(result, agent_id, str(self.simulation.id))

        await self._audit("turn.generated", f"agent:{agent_id}", {
            "turn_number": self.simulation.current_turn,
            "role": node.role,
            "agent_name": node.name,
            "provider": result.response.provider,
            "model": result.response.model,
            "prompt_sha256": result.response.prompt_sha256,
            "content_sha256": sha256_text(result.response.content),
            "retrieved": result.response.retrieved,
            "stage": (procedure_dict or {}).get("stage"),
            "legal_status": (review_dict or {}).get("status"),
            "violations": [v["code"] for v in (procedure_dict or {}).get("violations", [])],
        })
        flagged = [
            c for c in (review_dict or {}).get("citations", [])
            if c["severity"] in ("warning", "error")
        ]
        if flagged:
            await self._audit("citation.flagged", f"agent:{agent_id}", {
                "turn_number": self.simulation.current_turn,
                "citations": [{"raw": c["raw"], "status": c["status"]} for c in flagged],
            })
            if self.broadcast_fn:
                await self.broadcast_fn("citation.flagged", {
                    "agent_id": agent_id,
                    "turn_number": self.simulation.current_turn,
                    "citations": flagged,
                })

        # Update recent turns
        self._recent_turns.append({
            "agent_id": agent_id,
            "agent_name": node.name,
            "role": node.role,
            "content": result.response.content,
            "citations": result.response.citations,
            "turn_number": self.simulation.current_turn,
            "legal_review": review_dict,
            "procedure": procedure_dict,
        })

        if self.broadcast_fn:
            await self.broadcast_fn("turn.completed", {
                "turn_number": self.simulation.current_turn,
                "agent_id": agent_id,
                "agent_name": node.name,
                "role": node.role,
                "content": result.response.content,
                "citations": result.response.citations,
                "spawned_agents": [s.name for s in result.spawns],
                "legal_review": review_dict,
                "procedure": procedure_dict,
            })

        # Process spawns
        await self._process_spawns(agent_id, result)

        # Auto-spawn check
        await self._maybe_auto_spawn()

        # Contradiction check
        await self._check_contradiction(result, agent_id)

        self.simulation.current_turn += 1
        self._current_turn_index += 1

        return result

    async def run_all(self) -> AsyncIterator[TurnResult]:
        """Run the full simulation to completion, yielding each turn result."""
        while not self._is_complete():
            result = await self.run_next_turn()
            if result is None:
                break
            yield result
            await asyncio.sleep(0)  # yield control between turns
