from __future__ import annotations

import dataclasses
import mimetypes
import os
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from app.db.factory import get_repository
from app.db.session import get_session
from app.ingestion.factory import detect_modality
from app.models.evidence import Evidence
from app.schemas.evidence import EvidenceListResponse, EvidenceResponse
from app.schemas.turn import SearchRequest, SearchResultSchema
from app.storage.factory import get_file_storage

router = APIRouter()
MOCK_USER_ID = "user-001"


async def _ev_repo(session=Depends(get_session)):
    return get_repository("evidence", session)


@router.post("/cases/{case_id}/evidence/", response_model=EvidenceResponse, status_code=201)
async def upload_evidence(
    case_id: str,
    file: UploadFile = File(...),
    title: str = "",
    description: str = "",
    repo=Depends(_ev_repo),
):
    storage = get_file_storage()
    mime_type = file.content_type or mimetypes.guess_type(file.filename or "")[0] or "text/plain"
    modality = detect_modality(mime_type)
    key = f"cases/{case_id}/evidence/{uuid4()}/{file.filename}"

    content = await file.read()
    file_size = len(content)

    import io
    await storage.upload(key, io.BytesIO(content), mime_type)

    evidence = Evidence(
        case_id=case_id,  # type: ignore[arg-type]
        title=title or file.filename or "Untitled",
        description=description,
        evidence_type=_guess_type(mime_type),
        file_path=key,
        file_size=file_size,
        mime_type=mime_type,
        modality=modality,
        uploaded_by=MOCK_USER_ID,
        status="pending",
    )
    created = await repo.create(evidence)

    # Trigger async ingestion
    from app.tasks.evidence_tasks import ingest_evidence
    ingest_evidence.delay(
        str(created.id), case_id, key, mime_type
    )

    return EvidenceResponse(**dataclasses.asdict(created))


@router.get("/cases/{case_id}/evidence/", response_model=EvidenceListResponse)
async def list_evidence(
    case_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, le=100),
    repo=Depends(_ev_repo),
):
    items, total = await repo.list(filters={"case_id": case_id}, page=page, size=size)
    return EvidenceListResponse(
        items=[EvidenceResponse(**dataclasses.asdict(e)) for e in items],
        total=total, page=page, size=size,
    )


@router.get("/cases/{case_id}/evidence/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(case_id: str, evidence_id: str, repo=Depends(_ev_repo)):
    ev = await repo.get(evidence_id)
    if not ev or str(ev.case_id) != case_id:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return EvidenceResponse(**dataclasses.asdict(ev))


@router.delete("/cases/{case_id}/evidence/{evidence_id}", status_code=204)
async def delete_evidence(case_id: str, evidence_id: str, repo=Depends(_ev_repo)):
    ev = await repo.get(evidence_id)
    if not ev or str(ev.case_id) != case_id:
        raise HTTPException(status_code=404, detail="Evidence not found")
    await repo.delete(evidence_id)


@router.post("/cases/{case_id}/evidence/{evidence_id}/reindex", status_code=202)
async def reindex_evidence(case_id: str, evidence_id: str, repo=Depends(_ev_repo)):
    ev = await repo.get(evidence_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")
    await repo.update(evidence_id, {"status": "pending"})
    from app.tasks.evidence_tasks import ingest_evidence
    ingest_evidence.delay(evidence_id, case_id, ev.file_path, ev.mime_type)
    return {"status": "reindex_queued"}


@router.post("/cases/{case_id}/search", response_model=list[SearchResultSchema])
async def search_evidence(case_id: str, body: SearchRequest, repo=Depends(_ev_repo)):
    from app.rag.retriever import EvidenceRetriever
    from app.vector_db.factory import get_vector_store
    from uuid import UUID

    retriever = EvidenceRetriever(get_vector_store())
    results = await retriever.search_case(
        query=body.query,
        case_id=UUID(case_id),
        top_k=body.top_k,
        modality=body.modality,
    )

    output = []
    for r in results:
        ev_id = r.chunk.metadata.get("evidence_id", "")
        ev = await repo.get(ev_id) if ev_id else None
        output.append(SearchResultSchema(
            chunk_id=r.chunk.id,
            evidence_id=ev_id,
            evidence_title=ev.title if ev else ev_id,
            text=r.chunk.text,
            modality=r.chunk.modality,
            score=r.score,
            metadata=r.chunk.metadata,
        ))
    return output


def _guess_type(mime: str) -> str:
    if "pdf" in mime:
        return "pdf"
    if "word" in mime or "docx" in mime:
        return "docx"
    if mime.startswith("audio/"):
        return "audio"
    if mime.startswith("video/"):
        return "video"
    if mime.startswith("image/"):
        return "image"
    return "text"
