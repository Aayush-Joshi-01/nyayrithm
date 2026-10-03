"""Platform-operator functions: firms, plans, subscriptions, user directory, activity log.

The operator manages *who has access to what*. It never reads what a firm works on: nothing
here touches cases' content, evidence, turns or audit payloads, only counts and metadata.
Every mutation is written to ``admin_events``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import text

from app.core.auth import AuthenticatedUser
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.db.factory import get_repository
from app.db.stores import Stores
from app.models.tenancy import AdminEvent, Organization, Plan, Subscription
from app.services.entitlements import EntitlementService, current_period
from app.services.invites import InviteService
from app.services.orgs import OrgService

SUB_STATUSES = ("trialing", "active", "past_due", "cancelled")
ORG_STATUSES = ("active", "suspended")


class AdminService:
    def __init__(self, stores: Stores, actor: AuthenticatedUser) -> None:
        self.stores = stores
        self.actor = actor
        self.orgs = get_repository("organization", stores)
        self.subs = get_repository("subscription", stores)
        self.plans = get_repository("plan", stores)
        self.members = get_repository("membership", stores)
        self.ent = EntitlementService(stores)

    async def record(self, action: str, target_type: str = "", target_id: str = "",
                     **details: Any) -> None:
        await get_repository("admin_event", self.stores).create(AdminEvent(
            actor=self.actor.email or self.actor.id, action=action,
            target_type=target_type, target_id=target_id, details=details,
        ))

    # ── firms ─────────────────────────────────────────────────────────────────
    async def _firm_row(self, org: Organization) -> dict[str, Any]:
        ent = await self.ent.get(org.id)
        members, pending = await self.ent.seats_in_use(org.id)
        usage = await self.ent.usage(org.id)
        return {
            "id": str(org.id), "name": org.name, "slug": org.slug, "status": org.status,
            "created_at": org.created_at,
            "plan": ent.plan.code if ent else None,
            "subscription_status": ent.subscription.status if ent else None,
            "period_end": ent.subscription.current_period_end if ent else None,
            "seats": {"used": members, "pending": pending,
                      "limit": ent.subscription.seats if ent else 0},
            "usage": usage,
        }

    async def list_firms(self, q: str | None, status: str | None, page: int, size: int
                         ) -> dict[str, Any]:
        where, params = ["1=1"], {"limit": size, "offset": (page - 1) * size}
        if q:
            where.append("(lower(name) LIKE :q OR lower(slug) LIKE :q)")
            params["q"] = f"%{q.lower()}%"
        if status:
            where.append("status = :status")
            params["status"] = status
        clause = " AND ".join(where)
        total = (await self.stores.pg.execute(
            text(f"SELECT COUNT(*) FROM organizations WHERE {clause}"), params)).scalar() or 0
        orgs = await self.orgs.query(
            f"SELECT * FROM organizations WHERE {clause} ORDER BY created_at DESC "
            "LIMIT :limit OFFSET :offset", **params)
        return {"items": [await self._firm_row(o) for o in orgs], "total": int(total),
                "page": page, "size": size}

    async def _org(self, org_id: UUID | str) -> Organization:
        org = await self.orgs.get(str(org_id))
        if org is None:
            raise NotFoundError("Firm", str(org_id))
        return org

    async def firm_detail(self, org_id: UUID | str) -> dict[str, Any]:
        org = await self._org(org_id)
        row = await self._firm_row(org)
        members, _ = await self.members.list(
            filters={"org_id": str(org.id)}, size=500, order_by="created_at")
        invites, _ = await get_repository("invite", self.stores).list(
            filters={"org_id": str(org.id), "status": "pending"}, size=200)
        # Counts only: the operator never sees what a firm's cases contain.
        counts = {}
        for table in ("cases", "simulations", "evidence"):
            counts[table] = (await self.stores.pg.execute(
                text(f"SELECT COUNT(*) FROM {table} WHERE org_id = :o"), {"o": str(org.id)}
            )).scalar() or 0
        history, _ = await get_repository("usage_counter", self.stores).list(
            filters={"org_id": str(org.id)}, size=12, order_by="period DESC")
        summary = await self.ent.summary(org.id)
        return {
            **row,
            "plan_detail": summary["plan"], "subscription": summary["subscription"],
            "members": [{"user_id": m.user_id, "email": m.email, "display_name": m.display_name,
                         "role": m.role, "status": m.status, "last_seen_at": m.last_seen_at}
                        for m in members],
            "pending_invites": [{"id": str(i.id), "email": i.email, "role": i.role,
                                 "expires_at": i.expires_at} for i in invites],
            "counts": {k: int(v) for k, v in counts.items()},
            "usage_history": [{"period": h.period, "tokens": int(h.tokens),
                               "cost_usd": float(h.cost_usd), "simulations": int(h.simulations),
                               "turns": int(h.turns)} for h in history],
        }

    async def create_firm(
        self, name: str, plan_code: str, seats: int, owner_email: str,
        period_end: datetime | None, invoice_ref: str, notes: str, status: str,
        invites: InviteService,
    ) -> dict[str, Any]:
        plan = await self._assignable_plan(plan_code)
        if status not in SUB_STATUSES:
            raise ValidationError(f"status must be one of {list(SUB_STATUSES)}")
        org = await OrgService(self.stores, self.actor).create_org(name)
        await self.subs.create(Subscription(
            org_id=org.id, plan_code=plan.code, status=status, seats=seats,
            current_period_end=period_end, invoice_ref=invoice_ref, notes=notes,
            set_by=self.actor.email or self.actor.id,
        ))
        invite, token = await invites.create_as_platform(org.id, owner_email)
        await self.record("firm.created", "firm", str(org.id), name=org.name, plan=plan.code,
                          seats=seats, owner_email=invite.email)
        from app.services.invites import invite_url

        return {**await self._firm_row(org), "owner_invite_url": invite_url(token)}

    async def update_firm(self, org_id: UUID | str, name: str | None, status: str | None
                          ) -> dict[str, Any]:
        org = await self._org(org_id)
        data: dict[str, Any] = {"updated_at": datetime.now(timezone.utc)}
        if name:
            data["name"] = name.strip()
        if status:
            if status not in ORG_STATUSES:
                raise ValidationError(f"status must be one of {list(ORG_STATUSES)}")
            data["status"] = status
        org = await self.orgs.update(str(org.id), data)
        await self.record("firm.updated", "firm", str(org.id),
                          **{k: v for k, v in data.items() if k != "updated_at"})
        return await self._firm_row(org)

    async def invite_owner(self, org_id: UUID | str, email: str, invites: InviteService
                           ) -> dict[str, Any]:
        org = await self._org(org_id)
        invite, token = await invites.create_as_platform(org.id, email)
        await self.record("firm.owner_invited", "firm", str(org.id), email=invite.email)
        from app.services.invites import invite_url

        return {"email": invite.email, "invite_url": invite_url(token)}

    # ── plans & subscriptions ─────────────────────────────────────────────────
    async def _plan(self, code: str) -> Plan:
        items, _ = await self.plans.list(filters={"code": code}, size=1)
        if not items:
            raise NotFoundError("Plan", code)
        return items[0]

    async def _assignable_plan(self, code: str) -> Plan:
        plan = await self._plan(code)
        if not plan.is_active:
            raise ConflictError(f"The '{code}' plan has been retired.")
        return plan

    async def list_plans(self) -> list[dict[str, Any]]:
        plans, _ = await self.plans.list(size=100, order_by="seat_limit")
        out = []
        for p in plans:
            firms = await self.subs.count({"plan_code": p.code})
            out.append({**_plan_dict(p), "firms": firms})
        return out

    async def upsert_plan(self, code: str, fields: dict[str, Any]) -> dict[str, Any]:
        items, _ = await self.plans.list(filters={"code": code}, size=1)
        if items:
            plan = await self.plans.update(str(items[0].id), fields)
            await self.record("plan.updated", "plan", code, **fields)
        else:
            plan = await self.plans.create(Plan(code=code, **fields))
            await self.record("plan.created", "plan", code, **fields)
        return _plan_dict(plan)

    async def retire_plan(self, code: str) -> None:
        plan = await self._plan(code)
        in_use = await self.subs.count({"plan_code": code})
        if in_use:
            raise ConflictError(f"{in_use} firm(s) are on this plan; move them first.")
        await self.plans.update(str(plan.id), {"is_active": False})
        await self.record("plan.retired", "plan", code)

    async def set_subscription(self, org_id: UUID | str, plan_code: str, status: str, seats: int,
                               period_end: datetime | None, invoice_ref: str, notes: str
                               ) -> dict[str, Any]:
        org = await self._org(org_id)
        plan = await self._assignable_plan(plan_code)
        if status not in SUB_STATUSES:
            raise ValidationError(f"status must be one of {list(SUB_STATUSES)}")
        data = {
            "plan_code": plan.code, "status": status, "seats": seats,
            "current_period_end": period_end, "invoice_ref": invoice_ref, "notes": notes,
            "set_by": self.actor.email or self.actor.id, "updated_at": datetime.now(timezone.utc),
        }
        existing, _ = await self.subs.list(filters={"org_id": str(org.id)}, size=1)
        if existing:
            await self.subs.update(str(existing[0].id), data)
        else:
            await self.subs.create(Subscription(org_id=org.id, **{
                k: v for k, v in data.items() if k != "updated_at"}))
        await self.record("subscription.set", "firm", str(org.id), plan=plan.code, status=status,
                          seats=seats, invoice_ref=invoice_ref)
        return await self._firm_row(org)

    # ── users (directory built from memberships) ──────────────────────────────
    async def list_users(self, q: str | None, page: int, size: int) -> dict[str, Any]:
        where, params = "1=1", {"limit": size, "offset": (page - 1) * size}
        if q:
            where = "(lower(m.email) LIKE :q OR lower(m.display_name) LIKE :q)"
            params["q"] = f"%{q.lower()}%"
        total = (await self.stores.pg.execute(
            text(f"SELECT COUNT(DISTINCT m.user_id) FROM memberships m WHERE {where}"), params
        )).scalar() or 0
        rows = (await self.stores.pg.execute(text(
            "SELECT m.user_id, MIN(m.email) AS email, MIN(m.display_name) AS display_name, "
            "MAX(m.last_seen_at) AS last_seen_at "
            f"FROM memberships m WHERE {where} GROUP BY m.user_id "
            "ORDER BY MIN(m.email) LIMIT :limit OFFSET :offset"), params)).all()
        items = []
        for r in rows:
            firms, _ = await self.members.list(filters={"user_id": r.user_id}, size=50)
            names = {}
            for m in firms:
                org = await self.orgs.get(str(m.org_id))
                names[str(m.org_id)] = org.name if org else ""
            items.append({
                "user_id": r.user_id, "email": r.email, "display_name": r.display_name,
                "last_seen_at": r.last_seen_at,
                "firms": [{"org_id": str(m.org_id), "name": names[str(m.org_id)],
                           "role": m.role, "status": m.status} for m in firms],
            })
        return {"items": items, "total": int(total), "page": page, "size": size}

    # ── activity ──────────────────────────────────────────────────────────────
    async def events(self, action: str | None, page: int, size: int) -> dict[str, Any]:
        filters = {"action": action} if action else None
        items, total = await get_repository("admin_event", self.stores).list(
            filters=filters, page=page, size=size)
        return {"items": [{"id": str(e.id), "actor": e.actor, "action": e.action,
                           "target_type": e.target_type, "target_id": e.target_id,
                           "details": e.details, "created_at": e.created_at} for e in items],
                "total": total, "page": page, "size": size}

    # ── overview ──────────────────────────────────────────────────────────────
    async def overview(self) -> dict[str, Any]:
        firms = await self.orgs.count()
        active = await self.orgs.count({"status": "active"})
        users = (await self.stores.pg.execute(text(
            "SELECT COUNT(DISTINCT user_id) FROM memberships WHERE status = 'active'"
        ))).scalar() or 0
        by_status = {}
        for s in SUB_STATUSES:
            by_status[s] = await self.subs.count({"status": s})
        month = (await self.stores.pg.execute(text(
            "SELECT COALESCE(SUM(tokens),0), COALESCE(SUM(cost_usd),0), "
            "COALESCE(SUM(simulations),0), COALESCE(SUM(turns),0) "
            "FROM usage_counters WHERE period = :p"), {"p": current_period()})).one()
        return {
            "firms": {"total": firms, "active": active, "suspended": firms - active},
            "users": int(users), "subscriptions": by_status,
            "this_month": {"period": current_period(), "tokens": int(month[0]),
                           "cost_usd": float(month[1]), "simulations": int(month[2]),
                           "turns": int(month[3])},
        }


def _plan_dict(p: Plan) -> dict[str, Any]:
    return {"code": p.code, "name": p.name, "seat_limit": p.seat_limit,
            "monthly_simulations": p.monthly_simulations, "monthly_tokens": int(p.monthly_tokens),
            "max_turns_per_sim": p.max_turns_per_sim, "storage_mb": p.storage_mb,
            "features": p.features, "is_active": bool(p.is_active)}
