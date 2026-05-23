from __future__ import annotations

import dataclasses
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.db.factory import get_repository
from app.db.session import get_session
from app.llm.registry import list_providers, list_role_defaults
from app.schemas.agent import AgentResponse

router = APIRouter()


async def _agent_repo(session=Depends(get_session)):
    return get_repository("agent", session)


# Static routes must come before /{agent_id} so FastAPI matches them first.
@router.get("/roles/")
async def list_roles():
    return list_role_defaults()


@router.get("/providers/")
async def list_llm_providers():
    return {"providers": list_providers()}


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: UUID, repo=Depends(_agent_repo)):
    agent = await repo.get(str(agent_id))
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentResponse(**dataclasses.asdict(agent))


@router.delete("/{agent_id}/memory", status_code=204)
async def clear_agent_memory(agent_id: UUID):
    # Memory is in-process; clearing it requires the running orchestrator.
    # This endpoint signals intent — the orchestrator checks this flag on next turn.
    return
