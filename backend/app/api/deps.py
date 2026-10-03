from __future__ import annotations

from fastapi import Depends

from app.core.auth import AuthenticatedUser
from app.db.session import get_session
from app.dependencies import get_current_user
from app.services.access import AccessService
from app.services.cases import CaseService
from app.services.evidence import EvidenceService
from app.services.simulations import SimulationService


async def get_access(
    session=Depends(get_session), user: AuthenticatedUser = Depends(get_current_user)
) -> AccessService:
    return AccessService(session, user)


async def get_case_service(
    session=Depends(get_session), user: AuthenticatedUser = Depends(get_current_user)
) -> CaseService:
    return CaseService(session, user)


async def get_simulation_service(
    session=Depends(get_session), user: AuthenticatedUser = Depends(get_current_user)
) -> SimulationService:
    return SimulationService(session, user)


async def get_evidence_service(
    session=Depends(get_session), user: AuthenticatedUser = Depends(get_current_user)
) -> EvidenceService:
    return EvidenceService(session, user)
