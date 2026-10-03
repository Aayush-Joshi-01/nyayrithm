from __future__ import annotations

from fastapi import Depends, Header

from app.core.auth import AuthenticatedUser
from app.db.stores import Stores, get_stores
from app.dependencies import get_current_user
from app.services.access import AccessService
from app.services.cases import CaseService
from app.services.evidence import EvidenceService
from app.services.invites import InviteService
from app.services.orgs import OrgService, resolve_org_user
from app.services.simulations import SimulationService


async def get_org_user(
    stores: Stores = Depends(get_stores),
    user: AuthenticatedUser = Depends(get_current_user),
    x_org_id: str | None = Header(default=None),
) -> AuthenticatedUser:
    """The signed-in user acting for one firm (X-Org-Id, or their only firm)."""
    return await resolve_org_user(stores, user, x_org_id)


async def get_access(
    stores: Stores = Depends(get_stores), user: AuthenticatedUser = Depends(get_org_user)
) -> AccessService:
    return AccessService(stores, user)


async def get_case_service(
    stores: Stores = Depends(get_stores), user: AuthenticatedUser = Depends(get_org_user)
) -> CaseService:
    return CaseService(stores, user)


async def get_simulation_service(
    stores: Stores = Depends(get_stores), user: AuthenticatedUser = Depends(get_org_user)
) -> SimulationService:
    return SimulationService(stores, user)


async def get_evidence_service(
    stores: Stores = Depends(get_stores), user: AuthenticatedUser = Depends(get_org_user)
) -> EvidenceService:
    return EvidenceService(stores, user)


# Firm administration works on a firm named in the path, so it needs the user but not an
# active-firm header; membership in that firm is checked by the service.
async def get_org_service(
    stores: Stores = Depends(get_stores), user: AuthenticatedUser = Depends(get_current_user)
) -> OrgService:
    return OrgService(stores, user)


async def get_public_invite_service(stores: Stores = Depends(get_stores)) -> InviteService:
    """For the invite preview shown before sign-in: the secret link is the credential."""
    return InviteService(stores, AuthenticatedUser(id="anonymous"))


async def get_invite_service(
    stores: Stores = Depends(get_stores), user: AuthenticatedUser = Depends(get_current_user)
) -> InviteService:
    return InviteService(stores, user)
