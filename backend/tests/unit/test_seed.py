from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.db.factory import get_repository
from app.db.stores import open_stores
from app.seed import (
    DEV_ATTORNEY_ID,
    DEV_CASE_ID,
    DEV_ORG_ID,
    DEV_OWNER_ID,
    ensure_default_plans,
    seed_dev_data,
)


async def test_default_plans_are_created_once(db_path):
    async with open_stores() as stores:
        assert await ensure_default_plans(stores) == 3
        assert await ensure_default_plans(stores) == 0
        plans, _ = await get_repository("plan", stores).list(size=10)
        assert {p.code for p in plans} == {"trial", "pro", "enterprise"}


async def test_dev_seed_builds_a_working_firm_and_is_idempotent(db_path):
    for _ in range(2):
        async with open_stores() as stores:
            await seed_dev_data(stores)

    async with open_stores() as stores:
        org = await get_repository("organization", stores).get(str(DEV_ORG_ID))
        assert org.name == "Dev Firm" and org.status == "active"
        members, _ = await get_repository("membership", stores).list(
            filters={"org_id": str(DEV_ORG_ID)}, size=10)
        assert {m.user_id: m.role for m in members} == {
            DEV_OWNER_ID: "owner", DEV_ATTORNEY_ID: "attorney"}
        subs, _ = await get_repository("subscription", stores).list(
            filters={"org_id": str(DEV_ORG_ID)}, size=10)
        assert len(subs) == 1 and subs[0].status == "active"
        assert await get_repository("case", stores).get(str(DEV_CASE_ID)) is not None
        _, total = await get_repository("case", stores).list(size=10)
        assert total == 1


async def test_open_dev_mode_lands_in_the_seeded_firm(client, db_path, monkeypatch):
    from app.config import get_settings

    async with open_stores() as stores:
        await seed_dev_data(stores)
    monkeypatch.setenv("DEV_AUTH_MODE", "open")
    get_settings.cache_clear()

    cases = (await client.get("/api/v1/cases/")).json()  # no token at all
    assert [c["title"] for c in cases["items"]] == ["State v. Sample (dev)"]


@pytest.mark.parametrize("env", [
    {"DEV_AUTH_MODE": "open"},
    {"DEV_AUTH_MODE": "credentials"},
    {"AUTH_DEV_BYPASS": "true"},
    {"SEED_DEV_DATA": "true"},
])
def test_production_refuses_every_dev_switch(monkeypatch, env):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "a-real-secret")
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    with pytest.raises(ValidationError, match="must not be enabled"):
        Settings(_env_file=None)


def test_production_is_fine_with_dev_switches_off(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "a-real-secret")
    for k in ("DEV_AUTH_MODE", "AUTH_DEV_BYPASS", "SEED_DEV_DATA"):
        monkeypatch.delenv(k, raising=False)
    assert Settings(_env_file=None).APP_ENV == "production"


def test_credentials_mode_does_not_bypass_authentication(monkeypatch):
    monkeypatch.setenv("DEV_AUTH_MODE", "credentials")
    assert Settings(_env_file=None).auth_bypass is False
    monkeypatch.setenv("DEV_AUTH_MODE", "open")
    assert Settings(_env_file=None).auth_bypass is True
