"""What a firm's subscription allows, and how much of it has been used this month.

Billing is manual: the platform admin sets a subscription (plan, seats, period, status).
Everything here only reads that row and the plan it points at, so a payment gateway can
later write the same rows without changing enforcement.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text

from app.core.exceptions import QuotaExceededError, SeatLimitError, SubscriptionInactiveError
from app.db.factory import get_repository
from app.db.stores import Stores
from app.models.tenancy import Plan, Subscription

ACTIVE_STATUSES = ("active", "trialing")


def current_period() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _as_aware(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


@dataclass
class Entitlement:
    subscription: Subscription
    plan: Plan

    @property
    def seats(self) -> int:
        return self.subscription.seats


class EntitlementService:
    def __init__(self, stores: Stores) -> None:
        self.stores = stores

    # ── subscription lookup ───────────────────────────────────────────────────
    async def get(self, org_id: UUID | str) -> Entitlement | None:
        subs, _ = await get_repository("subscription", self.stores).list(
            filters={"org_id": str(org_id)}, size=1
        )
        if not subs:
            return None
        plans, _ = await get_repository("plan", self.stores).list(
            filters={"code": subs[0].plan_code}, size=1
        )
        if not plans:
            return None
        return Entitlement(subscription=subs[0], plan=plans[0])

    async def require_active(self, org_id: UUID | str) -> Entitlement:
        ent = await self.get(org_id)
        if ent is None:
            raise SubscriptionInactiveError("The firm has no subscription.")
        sub = ent.subscription
        if sub.status not in ACTIVE_STATUSES:
            raise SubscriptionInactiveError(f"The firm's subscription is {sub.status}.")
        end = _as_aware(sub.current_period_end)
        if end is not None and end < datetime.now(timezone.utc):
            raise SubscriptionInactiveError("The firm's subscription period has ended.")
        if not ent.plan.is_active:
            raise SubscriptionInactiveError("The firm's plan has been retired.")
        return ent

    # ── seats ─────────────────────────────────────────────────────────────────
    async def seats_in_use(self, org_id: UUID | str) -> tuple[int, int]:
        """(active members, pending invites)."""
        members = await get_repository("membership", self.stores).count(
            {"org_id": str(org_id), "status": "active"}
        )
        pending = await get_repository("invite", self.stores).count(
            {"org_id": str(org_id), "status": "pending"}
        )
        return members, pending

    async def check_seat_available(self, org_id: UUID | str, *, for_accept: bool = False) -> None:
        """An invite reserves a seat, so accepting one never needs a spare seat of its own."""
        ent = await self.require_active(org_id)
        members, pending = await self.seats_in_use(org_id)
        used = members + (0 if for_accept else pending)
        if used >= ent.seats:
            raise SeatLimitError(ent.seats)

    # ── usage ─────────────────────────────────────────────────────────────────
    async def usage(self, org_id: UUID | str, period: str | None = None) -> dict[str, Any]:
        period = period or current_period()
        counters, _ = await get_repository("usage_counter", self.stores).list(
            filters={"org_id": str(org_id), "period": period}, size=1
        )
        c = counters[0] if counters else None
        return {
            "period": period,
            "tokens": int(c.tokens) if c else 0,
            "cost_usd": float(c.cost_usd) if c else 0.0,
            "simulations": int(c.simulations) if c else 0,
            "turns": int(c.turns) if c else 0,
        }

    async def storage_used_bytes(self, org_id: UUID | str) -> int:
        result = await self.stores.pg.execute(
            text("SELECT COALESCE(SUM(file_size), 0) FROM evidence WHERE org_id = :org"),
            {"org": str(org_id)},
        )
        return int(result.scalar() or 0)

    async def add_usage(
        self, org_id: UUID | str, *, tokens: int = 0, cost_usd: float = 0.0,
        simulations: int = 0, turns: int = 0,
    ) -> None:
        """Atomically add to this month's counters (one row per firm per month)."""
        await self.stores.pg.execute(
            text(
                "INSERT INTO usage_counters "
                "(id, org_id, period, tokens, cost_usd, simulations, turns, updated_at) "
                "VALUES (:id, :org, :period, :tokens, :cost, :sims, :turns, :now) "
                "ON CONFLICT (org_id, period) DO UPDATE SET "
                "tokens = usage_counters.tokens + :tokens, "
                "cost_usd = usage_counters.cost_usd + :cost, "
                "simulations = usage_counters.simulations + :sims, "
                "turns = usage_counters.turns + :turns, "
                "updated_at = :now"
            ),
            {"id": str(uuid4()), "org": str(org_id), "period": current_period(),
             "tokens": tokens, "cost": cost_usd, "sims": simulations, "turns": turns,
             "now": datetime.now(timezone.utc)},
        )
        await self.stores.pg.commit()

    # ── simulation limits ─────────────────────────────────────────────────────
    async def check_can_create_simulation(self, org_id: UUID | str, max_turns: int) -> Entitlement:
        ent = await self.require_active(org_id)
        if max_turns > ent.plan.max_turns_per_sim:
            raise QuotaExceededError(
                f"The {ent.plan.name} plan allows at most {ent.plan.max_turns_per_sim} turns "
                "per simulation."
            )
        return ent

    async def check_can_start_simulation(
        self, org_id: UUID | str, *, first_start: bool
    ) -> Entitlement:
        ent = await self.require_active(org_id)
        used = await self.usage(org_id)
        if used["tokens"] >= ent.plan.monthly_tokens:
            raise QuotaExceededError("The firm's monthly token allowance has been used up.")
        if first_start and used["simulations"] >= ent.plan.monthly_simulations:
            raise QuotaExceededError(
                f"The firm has used all {ent.plan.monthly_simulations} simulations for this month."
            )
        return ent

    async def tokens_exhausted(self, org_id: UUID | str) -> bool:
        """Checked before every turn so a run stops the moment the budget is gone."""
        ent = await self.get(org_id)
        if ent is None:
            return True
        used = await self.usage(org_id)
        return used["tokens"] >= ent.plan.monthly_tokens

    async def check_storage(self, org_id: UUID | str, incoming_bytes: int) -> None:
        ent = await self.require_active(org_id)
        used = await self.storage_used_bytes(org_id)
        if used + incoming_bytes > ent.plan.storage_mb * 1024 * 1024:
            raise QuotaExceededError(
                f"The firm's {ent.plan.storage_mb} MB evidence storage allowance is full."
            )

    async def summary(self, org_id: UUID | str) -> dict[str, Any]:
        ent = await self.get(org_id)
        members, pending = await self.seats_in_use(org_id)
        usage = await self.usage(org_id)
        if ent is None:
            return {"subscription": None, "plan": None, "seats": {"used": members,
                    "pending": pending, "limit": 0}, "usage": usage}
        sub, plan = ent.subscription, ent.plan
        return {
            "subscription": {
                "status": sub.status, "seats": sub.seats,
                "current_period_start": sub.current_period_start,
                "current_period_end": sub.current_period_end,
                "invoice_ref": sub.invoice_ref,
            },
            "plan": {
                "code": plan.code, "name": plan.name, "seat_limit": plan.seat_limit,
                "monthly_simulations": plan.monthly_simulations,
                "monthly_tokens": plan.monthly_tokens,
                "max_turns_per_sim": plan.max_turns_per_sim, "storage_mb": plan.storage_mb,
                "features": plan.features,
            },
            "seats": {"used": members, "pending": pending, "limit": sub.seats},
            "usage": usage,
            "storage_used_bytes": await self.storage_used_bytes(org_id),
        }
