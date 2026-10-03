from __future__ import annotations

import dataclasses
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import get_simulation_service
from app.schemas.agent import AgentCreate, AgentResponse
from app.schemas.simulation import (
    AgentGraphEdge,
    AgentGraphNode,
    AgentGraphResponse,
    SimulationCreate,
    SimulationResponse,
)
from app.services.simulations import SimulationService

router = APIRouter()


def _sim(s) -> SimulationResponse:
    return SimulationResponse(**dataclasses.asdict(s))


def _agent(a) -> AgentResponse:
    return AgentResponse(**dataclasses.asdict(a))


@router.post("/cases/{case_id}/simulations/", response_model=SimulationResponse, status_code=201)
async def create_simulation(
    case_id: UUID, body: SimulationCreate, svc: SimulationService = Depends(get_simulation_service)
):
    return _sim(await svc.create(case_id, body))


@router.get("/cases/{case_id}/simulations/", response_model=list[SimulationResponse])
async def list_simulations(
    case_id: UUID, svc: SimulationService = Depends(get_simulation_service)
):
    return [_sim(s) for s in await svc.list_for_case(case_id)]


@router.get("/simulations/{sim_id}", response_model=SimulationResponse)
async def get_simulation(sim_id: UUID, svc: SimulationService = Depends(get_simulation_service)):
    return _sim(await svc.get(sim_id))


@router.post("/simulations/{sim_id}/start", status_code=202)
async def start_simulation(sim_id: UUID, svc: SimulationService = Depends(get_simulation_service)):
    await svc.start(sim_id)
    return {"status": "started", "simulation_id": str(sim_id)}


@router.post("/simulations/{sim_id}/pause", status_code=202)
async def pause_simulation(sim_id: UUID, svc: SimulationService = Depends(get_simulation_service)):
    await svc.pause(sim_id)
    return {"status": "paused"}


@router.post("/simulations/{sim_id}/stop", status_code=202)
async def stop_simulation(sim_id: UUID, svc: SimulationService = Depends(get_simulation_service)):
    await svc.stop(sim_id)
    return {"status": "stopped"}


@router.delete("/simulations/{sim_id}", status_code=204)
async def delete_simulation(
    sim_id: UUID, svc: SimulationService = Depends(get_simulation_service)
):
    await svc.delete(sim_id)


@router.post("/simulations/{sim_id}/clone", response_model=SimulationResponse, status_code=201)
async def clone_simulation(sim_id: UUID, svc: SimulationService = Depends(get_simulation_service)):
    return _sim(await svc.clone(sim_id))


@router.get("/simulations/{sim_id}/agents", response_model=list[AgentResponse])
async def list_agents(sim_id: UUID, svc: SimulationService = Depends(get_simulation_service)):
    return [_agent(a) for a in await svc.list_agents(sim_id)]


@router.post("/simulations/{sim_id}/agents", response_model=AgentResponse, status_code=201)
async def add_agent(
    sim_id: UUID, body: AgentCreate, svc: SimulationService = Depends(get_simulation_service)
):
    return _agent(await svc.add_agent(sim_id, body))


@router.delete("/simulations/{sim_id}/agents/{agent_id}", status_code=204)
async def delete_agent(
    sim_id: UUID, agent_id: UUID, svc: SimulationService = Depends(get_simulation_service)
):
    await svc.delete_agent(sim_id, agent_id)


@router.get("/simulations/{sim_id}/graph", response_model=AgentGraphResponse)
async def get_agent_graph(sim_id: UUID, svc: SimulationService = Depends(get_simulation_service)):
    items = await svc.list_agents(sim_id)
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
        AgentGraphEdge(source=str(a.parent_agent_id), target=str(a.id), reason=a.spawn_reason)
        for a in items
        if a.parent_agent_id
    ]
    return AgentGraphResponse(nodes=nodes, edges=edges)
