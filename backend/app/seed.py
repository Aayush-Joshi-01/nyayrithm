"""Startup data.

``ensure_default_plans`` runs everywhere: a platform with no plans cannot sell anything, and
the operator edits them in the admin portal afterwards.

``seed_dev_data`` runs only with SEED_DEV_DATA=true (refused in production): a "Dev Firm" with
the same accounts as keycloak/realm-dev.json, so both dev auth modes land in a working firm.
Everything is keyed by fixed ids, so running it twice changes nothing.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import structlog

from app.db.factory import get_repository
from app.db.stores import Stores
from app.models.case import Case
from app.models.tenancy import Membership, Organization, Plan, Subscription

logger = structlog.get_logger()

# Fixed identities shared with keycloak/realm-dev.json (Keycloak user ids).
DEV_PLATFORM_ADMIN_ID = "00000000-0000-4000-8000-0000000000a1"
DEV_OWNER_ID = "00000000-0000-4000-8000-0000000000b1"
DEV_ATTORNEY_ID = "00000000-0000-4000-8000-0000000000c1"
DEV_ORG_ID = UUID("00000000-0000-4000-8000-0000000000d1")
DEV_CASE_ID = UUID("00000000-0000-4000-8000-0000000000e1")

DEFAULT_PLANS: tuple[dict, ...] = (
    {"code": "trial", "name": "Trial", "seat_limit": 3, "monthly_simulations": 10,
     "monthly_tokens": 500_000, "max_turns_per_sim": 30, "storage_mb": 500},
    {"code": "pro", "name": "Professional", "seat_limit": 25, "monthly_simulations": 200,
     "monthly_tokens": 10_000_000, "max_turns_per_sim": 100, "storage_mb": 20_000},
    {"code": "enterprise", "name": "Enterprise", "seat_limit": 500, "monthly_simulations": 5_000,
     "monthly_tokens": 200_000_000, "max_turns_per_sim": 300, "storage_mb": 500_000},
)


async def ensure_default_plans(stores: Stores) -> int:
    repo = get_repository("plan", stores)
    created = 0
    for spec in DEFAULT_PLANS:
        existing, _ = await repo.list(filters={"code": spec["code"]}, size=1)
        if not existing:
            await repo.create(Plan(**spec))
            created += 1
    return created


async def seed_dev_data(stores: Stores) -> None:
    await ensure_default_plans(stores)
    orgs = get_repository("organization", stores)
    if await orgs.get(str(DEV_ORG_ID)) is None:
        await orgs.create(Organization(id=DEV_ORG_ID, name="Dev Firm", slug="dev-firm"))

    subs = get_repository("subscription", stores)
    if not (await subs.list(filters={"org_id": str(DEV_ORG_ID)}, size=1))[0]:
        await subs.create(Subscription(
            org_id=DEV_ORG_ID, plan_code="pro", status="active", seats=10,
            current_period_end=datetime.now(timezone.utc) + timedelta(days=3650),
            invoice_ref="DEV-0001", notes="Seeded development subscription", set_by="seed",
        ))

    members = get_repository("membership", stores)
    for user_id, email, name, role in (
        (DEV_OWNER_ID, "owner@devfirm.nyayrithm.dev", "Asha Rao", "owner"),
        (DEV_ATTORNEY_ID, "attorney@devfirm.nyayrithm.dev", "Vikram Sethi", "attorney"),
    ):
        if not (await members.list(filters={"org_id": str(DEV_ORG_ID), "user_id": user_id},
                                   size=1))[0]:
            await members.create(Membership(
                org_id=DEV_ORG_ID, user_id=user_id, email=email, display_name=name, role=role,
            ))

    cases = get_repository("case", stores)
    if await cases.get(str(DEV_CASE_ID)) is None:
        await cases.create(Case(
            id=DEV_CASE_ID, org_id=DEV_ORG_ID, created_by=DEV_OWNER_ID,
            title="State v. Sample (dev)", country="India", jurisdiction="Delhi",
            legal_system="common_law",
            description="A sample prosecution for criminal breach of trust, for trying out "
                        "simulations in development.",
        ))
    logger.info("dev_data_seeded", org="Dev Firm")
