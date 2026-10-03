from __future__ import annotations

import dataclasses
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.api.deps import get_evidence_service
from app.schemas.evidence import EvidenceListResponse, EvidenceResponse
from app.schemas.turn import SearchRequest, SearchResultSchema
from app.services.evidence import EvidenceService

router = APIRouter()


def _out(ev) -> EvidenceResponse:
    return EvidenceResponse(**dataclasses.asdict(ev))


@router.post("/cases/{case_id}/evidence/", response_model=EvidenceResponse, status_code=201)
async def upload_evidence(
    case_id: UUID,
    file: UploadFile = File(...),
    title: str = "",
    description: str = "",
    svc: EvidenceService = Depends(get_evidence_service),
):
    content = await file.read()
    evidence = await svc.upload(
        case_id, file.filename, file.content_type, content, title=title, description=description
    )
    return _out(evidence)


@router.get("/cases/{case_id}/evidence/", response_model=EvidenceListResponse)
async def list_evidence(
    case_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    svc: EvidenceService = Depends(get_evidence_service),
):
    items, total = await svc.list(case_id, page, size)
    return EvidenceListResponse(items=[_out(e) for e in items], total=total, page=page, size=size)


@router.get("/cases/{case_id}/evidence/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(
    case_id: UUID, evidence_id: UUID, svc: EvidenceService = Depends(get_evidence_service)
):
    return _out(await svc.get(case_id, evidence_id))


@router.delete("/cases/{case_id}/evidence/{evidence_id}", status_code=204)
async def delete_evidence(
    case_id: UUID, evidence_id: UUID, svc: EvidenceService = Depends(get_evidence_service)
):
    await svc.delete(case_id, evidence_id)


@router.post("/cases/{case_id}/evidence/{evidence_id}/reindex", status_code=202)
async def reindex_evidence(
    case_id: UUID, evidence_id: UUID, svc: EvidenceService = Depends(get_evidence_service)
):
    await svc.reindex(case_id, evidence_id)
    return {"status": "reindex_queued"}


@router.post("/cases/{case_id}/search", response_model=list[SearchResultSchema])
async def search_evidence(
    case_id: UUID, body: SearchRequest, svc: EvidenceService = Depends(get_evidence_service)
):
    return await svc.search(case_id, body.query, body.top_k, body.modality)
