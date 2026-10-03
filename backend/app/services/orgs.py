"""Firms and their members."""

from __future__ import annotations

import dataclasses
import re
from typing import Any
from uuid import UUID

from app.core.auth import AuthenticatedUser
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NoOrganizationError,
    NotFoundError,
    OrgSuspendedError,
    ValidationError,
)
from app.db.factory import get_repository
from app.db.stores import Stores
from app.models.tenancy import (
    ORG_ROLES,
    ROLE_ADMIN,
    ROLE_ATTORNEY,
    ROLE_OWNER,
    Membership,
    Organization,
)


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:60] or "firm"


async def memberships_of(stores: Stores, user_id: str) -> list[Membership]:
    items, _ = await get_repository("membership", stores).list(
        filters={"user_id": user_id, "status": "active"}, size=100, order_by="created_at"
    )
    return items


async def resolve_org_user(
    stores: Stores, user: AuthenticatedUser, requested_org: str | None = None
) -> AuthenticatedUser:
    """Attach the firm and the firm role this request acts under.

    The firm comes from the ``X-Org-Id`` header when given (it must be one the user belongs
    to), otherwise from their only membership (the oldest, if there are several).
    """
    memberships = await memberships_of(stores, user.id)
    if not memberships:
        raise NoOrganizationError()
    if requested_org:
        chosen = next((m for m in memberships if str(m.org_id) == requested_org), None)
        if chosen is None:
            raise ForbiddenError("You are not a member of that firm.")
    else:
        chosen = memberships[0]
    org = await get_repository("organization", stores).get(str(chosen.org_id))
    if org is None:
        raise NoOrganizationError()
    if org.status != "active":
        raise OrgSuspendedError()
    return dataclasses.replace(user, org_id=str(chosen.org_id), org_role=chosen.role)


class OrgService:
    def __init__(self, stores: Stores, user: AuthenticatedUser) -> None:
        self.stores = stores
        self.user = user
        self.orgs = get_repository("organization", stores)
        self.members = get_repository("membership", stores)

    # ── who am I ──────────────────────────────────────────────────────────────
    async def my_firms(self) -> list[dict[str, Any]]:
        out = []
        for m in await memberships_of(self.stores, self.user.id):
            org = await self.orgs.get(str(m.org_id))
            if org:
                out.append({"org_id": str(org.id), "name": org.name, "slug": org.slug,
                            "status": org.status, "role": m.role})
        return out

    async def require_member(self, org_id: UUID | str, *roles: str) -> Membership:
        """The caller's active membership in ``org_id``, optionally restricted to ``roles``."""
        items, _ = await self.members.list(
            filters={"org_id": str(org_id), "user_id": self.user.id, "status": "active"}, size=1
        )
        if not items:
            raise NotFoundError("Organization", str(org_id))
        if roles and items[0].role not in roles:
            raise ForbiddenError("Your role does not allow this.")
        org = await self.orgs.get(str(org_id))
        if org is None:
            raise NotFoundError("Organization", str(org_id))
        if org.status != "active":
            raise OrgSuspendedError()
        return items[0]

    # ── members ───────────────────────────────────────────────────────────────
    async def list_members(self, org_id: UUID | str) -> list[Membership]:
        await self.require_member(org_id)
        items, _ = await self.members.list(
            filters={"org_id": str(org_id), "status": "active"}, size=500, order_by="created_at"
        )
        return items

    async def _target(self, org_id: UUID | str, user_id: str) -> Membership:
        items, _ = await self.members.list(
            filters={"org_id": str(org_id), "user_id": user_id, "status": "active"}, size=1
        )
        if not items:
            raise NotFoundError("Member", user_id)
        return items[0]

    async def _owner_count(self, org_id: UUID | str) -> int:
        return await self.members.count(
            {"org_id": str(org_id), "role": ROLE_OWNER, "status": "active"}
        )

    async def change_role(self, org_id: UUID | str, user_id: str, new_role: str) -> Membership:
        me = await self.require_member(org_id, ROLE_OWNER, ROLE_ADMIN)
        if new_role not in ORG_ROLES:
            raise ValidationError(f"role must be one of {list(ORG_ROLES)}")
        target = await self._target(org_id, user_id)
        if me.role == ROLE_ADMIN and (target.role == ROLE_OWNER or new_role == ROLE_OWNER):
            raise ForbiddenError("Only an owner can change an owner's role or make one.")
        if target.role == ROLE_OWNER and new_role != ROLE_OWNER \
                and await self._owner_count(org_id) <= 1:
            raise ConflictError("A firm must keep at least one owner.")
        return await self.members.update(str(target.id), {"role": new_role})

    async def remove_member(self, org_id: UUID | str, user_id: str) -> None:
        me = await self.require_member(org_id, ROLE_OWNER, ROLE_ADMIN)
        target = await self._target(org_id, user_id)
        if me.role == ROLE_ADMIN and target.role != ROLE_ATTORNEY:
            raise ForbiddenError("Admins can only remove attorneys.")
        if target.role == ROLE_OWNER and await self._owner_count(org_id) <= 1:
            raise ConflictError("A firm must keep at least one owner.")
        await self.members.update(str(target.id), {"status": "removed"})

    # ── used by the admin portal and the dev seeder ───────────────────────────
    async def create_org(self, name: str, slug: str | None = None) -> Organization:
        slug = slugify(slug or name)
        base, n = slug, 1
        while (await self.orgs.list(filters={"slug": slug}, size=1))[0]:
            n += 1
            slug = f"{base}-{n}"
        return await self.orgs.create(Organization(name=name.strip(), slug=slug))
