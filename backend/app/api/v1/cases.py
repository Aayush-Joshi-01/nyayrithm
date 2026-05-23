from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query

from app.db.factory import get_repository
from app.db.session import get_session
from app.models.case import Case
from app.schemas.case import CaseCreate, CaseListResponse, CaseResponse, CaseUpdate

router = APIRouter()

# TODO: replace with real auth
MOCK_USER_ID = "user-001"


async def _get_case_repo(session=Depends(get_session)):
    return get_repository("case", session)


@router.post("/", response_model=CaseResponse, status_code=201)
async def create_case(body: CaseCreate, repo=Depends(_get_case_repo)):
    case = Case(
        title=body.title,
        description=body.description,
        country=body.country,
        jurisdiction=body.jurisdiction,
        legal_system=body.legal_system,
        created_by=MOCK_USER_ID,
        metadata=body.metadata,
    )
    created = await repo.create(case)
    return CaseResponse(**_case_to_dict(created))


@router.get("/", response_model=CaseListResponse)
async def list_cases(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    repo=Depends(_get_case_repo),
):
    filters = {}
    if status:
        filters["status"] = status
    items, total = await repo.list(filters=filters, page=page, size=size)
    return CaseListResponse(
        items=[CaseResponse(**_case_to_dict(c)) for c in items],
        total=total, page=page, size=size,
    )


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(case_id: UUID, repo=Depends(_get_case_repo)):
    case = await repo.get(str(case_id))
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return CaseResponse(**_case_to_dict(case))


@router.put("/{case_id}", response_model=CaseResponse)
async def update_case(case_id: UUID, body: CaseUpdate, repo=Depends(_get_case_repo)):
    data = body.model_dump(exclude_none=True)
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    updated = await repo.update(str(case_id), data)
    return CaseResponse(**_case_to_dict(updated))


@router.delete("/{case_id}", status_code=204)
async def delete_case(case_id: UUID, repo=Depends(_get_case_repo)):
    deleted = await repo.delete(str(case_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Case not found")


def _case_to_dict(case: Case) -> dict:
    import dataclasses
    return dataclasses.asdict(case)
