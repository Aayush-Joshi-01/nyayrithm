from __future__ import annotations

"""Platform-operator API. Every route needs the ``platform_admin`` realm role.

It manages access and consumption (firms, plans, subscriptions, users, usage); it exposes no
case, evidence, turn or audit content.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.core.auth import AuthenticatedUser
from app.db.stores import Stores, get_stores
from app.dependencies import require_platform_admin
from app.services import system_health
from app.services.admin import AdminService
from app.services.invites import InviteService
from app.services.keycloak_admin import KeycloakAdmin
from app.services.llmops import LlmOpsService

router = APIRouter(prefix="/admin", tags=["admin"])


async def get_admin(
    stores: Stores = Depends(get_stores), user: AuthenticatedUser = Depends(require_platform_admin)
) -> AdminService:
    return AdminService(stores, user)


async def get_admin_invites(
    stores: Stores = Depends(get_stores), user: AuthenticatedUser = Depends(require_platform_admin)
) -> InviteService:
    return InviteService(stores, user)


class FirmCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    plan_code: str
    seats: int = Field(5, ge=1, le=100_000)
    owner_email: str = Field(..., min_length=3, max_length=254)
    period_end: datetime | None = None
    invoice_ref: str = ""
    notes: str = ""
    status: str = "active"


class FirmUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    status: str | None = None


class OwnerInvite(BaseModel):
    email: str = Field(..., min_length=3, max_length=254)


class SubscriptionSet(BaseModel):
    plan_code: str
    status: str = "active"
    seats: int = Field(5, ge=1, le=100_000)
    period_end: datetime | None = None
    invoice_ref: str = ""
    notes: str = ""


class PlanSet(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    seat_limit: int = Field(5, ge=1)
    monthly_simulations: int = Field(50, ge=0)
    monthly_tokens: int = Field(2_000_000, ge=0)
    max_turns_per_sim: int = Field(100, ge=1)
    storage_mb: int = Field(5_000, ge=0)
    features: dict[str, Any] = {}
    is_active: bool = True


class PriceSet(BaseModel):
    provider: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)
    input_per_mtok: float = Field(..., ge=0)
    output_per_mtok: float = Field(..., ge=0)


# ── overview / system / activity ──────────────────────────────────────────────
@router.get("/overview")
async def overview(svc: AdminService = Depends(get_admin)):
    return await svc.overview()


@router.get("/system")
async def system(
    stores: Stores = Depends(get_stores), _: AuthenticatedUser = Depends(require_platform_admin)
):
    checks = await system_health.check_all(stores)
    return {"ok": all(c["ok"] for c in checks), "checks": checks}


@router.get("/events")
async def activity(
    action: str | None = None, page: int = Query(1, ge=1), size: int = Query(50, ge=1, le=200),
    svc: AdminService = Depends(get_admin),
):
    return await svc.events(action, page, size)


# ── firms ─────────────────────────────────────────────────────────────────────
@router.get("/firms")
async def list_firms(
    q: str | None = None, status: str | None = None, page: int = Query(1, ge=1),
    size: int = Query(25, ge=1, le=100), svc: AdminService = Depends(get_admin),
):
    return await svc.list_firms(q, status, page, size)


@router.post("/firms", status_code=201)
async def create_firm(
    body: FirmCreate, svc: AdminService = Depends(get_admin),
    invites: InviteService = Depends(get_admin_invites),
):
    return await svc.create_firm(
        body.name, body.plan_code, body.seats, body.owner_email, body.period_end,
        body.invoice_ref, body.notes, body.status, invites,
    )


@router.get("/firms/{org_id}")
async def firm_detail(org_id: UUID, svc: AdminService = Depends(get_admin)):
    return await svc.firm_detail(org_id)


@router.patch("/firms/{org_id}")
async def update_firm(org_id: UUID, body: FirmUpdate, svc: AdminService = Depends(get_admin)):
    return await svc.update_firm(org_id, body.name, body.status)


@router.post("/firms/{org_id}/owner-invite", status_code=201)
async def invite_owner(
    org_id: UUID, body: OwnerInvite, svc: AdminService = Depends(get_admin),
    invites: InviteService = Depends(get_admin_invites),
):
    return await svc.invite_owner(org_id, body.email, invites)


@router.put("/firms/{org_id}/subscription")
async def set_subscription(
    org_id: UUID, body: SubscriptionSet, svc: AdminService = Depends(get_admin)
):
    return await svc.set_subscription(
        org_id, body.plan_code, body.status, body.seats, body.period_end, body.invoice_ref,
        body.notes,
    )


# ── plans ─────────────────────────────────────────────────────────────────────
@router.get("/plans")
async def list_plans(svc: AdminService = Depends(get_admin)):
    return await svc.list_plans()


@router.put("/plans/{code}")
async def upsert_plan(code: str, body: PlanSet, svc: AdminService = Depends(get_admin)):
    return await svc.upsert_plan(code.lower().strip(), body.model_dump())


@router.delete("/plans/{code}", status_code=204)
async def retire_plan(code: str, svc: AdminService = Depends(get_admin)):
    await svc.retire_plan(code)


# ── users ─────────────────────────────────────────────────────────────────────
@router.get("/users")
async def list_users(
    q: str | None = None, page: int = Query(1, ge=1), size: int = Query(25, ge=1, le=100),
    svc: AdminService = Depends(get_admin),
):
    return await svc.list_users(q, page, size)


@router.post("/users/{user_id}/disable", status_code=204)
async def disable_user(user_id: str, svc: AdminService = Depends(get_admin)):
    await KeycloakAdmin().set_enabled(user_id, False)
    await svc.record("user.disabled", "user", user_id)


@router.post("/users/{user_id}/enable", status_code=204)
async def enable_user(user_id: str, svc: AdminService = Depends(get_admin)):
    await KeycloakAdmin().set_enabled(user_id, True)
    await svc.record("user.enabled", "user", user_id)


# ── LLMOps ────────────────────────────────────────────────────────────────────
async def get_llmops(
    stores: Stores = Depends(get_stores), _: AuthenticatedUser = Depends(require_platform_admin)
) -> LlmOpsService:
    return LlmOpsService(stores)


@router.get("/llmops/summary")
async def llmops_summary(
    days: int = Query(30, ge=1, le=365), org_id: str | None = None,
    svc: LlmOpsService = Depends(get_llmops),
):
    return await svc.summary(days, org_id)


@router.get("/llmops/timeseries")
async def llmops_timeseries(
    days: int = Query(30, ge=1, le=365), bucket: str = Query("day", pattern="^(day|hour)$"),
    org_id: str | None = None, svc: LlmOpsService = Depends(get_llmops),
):
    return await svc.timeseries(days, bucket, org_id)


@router.get("/llmops/breakdown")
async def llmops_breakdown(
    by: str = Query("model", pattern="^(provider|model|role|firm|kind)$"),
    days: int = Query(30, ge=1, le=365), org_id: str | None = None,
    svc: LlmOpsService = Depends(get_llmops),
):
    return await svc.breakdown(by, days, org_id)


@router.get("/llmops/failures")
async def llmops_failures(
    days: int = Query(7, ge=1, le=365), limit: int = Query(50, ge=1, le=200),
    svc: LlmOpsService = Depends(get_llmops),
):
    return await svc.failures(days, limit)


@router.get("/llmops/quota")
async def llmops_quota(svc: LlmOpsService = Depends(get_llmops)):
    return await svc.quota()


@router.get("/llmops/prices")
async def llmops_prices(svc: LlmOpsService = Depends(get_llmops)):
    return await svc.prices()


@router.put("/llmops/prices", status_code=204)
async def llmops_set_price(
    body: PriceSet, svc: LlmOpsService = Depends(get_llmops),
    admin: AdminService = Depends(get_admin),
):
    await svc.set_price(body.provider, body.model, body.input_per_mtok, body.output_per_mtok,
                        admin.actor.email or admin.actor.id)
    await admin.record("price.set", "model", f"{body.provider}/{body.model}",
                       input=body.input_per_mtok, output=body.output_per_mtok)


@router.delete("/llmops/prices/{provider}/{model:path}", status_code=204)
async def llmops_clear_price(
    provider: str, model: str, svc: LlmOpsService = Depends(get_llmops),
    admin: AdminService = Depends(get_admin),
):
    await svc.clear_price(provider, model)
    await admin.record("price.cleared", "model", f"{provider}/{model}")
