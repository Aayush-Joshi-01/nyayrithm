from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.core.auth import AuthenticatedUser
from app.db.factory import get_repository
from app.models.case import Case
from app.schemas.case import CaseCreate, CaseUpdate
from app.services.access import AccessService


class CaseService:
    def __init__(self, session: Any, user: AuthenticatedUser) -> None:
        self.user = user
        self.repo = get_repository("case", session)
        self.access = AccessService(session, user)

    async def create(self, body: CaseCreate) -> Case:
        case = Case(
            title=body.title,
            description=body.description,
            country=body.country,
            jurisdiction=body.jurisdiction,
            legal_system=body.legal_system,
            created_by=self.user.id,
            metadata=body.metadata,
        )
        return await self.repo.create(case)

    async def list(self, page: int, size: int, status: str | None) -> tuple[list[Case], int]:
        filters: dict[str, Any] = {"created_by": self.user.id}
        if status:
            filters["status"] = status
        return await self.repo.list(filters=filters, page=page, size=size)

    async def get(self, case_id: UUID) -> Case:
        return await self.access.case(case_id)

    async def update(self, case_id: UUID, body: CaseUpdate) -> Case:
        await self.access.case(case_id)
        data = body.model_dump(exclude_none=True)
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        return await self.repo.update(str(case_id), data)

    async def delete(self, case_id: UUID) -> None:
        await self.access.case(case_id)
        await self.repo.delete(str(case_id))
