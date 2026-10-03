from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import text

from app.core.auth import AuthenticatedUser
from app.core.exceptions import ConflictError, NotFoundError
from app.db.factory import get_repository
from app.db.stores import Stores
from app.models.case import Case
from app.models.tenancy import CaseMember
from app.schemas.case import CaseCreate, CaseUpdate
from app.services.access import AccessService
from app.services.entitlements import EntitlementService

logger = structlog.get_logger()


class CaseService:
    def __init__(self, stores: Stores, user: AuthenticatedUser) -> None:
        self.stores = stores
        self.user = user
        self.repo = get_repository("case", stores)
        self.access = AccessService(stores, user)
        self.ent = EntitlementService(stores)

    async def create(self, body: CaseCreate) -> Case:
        await self.ent.require_active(self.access.org_id)
        case = Case(
            title=body.title,
            description=body.description,
            country=body.country,
            jurisdiction=body.jurisdiction,
            legal_system=body.legal_system,
            created_by=self.user.id,
            org_id=self.access.org_id,  # type: ignore[arg-type]
            metadata=body.metadata,
        )
        return await self.repo.create(case)

    async def list(self, page: int, size: int, status: str | None) -> tuple[list[Case], int]:
        """The cases this user may see in their firm, newest first."""
        org = self.access.org_id
        params: dict[str, Any] = {"org": org, "uid": self.user.id,
                                  "limit": size, "offset": (page - 1) * size}
        where = "org_id = :org"
        if not self.user.is_firm_manager:
            where += (" AND (created_by = :uid OR id IN "
                      "(SELECT case_id FROM case_members WHERE user_id = :uid))")
        if status:
            where += " AND status = :status"
            params["status"] = status
        total = (await self.stores.pg.execute(
            text(f"SELECT COUNT(*) FROM cases WHERE {where}"), params)).scalar() or 0
        items = await self.repo.query(
            f"SELECT * FROM cases WHERE {where} ORDER BY created_at DESC LIMIT :limit OFFSET :offset",
            **params,
        )
        return items, int(total)

    async def get(self, case_id: UUID) -> Case:
        return await self.access.case(case_id)

    async def update(self, case_id: UUID, body: CaseUpdate) -> Case:
        await self.access.case(case_id)
        data = body.model_dump(exclude_none=True)
        data["updated_at"] = datetime.now(timezone.utc)
        return await self.repo.update(str(case_id), data)

    async def delete(self, case_id: UUID) -> None:
        case = await self.access.managed_case(case_id)
        cid = str(case.id)
        # Documents and vectors are not covered by Postgres cascades; clear them explicitly.
        await get_repository("evidence_content", self.stores).delete_where({"case_id": cid})
        sims, _ = await get_repository("simulation", self.stores).list(
            filters={"case_id": cid}, size=500
        )
        for sim in sims:
            await get_repository("turn", self.stores).delete_where({"simulation_id": str(sim.id)})
        # The uploaded files too (best-effort: a storage hiccup must not block the delete).
        from app.storage.factory import get_file_storage

        files, _ = await get_repository("evidence", self.stores).list(
            filters={"case_id": cid}, size=1000
        )
        for ev in files:
            try:
                await get_file_storage().delete(ev.file_path)
            except Exception as exc:  # noqa: BLE001
                logger.warning("case_file_delete_failed", evidence_id=str(ev.id), error=str(exc))
        try:
            from app.vector_db.factory import get_vector_store

            await get_vector_store().drop_collection(cid)
        except Exception as exc:  # noqa: BLE001
            logger.warning("case_vectors_drop_failed", case_id=cid, error=str(exc))
        await self.repo.delete(cid)

    # ── sharing ───────────────────────────────────────────────────────────────
    async def members(self, case_id: UUID) -> list[dict[str, Any]]:
        await self.access.case(case_id)
        shared, _ = await get_repository("case_member", self.stores).list(
            filters={"case_id": str(case_id)}, size=200
        )
        by_user = {
            m.user_id: m for m in (await get_repository("membership", self.stores).list(
                filters={"org_id": self.access.org_id, "status": "active"}, size=500))[0]
        }
        return [
            {"user_id": s.user_id, "email": by_user[s.user_id].email if s.user_id in by_user else "",
             "added_by": s.added_by, "created_at": s.created_at}
            for s in shared
        ]

    async def share(self, case_id: UUID, user_id: str) -> None:
        case = await self.access.managed_case(case_id)
        target, _ = await get_repository("membership", self.stores).list(
            filters={"org_id": str(case.org_id), "user_id": user_id, "status": "active"}, size=1
        )
        if not target:
            raise NotFoundError("Member", user_id)
        repo = get_repository("case_member", self.stores)
        if await repo.count({"case_id": str(case_id), "user_id": user_id}):
            raise ConflictError("The case is already shared with this person.")
        await repo.create(CaseMember(
            case_id=case_id, user_id=user_id, added_by=self.user.id  # type: ignore[arg-type]
        ))

    async def unshare(self, case_id: UUID, user_id: str) -> None:
        await self.access.managed_case(case_id)
        await get_repository("case_member", self.stores).delete_where(
            {"case_id": str(case_id), "user_id": user_id}
        )
