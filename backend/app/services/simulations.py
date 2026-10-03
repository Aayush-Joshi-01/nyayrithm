from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.core.auth import AuthenticatedUser
from app.core.exceptions import ConflictError, NotFoundError
from app.db.factory import get_repository
from app.db.stores import Stores
from app.legal.audit import AuditLog
from app.models.agent import AgentDefinition
from app.models.simulation import Simulation
from app.schemas.agent import AgentCreate
from app.schemas.simulation import SimulationCreate
from app.services.access import AccessService

_STARTABLE = ("draft", "paused", "failed")


def role_defaults(role: str) -> tuple[str, str]:
    from app.llm.registry import ROLE_PROVIDER_MAP, _lazy_register

    _lazy_register()
    return ROLE_PROVIDER_MAP.get(role, ("gemini", "gemini-flash-lite-latest"))


class SimulationService:
    def __init__(self, stores: Stores, user: AuthenticatedUser) -> None:
        self.stores = stores
        self.user = user
        self.sims = get_repository("simulation", stores)
        self.agents = get_repository("agent", stores)
        self.access = AccessService(stores, user)
        self.audit = AuditLog(stores)

    async def _record(
        self, sim_id: UUID, event: str, payload: dict[str, Any] | None = None
    ) -> None:
        await self.audit.append(sim_id, event, f"user:{self.user.id}", payload or {})

    # ── simulations ───────────────────────────────────────────────────────────
    async def create(self, case_id: UUID, body: SimulationCreate) -> Simulation:
        await self.access.case(case_id)
        sim = await self.sims.create(Simulation(
            case_id=case_id,  # type: ignore[arg-type]
            title=body.title,
            mode=body.mode,
            max_turns=body.max_turns,
            config=body.config,
            created_by=self.user.id,
        ))
        await self._record(sim.id, "simulation.created", {
            "mode": body.mode, "max_turns": body.max_turns, "title": body.title,
        })

        # Seed a sensible default roster unless the caller opted out. Agents stay
        # editable via the agent endpoints while the simulation is in draft.
        if body.config.get("seed_default_agents", True):
            from app.simulation.rosters import roster_for

            for entry in roster_for(body.mode):
                provider, model = role_defaults(entry["role"])
                await self.agents.create(AgentDefinition(
                    simulation_id=sim.id,
                    role=entry["role"],
                    name=entry["name"],
                    llm_provider=provider,
                    llm_model=model,
                    system_prompt="",
                    is_predefined=True,
                    initial_instruction=entry.get("initial_instruction"),
                ))
        return sim

    async def list_for_case(self, case_id: UUID) -> list[Simulation]:
        await self.access.case(case_id)
        items, _ = await self.sims.list(filters={"case_id": str(case_id)}, size=100)
        return items

    async def get(self, sim_id: UUID) -> Simulation:
        return await self.access.simulation(sim_id)

    async def start(self, sim_id: UUID) -> None:
        sim = await self.access.simulation(sim_id)
        if sim.status not in _STARTABLE:
            raise ConflictError(f"Cannot start simulation in status '{sim.status}'")
        await self.sims.update(str(sim_id), {
            "status": "running",
            "started_at": datetime.now(timezone.utc),
        })
        await self._record(sim_id, "simulation.started", {
            "from_status": sim.status,
            "enforce_procedure": sim.config.get("enforce_procedure", True),
        })
        from app.tasks.simulation_tasks import run_simulation

        run_simulation.delay(str(sim_id))

    async def pause(self, sim_id: UUID) -> None:
        sim = await self.access.simulation(sim_id)
        if sim.status != "running":
            raise ConflictError(f"Cannot pause simulation in status '{sim.status}'")
        await self.sims.update(str(sim_id), {"status": "paused"})
        await self._record(sim_id, "simulation.paused", {"at_turn": sim.current_turn})

    async def stop(self, sim_id: UUID) -> None:
        await self.access.simulation(sim_id)
        await self.sims.update(str(sim_id), {
            "status": "completed",
            "ended_at": datetime.now(timezone.utc),
        })
        await self._record(sim_id, "simulation.stopped", {})

    async def delete(self, sim_id: UUID) -> None:
        await self.access.simulation(sim_id)
        # Mark completed first so any running worker loop exits at its next check.
        await self.sims.update(str(sim_id), {"status": "completed"})

        # Children first, in FK order. One bulk delete per table also copes with the
        # self-referential parent_agent_id link on agent_definitions.
        by_sim = {"simulation_id": str(sim_id)}
        for model in ("audit", "turn", "agent"):
            await get_repository(model, self.stores).delete_where(by_sim)
        await self.sims.delete(str(sim_id))

    async def clone(self, sim_id: UUID) -> Simulation:
        src = await self.access.simulation(sim_id)
        created = await self.sims.create(Simulation(
            case_id=src.case_id,
            title=f"{src.title} (copy)",
            mode=src.mode,
            max_turns=src.max_turns,
            config={**src.config, "seed_default_agents": False},
            created_by=self.user.id,
        ))

        # Copy the predefined roster (not spawned agents or turns).
        src_agents, _ = await self.agents.list(
            filters={"simulation_id": str(sim_id)}, size=200, order_by="spawned_at",
        )
        for a in src_agents:
            if not a.is_predefined:
                continue
            # Refresh to the current role default so a clone picks up model changes.
            provider, model = role_defaults(a.role)
            await self.agents.create(AgentDefinition(
                simulation_id=created.id,
                role=a.role,
                name=a.name,
                llm_provider=provider,
                llm_model=model,
                system_prompt="",
                persona=a.persona,
                knowledge_scope=a.knowledge_scope,
                is_predefined=True,
                initial_instruction=a.initial_instruction,
            ))
        return created

    # ── agents ────────────────────────────────────────────────────────────────
    async def list_agents(self, sim_id: UUID) -> list[AgentDefinition]:
        await self.access.simulation(sim_id)
        items, _ = await self.agents.list(
            filters={"simulation_id": str(sim_id)}, size=100, order_by="spawned_at"
        )
        return items

    async def add_agent(self, sim_id: UUID, body: AgentCreate) -> AgentDefinition:
        sim = await self.access.simulation(sim_id)
        if sim.status == "running":
            raise ConflictError("Pause the simulation before changing its agents")
        default_provider, default_model = role_defaults(body.role)
        return await self.agents.create(AgentDefinition(
            simulation_id=sim_id,
            role=body.role,
            name=body.name,
            llm_provider=body.llm_provider or default_provider,
            llm_model=body.llm_model or default_model,
            system_prompt="",
            persona=body.persona,
            knowledge_scope=body.knowledge_scope,
            is_predefined=True,
            initial_instruction=body.initial_instruction,
        ))

    async def delete_agent(self, sim_id: UUID, agent_id: UUID) -> None:
        sim = await self.access.simulation(sim_id)
        agent = await self.agents.get(str(agent_id))
        if agent is None or str(agent.simulation_id) != str(sim_id):
            raise NotFoundError("Agent", str(agent_id))
        if sim.status == "running":
            raise ConflictError("Pause the simulation before changing its agents")
        await self.agents.delete(str(agent_id))
