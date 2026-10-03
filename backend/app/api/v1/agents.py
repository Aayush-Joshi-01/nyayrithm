from __future__ import annotations

import dataclasses
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import get_access
from app.llm.registry import list_providers, list_role_defaults
from app.schemas.agent import AgentResponse
from app.services.access import AccessService

router = APIRouter()


# Static routes must come before /{agent_id} so FastAPI matches them first.
@router.get("/roles/")
async def list_roles():
    return list_role_defaults()


@router.get("/providers/")
async def list_llm_providers():
    return {"providers": list_providers()}


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: UUID, access: AccessService = Depends(get_access)):
    return AgentResponse(**dataclasses.asdict(await access.agent(agent_id)))


@router.delete("/{agent_id}/memory", status_code=204)
async def clear_agent_memory(agent_id: UUID, access: AccessService = Depends(get_access)):
    # Memory is in-process; clearing it requires the running orchestrator.
    # This endpoint verifies access and signals intent only.
    await access.agent(agent_id)
