from __future__ import annotations

import dataclasses
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.deps import get_case_service
from app.schemas.case import CaseCreate, CaseListResponse, CaseResponse, CaseUpdate
from app.services.cases import CaseService

router = APIRouter()


def _out(case) -> CaseResponse:
    return CaseResponse(**dataclasses.asdict(case))


@router.post("/", response_model=CaseResponse, status_code=201)
async def create_case(body: CaseCreate, svc: CaseService = Depends(get_case_service)):
    return _out(await svc.create(body))


@router.get("/", response_model=CaseListResponse)
async def list_cases(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    svc: CaseService = Depends(get_case_service),
):
    items, total = await svc.list(page, size, status)
    return CaseListResponse(items=[_out(c) for c in items], total=total, page=page, size=size)


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(case_id: UUID, svc: CaseService = Depends(get_case_service)):
    return _out(await svc.get(case_id))


@router.put("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: UUID, body: CaseUpdate, svc: CaseService = Depends(get_case_service)
):
    return _out(await svc.update(case_id, body))


@router.delete("/{case_id}", status_code=204)
async def delete_case(case_id: UUID, svc: CaseService = Depends(get_case_service)):
    await svc.delete(case_id)


class ShareIn(BaseModel):
    user_id: str


@router.get("/{case_id}/members")
async def list_case_members(case_id: UUID, svc: CaseService = Depends(get_case_service)):
    return await svc.members(case_id)


@router.post("/{case_id}/members", status_code=201)
async def share_case(case_id: UUID, body: ShareIn, svc: CaseService = Depends(get_case_service)):
    await svc.share(case_id, body.user_id)
    return {"status": "shared"}


@router.delete("/{case_id}/members/{user_id}", status_code=204)
async def unshare_case(case_id: UUID, user_id: str, svc: CaseService = Depends(get_case_service)):
    await svc.unshare(case_id, user_id)
