from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import get_invite_service, get_org_service, get_public_invite_service
from app.db.stores import Stores, get_stores
from app.models.tenancy import ORG_ROLES, Invite, Membership
from app.services.entitlements import EntitlementService
from app.services.invites import InviteService, invite_url
from app.services.orgs import OrgService

router = APIRouter()


class MemberOut(BaseModel):
    user_id: str
    email: str
    display_name: str
    role: str
    created_at: datetime


class RoleChange(BaseModel):
    role: str


class InviteCreate(BaseModel):
    email: str = Field(..., min_length=3, max_length=254)
    role: str = "attorney"


class InviteOut(BaseModel):
    id: UUID
    email: str
    role: str
    status: str
    expires_at: datetime
    created_at: datetime
    # Only present when the invite is created or re-sent: the one-time link to share by hand
    # if the email is slow or lands in spam.
    invite_url: str | None = None


class TokenIn(BaseModel):
    token: str = Field(..., min_length=10, max_length=200)


def _member(m: Membership) -> MemberOut:
    return MemberOut(user_id=m.user_id, email=m.email, display_name=m.display_name,
                     role=m.role, created_at=m.created_at)


def _invite(i: Invite, token: str | None = None) -> InviteOut:
    return InviteOut(
        id=i.id, email=i.email, role=i.role, status=i.status, expires_at=i.expires_at,
        created_at=i.created_at, invite_url=invite_url(token) if token else None,
    )


# ── my firms ──────────────────────────────────────────────────────────────────
@router.get("/orgs/me")
async def my_firms(svc: OrgService = Depends(get_org_service)):
    u = svc.user
    return {
        "user": {"id": u.id, "email": u.email, "name": u.username or u.email,
                 "platform_admin": u.is_platform_admin},
        "firms": await svc.my_firms(),
        "roles": list(ORG_ROLES),
    }


# ── members ───────────────────────────────────────────────────────────────────
@router.get("/orgs/{org_id}/members", response_model=list[MemberOut])
async def list_members(org_id: UUID, svc: OrgService = Depends(get_org_service)):
    return [_member(m) for m in await svc.list_members(org_id)]


@router.patch("/orgs/{org_id}/members/{user_id}", response_model=MemberOut)
async def change_member_role(
    org_id: UUID, user_id: str, body: RoleChange, svc: OrgService = Depends(get_org_service)
):
    return _member(await svc.change_role(org_id, user_id, body.role))


@router.delete("/orgs/{org_id}/members/{user_id}", status_code=204)
async def remove_member(org_id: UUID, user_id: str, svc: OrgService = Depends(get_org_service)):
    await svc.remove_member(org_id, user_id)


# ── subscription and usage (read-only for the firm) ───────────────────────────
@router.get("/orgs/{org_id}/subscription")
async def firm_subscription(
    org_id: UUID,
    svc: OrgService = Depends(get_org_service),
    stores: Stores = Depends(get_stores),
) -> dict[str, Any]:
    await svc.require_member(org_id)
    return await EntitlementService(stores).summary(org_id)


@router.get("/orgs/{org_id}/usage")
async def firm_usage(
    org_id: UUID,
    period: str | None = Query(None, pattern=r"^\d{4}-\d{2}$"),
    svc: OrgService = Depends(get_org_service),
    stores: Stores = Depends(get_stores),
) -> dict[str, Any]:
    await svc.require_member(org_id)
    summary = await EntitlementService(stores).summary(org_id)
    if period:
        summary["usage"] = await EntitlementService(stores).usage(org_id, period)
    return summary


# ── invites ───────────────────────────────────────────────────────────────────
@router.get("/orgs/{org_id}/invites", response_model=list[InviteOut])
async def list_invites(org_id: UUID, svc: InviteService = Depends(get_invite_service)):
    return [_invite(i) for i in await svc.list(org_id)]


@router.post("/orgs/{org_id}/invites", response_model=InviteOut, status_code=201)
async def create_invite(
    org_id: UUID, body: InviteCreate, svc: InviteService = Depends(get_invite_service)
):
    invite, token = await svc.create(org_id, body.email, body.role)
    return _invite(invite, token)


@router.post("/orgs/{org_id}/invites/{invite_id}/resend", response_model=InviteOut)
async def resend_invite(
    org_id: UUID, invite_id: UUID, svc: InviteService = Depends(get_invite_service)
):
    invite, token = await svc.resend(org_id, invite_id)
    return _invite(invite, token)


@router.delete("/orgs/{org_id}/invites/{invite_id}", status_code=204)
async def revoke_invite(
    org_id: UUID, invite_id: UUID, svc: InviteService = Depends(get_invite_service)
):
    await svc.revoke(org_id, invite_id)


@router.get("/invites/preview")
async def preview_invite(token: str = Query(..., min_length=10, max_length=200),
                         svc: InviteService = Depends(get_public_invite_service)):
    return await svc.preview(token)


@router.post("/invites/accept", response_model=MemberOut)
async def accept_invite(body: TokenIn, svc: InviteService = Depends(get_invite_service)):
    return _member(await svc.accept(body.token))
