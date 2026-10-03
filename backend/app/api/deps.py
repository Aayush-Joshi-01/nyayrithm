from __future__ import annotations

from fastapi import Depends

from app.core.auth import AuthenticatedUser
from app.db.stores import get_stores
from app.dependencies import get_current_user
from app.services.access import AccessService
from app.services.cases import CaseService
from app.services.evidence import EvidenceService
from app.services.simulations import SimulationService


async def get_access(
    stores=Depends(get_stores), user: AuthenticatedUser = Depends(get_current_user)
) -> AccessService:
    return AccessService(stores, user)


async def get_case_service(
    stores=Depends(get_stores), user: AuthenticatedUser = Depends(get_current_user)
) -> CaseService:
    return CaseService(stores, user)


async def get_simulation_service(
    stores=Depends(get_stores), user: AuthenticatedUser = Depends(get_current_user)
) -> SimulationService:
    return SimulationService(stores, user)


async def get_evidence_service(
    stores=Depends(get_stores), user: AuthenticatedUser = Depends(get_current_user)
) -> EvidenceService:
    return EvidenceService(stores, user)
