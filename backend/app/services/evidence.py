from __future__ import annotations

import io
import mimetypes
import os
import re
from typing import Any
from uuid import UUID, uuid4

import structlog

from app.config import get_settings
from app.core.auth import AuthenticatedUser
from app.core.exceptions import PayloadTooLargeError, ValidationError
from app.db.factory import get_repository
from app.db.stores import Stores
from app.ingestion.factory import detect_modality
from app.models.evidence import Evidence
from app.schemas.turn import SearchResultSchema
from app.services.access import AccessService
from app.storage.factory import get_file_storage

logger = structlog.get_logger()

_UNSAFE_NAME = re.compile(r"[^A-Za-z0-9._\- ]")


def safe_filename(name: str | None) -> str:
    """Strip any directory part and unsafe characters from a client-supplied name."""
    base = os.path.basename((name or "").replace("\\", "/")).strip()
    base = _UNSAFE_NAME.sub("_", base).lstrip(".")
    return base[:200] or "upload"


def guess_type(mime: str) -> str:
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


class EvidenceService:
    def __init__(self, stores: Stores, user: AuthenticatedUser) -> None:
        self.user = user
        self.repo = get_repository("evidence", stores)
        self.access = AccessService(stores, user)

    async def upload(
        self,
        case_id: UUID,
        filename: str | None,
        content_type: str | None,
        content: bytes,
        title: str = "",
        description: str = "",
    ) -> Evidence:
        await self.access.case(case_id)

        max_bytes = get_settings().MAX_UPLOAD_MB * 1024 * 1024
        if not content:
            raise ValidationError("The uploaded file is empty")
        if len(content) > max_bytes:
            raise PayloadTooLargeError(
                f"File exceeds the {get_settings().MAX_UPLOAD_MB} MB upload limit"
            )

        name = safe_filename(filename)
        mime_type = content_type or mimetypes.guess_type(name)[0] or "text/plain"
        key = f"cases/{case_id}/evidence/{uuid4()}/{name}"
        await get_file_storage().upload(key, io.BytesIO(content), mime_type)

        evidence = await self.repo.create(Evidence(
            case_id=case_id,  # type: ignore[arg-type]
            title=title or name,
            description=description,
            evidence_type=guess_type(mime_type),
            file_path=key,
            file_size=len(content),
            mime_type=mime_type,
            modality=detect_modality(mime_type),
            uploaded_by=self.user.id,
            status="pending",
        ))
        self._queue_ingestion(evidence.id, case_id, key, mime_type)
        return evidence

    @staticmethod
    def _queue_ingestion(evidence_id: UUID | str, case_id: UUID, key: str, mime_type: str) -> None:
        from app.tasks.evidence_tasks import ingest_evidence

        ingest_evidence.delay(str(evidence_id), str(case_id), key, mime_type)

    async def list(self, case_id: UUID, page: int, size: int) -> tuple[list[Evidence], int]:
        await self.access.case(case_id)
        return await self.repo.list(filters={"case_id": str(case_id)}, page=page, size=size)

    async def get(self, case_id: UUID, evidence_id: UUID) -> Evidence:
        return await self.access.evidence(case_id, evidence_id)

    async def delete(self, case_id: UUID, evidence_id: UUID) -> None:
        ev = await self.access.evidence(case_id, evidence_id)

        # Best-effort de-index from the vector store and removal of the stored file.
        try:
            from app.rag.indexer import EvidenceIndexer
            from app.vector_db.factory import get_vector_store

            indexer = EvidenceIndexer(get_vector_store())
            await indexer.delete_evidence(case_id, evidence_id, ev.chunk_count or 0)
        except Exception as exc:  # noqa: BLE001
            logger.warning("evidence_deindex_failed", evidence_id=str(evidence_id), error=str(exc))
        try:
            await get_file_storage().delete(ev.file_path)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "evidence_file_delete_failed", evidence_id=str(evidence_id), error=str(exc)
            )
        await self.repo.delete(str(evidence_id))

    async def reindex(self, case_id: UUID, evidence_id: UUID) -> None:
        ev = await self.access.evidence(case_id, evidence_id)
        await self.repo.update(str(evidence_id), {"status": "pending"})
        self._queue_ingestion(evidence_id, case_id, ev.file_path, ev.mime_type)

    async def search(
        self, case_id: UUID, query: str, top_k: int, modality: str | None
    ) -> list[SearchResultSchema]:
        await self.access.case(case_id)

        from app.rag.retriever import EvidenceRetriever
        from app.vector_db.factory import get_vector_store

        results = await EvidenceRetriever(get_vector_store()).search_case(
            query=query, case_id=case_id, top_k=top_k, modality=modality
        )
        output: list[SearchResultSchema] = []
        for r in results:
            ev_id = r.chunk.metadata.get("evidence_id", "")
            ev = await self.repo.get(ev_id) if ev_id else None
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
