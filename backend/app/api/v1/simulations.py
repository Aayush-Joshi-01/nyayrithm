from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.db.factory import get_repository
from app.db.session import get_session
from app.models.simulation import Simulation
from app.models.agent import AgentDefinition
from app.schemas.agent import AgentCreate, AgentResponse
from app.schemas.simulation import (
    AgentGraphResponse, AgentGraphNode, AgentGraphEdge,
    SimulationCreate, SimulationResponse,
)

router = APIRouter()
MOCK_USER_ID = "user-001"


async def _sim_repo(session=Depends(get_session)):
    return get_repository("simulation", session)


async def _agent_repo(session=Depends(get_session)):
    return get_repository("agent", session)


def _defaults_for_role(role: str) -> tuple[str, str]:
    from app.llm.registry import ROLE_PROVIDER_MAP, _lazy_register
    _lazy_register()
    return ROLE_PROVIDER_MAP.get(role, ("gemini", "gemini-flash-lite-latest"))


@router.post("/cases/{case_id}/simulations/", response_model=SimulationResponse, status_code=201)
async def create_simulation(
    case_id: UUID,
    body: SimulationCreate,
    repo=Depends(_sim_repo),
    agent_repo=Depends(_agent_repo),
):
    sim = Simulation(
        case_id=case_id,  # type: ignore
        title=body.title,
        mode=body.mode,
        max_turns=body.max_turns,
        config=body.config,
        created_by=MOCK_USER_ID,
    )
    created = await repo.create(sim)

    # Seed a sensible default roster unless the caller opted out. Agents stay
    # editable via the /agents endpoints while the simulation is in draft.
    if body.config.get("seed_default_agents", True):
        from app.simulation.rosters import roster_for
        for entry in roster_for(body.mode):
            provider, model = _defaults_for_role(entry["role"])
            await agent_repo.create(AgentDefinition(
                simulation_id=created.id,
                role=entry["role"],
                name=entry["name"],
                llm_provider=provider,
                llm_model=model,
                system_prompt="",
                is_predefined=True,
                initial_instruction=entry.get("initial_instruction"),
            ))

    return SimulationResponse(**dataclasses.asdict(created))


@router.get("/cases/{case_id}/simulations/", response_model=list[SimulationResponse])
async def list_simulations(case_id: UUID, repo=Depends(_sim_repo)):
    items, _ = await repo.list(filters={"case_id": str(case_id)}, size=100)
    return [SimulationResponse(**dataclasses.asdict(s)) for s in items]


@router.get("/simulations/{sim_id}", response_model=SimulationResponse)
async def get_simulation(sim_id: UUID, repo=Depends(_sim_repo)):
    sim = await repo.get(str(sim_id))
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return SimulationResponse(**dataclasses.asdict(sim))


@router.post("/simulations/{sim_id}/start", status_code=202)
async def start_simulation(sim_id: UUID, repo=Depends(_sim_repo)):
    sim = await repo.get(str(sim_id))
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    if sim.status not in ("draft", "paused", "failed"):
        raise HTTPException(status_code=400, detail=f"Cannot start simulation in status '{sim.status}'")
    await repo.update(str(sim_id), {
        "status": "running",
        "started_at": datetime.now(timezone.utc),
    })
    from app.tasks.simulation_tasks import run_simulation
    run_simulation.delay(str(sim_id))
    return {"status": "started", "simulation_id": str(sim_id)}


@router.post("/simulations/{sim_id}/pause", status_code=202)
async def pause_simulation(sim_id: UUID, repo=Depends(_sim_repo)):
    await repo.update(str(sim_id), {"status": "paused"})
    return {"status": "paused"}


@router.post("/simulations/{sim_id}/stop", status_code=202)
async def stop_simulation(sim_id: UUID, repo=Depends(_sim_repo)):
    await repo.update(str(sim_id), {
        "status": "completed",
        "ended_at": datetime.now(timezone.utc),
    })
    return {"status": "stopped"}


@router.delete("/simulations/{sim_id}", status_code=204)
async def delete_simulation(
    sim_id: UUID,
    repo=Depends(_sim_repo),
    session=Depends(get_session),
):
    from sqlalchemy import text

    sim = await repo.get(str(sim_id))
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    # Mark completed first so any running worker loop exits at its next check.
    await repo.update(str(sim_id), {"status": "completed"})

    # Bulk deletes in FK order — one statement each handles the self-referential
    # parent_agent_id link on agent_definitions without ordering games.
    sid = str(sim_id)
    await session.execute(text("DELETE FROM turns WHERE simulation_id = :sid"), {"sid": sid})
    await session.execute(
        text("DELETE FROM agent_definitions WHERE simulation_id = :sid"), {"sid": sid}
    )
    await session.execute(text("DELETE FROM simulations WHERE id = :sid"), {"sid": sid})
    await session.commit()
    return None


@router.post("/simulations/{sim_id}/clone", response_model=SimulationResponse, status_code=201)
async def clone_simulation(
    sim_id: UUID,
    repo=Depends(_sim_repo),
    agent_repo=Depends(_agent_repo),
):
    src = await repo.get(str(sim_id))
    if not src:
        raise HTTPException(status_code=404, detail="Simulation not found")

    dst = Simulation(
        case_id=src.case_id,
        title=f"{src.title} (copy)",
        mode=src.mode,
        max_turns=src.max_turns,
        config={**src.config, "seed_default_agents": False},
        created_by=MOCK_USER_ID,
    )
    created = await repo.create(dst)

    # Copy the predefined roster (not spawned agents or turns).
    src_agents, _ = await agent_repo.list(
        filters={"simulation_id": str(sim_id)}, size=200, order_by="spawned_at",
    )
    for a in src_agents:
        if not a.is_predefined:
            continue
        # Refresh to the current role default so a clone picks up model changes.
        provider, model = _defaults_for_role(a.role)
        await agent_repo.create(AgentDefinition(
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

    return SimulationResponse(**dataclasses.asdict(created))


@router.get("/simulations/{sim_id}/agents", response_model=list[AgentResponse])
async def list_agents(sim_id: UUID, repo=Depends(_agent_repo)):
    items, _ = await repo.list(filters={"simulation_id": str(sim_id)}, size=100, order_by="spawned_at")
    return [AgentResponse(**dataclasses.asdict(a)) for a in items]


@router.post("/simulations/{sim_id}/agents", response_model=AgentResponse, status_code=201)
async def add_agent(sim_id: UUID, body: AgentCreate, repo=Depends(_agent_repo)):
    from app.llm.registry import ROLE_PROVIDER_MAP, _lazy_register
    _lazy_register()
    default_provider, default_model = ROLE_PROVIDER_MAP.get(body.role, ("gemini", "gemini-flash-lite-latest"))

    defn = AgentDefinition(
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
    )
    created = await repo.create(defn)
    return AgentResponse(**dataclasses.asdict(created))


@router.delete("/simulations/{sim_id}/agents/{agent_id}", status_code=204)
async def delete_agent(sim_id: UUID, agent_id: UUID, repo=Depends(_agent_repo)):
    agent = await repo.get(str(agent_id))
    if not agent or str(agent.simulation_id) != str(sim_id):
        raise HTTPException(status_code=404, detail="Agent not found")
    await repo.delete(str(agent_id))
    return None


@router.get("/simulations/{sim_id}/graph", response_model=AgentGraphResponse)
async def get_agent_graph(sim_id: UUID, repo=Depends(_agent_repo)):
    items, _ = await repo.list(filters={"simulation_id": str(sim_id)}, size=100, order_by="spawned_at")
    nodes = [
        AgentGraphNode(
            id=str(a.id),
            role=a.role,
            name=a.name,
            status=a.status,
            is_predefined=a.is_predefined,
            llm_provider=a.llm_provider,
            llm_model=a.llm_model,
            parent_id=str(a.parent_agent_id) if a.parent_agent_id else None,
        )
        for a in items
    ]
    edges = [
        AgentGraphEdge(
            source=str(a.parent_agent_id),
            target=str(a.id),
            reason=a.spawn_reason,
        )
        for a in items if a.parent_agent_id
    ]
    return AgentGraphResponse(nodes=nodes, edges=edges)
