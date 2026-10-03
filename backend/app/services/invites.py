"""Inviting attorneys to a firm.

An invite is bound to an email address and carries a random single-use token; only the
token's SHA-256 is stored. The invitee signs in (or registers) with that email and accepts.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import structlog

from app.config import get_settings
from app.core.auth import AuthenticatedUser
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    GoneError,
    NotFoundError,
    ValidationError,
)
from app.db.factory import get_repository
from app.db.stores import Stores
from app.models.tenancy import ORG_ROLES, ROLE_ADMIN, ROLE_ATTORNEY, ROLE_OWNER, Invite, Membership
from app.services.entitlements import EntitlementService
from app.services.orgs import OrgService

logger = structlog.get_logger()

INVITE_TTL = timedelta(days=7)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def invite_url(token: str) -> str:
    return f"{get_settings().APP_URL.rstrip('/')}/invite/{token}"


def _aware(value: Any) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _queue_email(invite: Invite, org_name: str, inviter: str, token: str) -> None:
    from app.tasks.notification_tasks import send_invite_email

    send_invite_email.delay(
        to=invite.email, org_name=org_name, role=invite.role, inviter=inviter,
        url=invite_url(token),
    )


class InviteService:
    def __init__(self, stores: Stores, user: AuthenticatedUser) -> None:
        self.stores = stores
        self.user = user
        self.repo = get_repository("invite", stores)
        self.orgs = OrgService(stores, user)
        self.ent = EntitlementService(stores)

    # ── firm side ─────────────────────────────────────────────────────────────
    async def create(self, org_id: UUID | str, email: str, role: str) -> tuple[Invite, str]:
        me = await self.orgs.require_member(org_id, ROLE_OWNER, ROLE_ADMIN)
        if role == ROLE_OWNER and me.role != ROLE_OWNER:
            raise ForbiddenError("Only an owner can invite another owner.")
        return await self._create(org_id, email, role)

    async def create_as_platform(
        self, org_id: UUID | str, email: str, role: str = ROLE_OWNER
    ) -> tuple[Invite, str]:
        """Used by the admin portal to invite a firm's first owner (the firm has no members yet)."""
        return await self._create(org_id, email, role)

    async def _create(self, org_id: UUID | str, email: str, role: str) -> tuple[Invite, str]:
        email = email.strip().lower()
        if "@" not in email:
            raise ValidationError("Enter a valid email address.")
        if role not in ORG_ROLES:
            raise ValidationError(f"role must be one of {list(ORG_ROLES)}")

        # Already a member?
        existing, _ = await get_repository("membership", self.stores).list(
            filters={"org_id": str(org_id), "email": email, "status": "active"}, size=1
        )
        if existing:
            raise ConflictError(f"{email} is already a member of this firm.")
        # One live invite per address: re-inviting replaces it rather than stacking.
        pending, _ = await self.repo.list(
            filters={"org_id": str(org_id), "email": email, "status": "pending"}, size=50
        )
        for old in pending:
            await self.repo.update(str(old.id), {"status": "revoked"})

        await self.ent.check_seat_available(org_id)

        token = secrets.token_urlsafe(32)
        invite = await self.repo.create(Invite(
            org_id=org_id,  # type: ignore[arg-type]
            email=email, role=role, token_hash=hash_token(token),
            invited_by=self.user.id, expires_at=datetime.now(timezone.utc) + INVITE_TTL,
        ))
        org = await get_repository("organization", self.stores).get(str(org_id))
        _queue_email(invite, org.name if org else "your firm", self.user.email or self.user.id,
                     token)
        return invite, token

    async def list(self, org_id: UUID | str) -> list[Invite]:
        await self.orgs.require_member(org_id, ROLE_OWNER, ROLE_ADMIN)
        items, _ = await self.repo.list(
            filters={"org_id": str(org_id), "status": "pending"}, size=200
        )
        return items

    async def _get(self, org_id: UUID | str, invite_id: UUID | str) -> Invite:
        invite = await self.repo.get(str(invite_id))
        if invite is None or str(invite.org_id) != str(org_id):
            raise NotFoundError("Invite", str(invite_id))
        return invite

    async def resend(self, org_id: UUID | str, invite_id: UUID | str) -> tuple[Invite, str]:
        await self.orgs.require_member(org_id, ROLE_OWNER, ROLE_ADMIN)
        invite = await self._get(org_id, invite_id)
        if invite.status != "pending":
            raise ConflictError(f"This invite is {invite.status}.")
        token = secrets.token_urlsafe(32)  # the old link stops working
        invite = await self.repo.update(str(invite.id), {
            "token_hash": hash_token(token),
            "expires_at": datetime.now(timezone.utc) + INVITE_TTL,
        })
        org = await get_repository("organization", self.stores).get(str(org_id))
        _queue_email(invite, org.name if org else "your firm", self.user.email or self.user.id,
                     token)
        return invite, token

    async def revoke(self, org_id: UUID | str, invite_id: UUID | str) -> None:
        await self.orgs.require_member(org_id, ROLE_OWNER, ROLE_ADMIN)
        invite = await self._get(org_id, invite_id)
        if invite.status == "pending":
            await self.repo.update(str(invite.id), {"status": "revoked"})

    # ── invitee side ──────────────────────────────────────────────────────────
    async def _by_token(self, token: str) -> Invite:
        items, _ = await self.repo.list(filters={"token_hash": hash_token(token)}, size=1)
        if not items:
            raise NotFoundError("Invite", "token")
        return items[0]

    @staticmethod
    def _check_usable(invite: Invite) -> None:
        if invite.status == "accepted":
            raise GoneError("This invitation has already been used.")
        if invite.status == "revoked":
            raise GoneError("This invitation was withdrawn.")
        if _aware(invite.expires_at) < datetime.now(timezone.utc):
            raise GoneError("This invitation has expired. Ask your firm for a new one.")

    async def preview(self, token: str) -> dict[str, Any]:
        """What the accept page shows before sign-in. Reveals only what the link holder needs."""
        invite = await self._by_token(token)
        self._check_usable(invite)
        org = await get_repository("organization", self.stores).get(str(invite.org_id))
        return {"org_name": org.name if org else "", "email": invite.email, "role": invite.role,
                "expires_at": invite.expires_at}

    async def accept(self, token: str) -> Membership:
        invite = await self._by_token(token)
        self._check_usable(invite)

        email = (self.user.email or "").strip().lower()
        if email != invite.email.lower():
            raise ForbiddenError(
                f"This invitation was sent to {invite.email}. Sign in with that address.",
                "INVITE_EMAIL_MISMATCH",
            )
        await self.ent.require_active(invite.org_id)
        org = await get_repository("organization", self.stores).get(str(invite.org_id))
        if org is None or org.status != "active":
            raise GoneError("This firm is no longer active.")

        members = get_repository("membership", self.stores)
        existing, _ = await members.list(
            filters={"org_id": str(invite.org_id), "user_id": self.user.id}, size=1
        )
        if existing:
            member = existing[0]
            if member.status != "active":
                member = await members.update(str(member.id), {"status": "active",
                                                               "role": invite.role})
        else:
            # The invite already holds a seat, so only the active members count here.
            await self.ent.check_seat_available(invite.org_id, for_accept=True)
            member = await members.create(Membership(
                org_id=invite.org_id, user_id=self.user.id, email=email, role=invite.role,
                display_name=self.user.username or email,
            ))
        await self.repo.update(str(invite.id), {
            "status": "accepted", "accepted_by": self.user.id,
            "accepted_at": datetime.now(timezone.utc),
        })
        logger.info("invite_accepted", org_id=str(invite.org_id), role=invite.role)
        return member


_ = ROLE_ATTORNEY
