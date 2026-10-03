from __future__ import annotations

import asyncio
from uuid import UUID

import structlog

from app.tasks.celery_app import celery_app
from app.tasks.loop_utils import clear_loop_bound_caches

logger = structlog.get_logger()


@celery_app.task(name="app.tasks.evidence_tasks.ingest_evidence", bind=True, max_retries=3)
def ingest_evidence(self, evidence_id: str, case_id: str, file_path: str, mime_type: str):
    """
    Celery task: ingest + index a piece of evidence.
    Runs in the 'evidence' queue.
    """
    clear_loop_bound_caches()
    asyncio.run(_ingest_evidence_async(evidence_id, case_id, file_path, mime_type))


async def _ingest_evidence_async(
    evidence_id: str,
    case_id: str,
    file_path: str,
    mime_type: str,
) -> None:
    """Run ingestion with embedding/vision calls attributed to the evidence's firm."""
    from app.db.factory import get_repository
    from app.db.stores import open_stores
    from app.llm.metering import usage_context

    org_id = user_id = None
    try:
        async with open_stores() as stores:
            ev = await get_repository("evidence", stores).get(evidence_id)
            if ev:
                org_id = str(ev.org_id) if ev.org_id else None
                user_id = ev.uploaded_by
    except Exception as exc:  # noqa: BLE001 - metering context is optional
        logger.warning("evidence_usage_context_failed", error=str(exc))
    with usage_context(org_id=org_id, user_id=user_id):
        await _ingest_evidence_body(evidence_id, case_id, file_path, mime_type)


async def _ingest_evidence_body(
    evidence_id: str,
    case_id: str,
    file_path: str,
    mime_type: str,
) -> None:
    from app.ingestion.factory import get_ingester, detect_modality
    from app.rag.indexer import EvidenceIndexer
    from app.vector_db.factory import get_vector_store
    from app.storage.factory import get_file_storage
    from app.db.factory import get_repository
    from app.db.stores import open_stores
    from app.models.documents import EvidenceContent

    log = logger.bind(evidence_id=evidence_id, case_id=case_id)
    log.info("evidence_ingestion_started")

    try:
        # `file_path` is a storage key (e.g. "cases/<id>/evidence/<id>/name.txt").
        # Resolve it to a real local path the ingester can open.
        local_path = await get_file_storage().localize(file_path)

        # Ingest file
        ingester = get_ingester(mime_type)
        result = await ingester.ingest(local_path)
        modality = detect_modality(mime_type)

        # Index into vector store
        vector_store = get_vector_store()
        indexer = EvidenceIndexer(vector_store)
        chunk_count = await indexer.index_evidence(
            case_id=UUID(case_id),
            evidence_id=UUID(evidence_id),
            modality=modality,
            mime_type=mime_type,
            text=result.raw_text,
            segments=result.segments,
            extra_metadata=result.metadata,
        )

        # Update evidence record
        async with open_stores() as stores:
            from datetime import datetime, timezone

            # The extracted text itself lives in MongoDB; the Postgres row keeps status only.
            content_repo = get_repository("evidence_content", stores)
            await content_repo.delete_where({"evidence_id": evidence_id})
            await content_repo.create(EvidenceContent(
                evidence_id=UUID(evidence_id),
                case_id=UUID(case_id),
                raw_text=result.raw_text,
                transcription=result.transcription,
                segments=result.segments,
            ))
            repo = get_repository("evidence", stores)
            await repo.update(evidence_id, {
                "status": "indexed",
                "modality": modality,
                "chunk_count": chunk_count,
                "vector_collection": case_id,
                "metadata": result.metadata,
                "indexed_at": datetime.now(timezone.utc),
            })

        log.info("evidence_ingestion_completed", chunk_count=chunk_count)

    except Exception as exc:
        log.error("evidence_ingestion_failed", error=str(exc))
        async with open_stores() as stores:
            repo = get_repository("evidence", stores)
            await repo.update(evidence_id, {
                "status": "error",
                "error_message": str(exc),
            })
        raise
