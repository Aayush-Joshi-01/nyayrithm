from __future__ import annotations

"""The firm's plan is enforced on the server: status, limits, and the mid-run quota pause."""

import io
import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

import tests.conftest
from app.services.entitlements import EntitlementService, current_period


@pytest.fixture
def mk(seed):
    """A firm with one owner and given plan limits / subscription state."""
    def make(**kw):
        org = seed.org(kw.pop("name", "Acme LLP"), **kw)
        seed.member(org, "owner", "owner")
        return org
    return make


async def create_case(client, headers):
    return await client.post("/api/v1/cases/", headers=headers,
                             json={"title": "New matter", "country": "India"})


# ── subscription status ───────────────────────────────────────────────────────
@pytest.mark.parametrize("status", ["active", "trialing"])
async def test_active_and_trialing_firms_can_work(client, mk, auth_headers, status):
    mk(sub_status=status)
    assert (await create_case(client, auth_headers("owner", provision=False))).status_code == 201


@pytest.mark.parametrize("status", ["past_due", "cancelled"])
async def test_lapsed_subscriptions_cannot_create_cases(client, mk, auth_headers, status):
    mk(sub_status=status)
    r = await create_case(client, auth_headers("owner", provision=False))
    assert r.status_code == 402 and r.json()["error"] == "SUBSCRIPTION_INACTIVE"


async def test_an_expired_period_counts_as_inactive(client, mk, auth_headers):
    mk(period_end=(datetime.now(timezone.utc) - timedelta(days=1)).isoformat())
    r = await create_case(client, auth_headers("owner", provision=False))
    assert r.status_code == 402 and "ended" in r.json()["message"]


async def test_a_future_period_end_is_fine(client, mk, auth_headers):
    mk(period_end=(datetime.now(timezone.utc) + timedelta(days=30)).isoformat())
    assert (await create_case(client, auth_headers("owner", provision=False))).status_code == 201


async def test_a_firm_with_no_subscription_cannot_work(client, seed, auth_headers):
    org = seed.org("Unbilled")
    conn = sqlite3.connect(seed.path)
    conn.execute("DELETE FROM subscriptions WHERE org_id = ?", [org])
    conn.commit()
    conn.close()
    seed.member(org, "owner", "owner")
    r = await create_case(client, auth_headers("owner", provision=False))
    assert r.status_code == 402


async def test_lapsed_firms_can_still_read_their_data(client, mk, seed, auth_headers):
    org = mk(sub_status="cancelled")
    case = seed.case("owner", org=org)
    h = auth_headers("owner", provision=False)
    assert (await client.get(f"/api/v1/cases/{case}", headers=h)).status_code == 200


# ── simulation limits ─────────────────────────────────────────────────────────
async def test_max_turns_is_capped_by_the_plan(client, mk, seed, auth_headers):
    org = mk(plan="small", plan_limits={"max_turns_per_sim": 20})
    case = seed.case("owner", org=org)
    h = auth_headers("owner", provision=False)
    ok = await client.post(f"/api/v1/cases/{case}/simulations/", headers=h,
                           json={"title": "ok", "max_turns": 20})
    too_long = await client.post(f"/api/v1/cases/{case}/simulations/", headers=h,
                                 json={"title": "long", "max_turns": 21})
    assert ok.status_code == 201
    assert too_long.status_code == 402 and too_long.json()["error"] == "QUOTA_EXCEEDED"


async def test_monthly_simulation_allowance(client, mk, seed, auth_headers, queued):
    org = mk(plan="two", plan_limits={"monthly_simulations": 2})
    case = seed.case("owner", org=org)
    h = auth_headers("owner", provision=False)
    ids = []
    for i in range(3):
        r = await client.post(f"/api/v1/cases/{case}/simulations/", headers=h,
                              json={"title": f"s{i}"})
        ids.append(r.json()["id"])
    assert (await client.post(f"/api/v1/simulations/{ids[0]}/start", headers=h)).status_code == 202
    assert (await client.post(f"/api/v1/simulations/{ids[1]}/start", headers=h)).status_code == 202
    third = await client.post(f"/api/v1/simulations/{ids[2]}/start", headers=h)
    assert third.status_code == 402 and "simulations" in third.json()["message"]
    assert queued["run"].call_count == 2


async def test_resuming_a_paused_simulation_does_not_use_another_allowance(
    client, mk, seed, auth_headers, queued
):
    org = mk(plan="one", plan_limits={"monthly_simulations": 1})
    case = seed.case("owner", org=org)
    h = auth_headers("owner", provision=False)
    sim = (await client.post(f"/api/v1/cases/{case}/simulations/", headers=h,
                             json={"title": "s"})).json()["id"]
    await client.post(f"/api/v1/simulations/{sim}/start", headers=h)
    await client.post(f"/api/v1/simulations/{sim}/pause", headers=h)
    assert (await client.post(f"/api/v1/simulations/{sim}/start", headers=h)).status_code == 202


async def test_token_budget_blocks_starting(client, mk, seed, auth_headers, queued, db_path):
    org = mk(plan="tiny", plan_limits={"monthly_tokens": 1000})
    sim = seed.simulation(seed.case("owner", org=org), "owner")
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO usage_counters (id, org_id, period, tokens) VALUES ('u1', ?, ?, 1000)",
        [org, current_period()])
    conn.commit()
    conn.close()
    r = await client.post(f"/api/v1/simulations/{sim}/start",
                          headers=auth_headers("owner", provision=False))
    assert r.status_code == 402 and "token" in r.json()["message"]


async def test_usage_is_tracked_per_month(db_path, seed):
    from app.db.stores import open_stores

    org = seed.org("Meter")
    async with open_stores() as stores:
        ent = EntitlementService(stores)
        await ent.add_usage(org, tokens=100, cost_usd=0.5, turns=1)
        await ent.add_usage(org, tokens=50, cost_usd=0.25, simulations=1)
        usage = await ent.usage(org)
        assert usage == {"period": current_period(), "tokens": 150, "cost_usd": 0.75,
                         "simulations": 1, "turns": 1}
        assert (await ent.usage(org, "2020-01"))["tokens"] == 0


# ── evidence storage ──────────────────────────────────────────────────────────
async def test_evidence_storage_cap(client, mk, seed, auth_headers, queued):
    org = mk(plan="mini", plan_limits={"storage_mb": 1})
    case = seed.case("owner", org=org)
    h = auth_headers("owner", provision=False)

    def up(n):
        return client.post(f"/api/v1/cases/{case}/evidence/", headers=h,
                           files={"file": ("a.txt", io.BytesIO(b"x" * n), "text/plain")})

    assert (await up(700_000)).status_code == 201
    r = await up(700_000)
    assert r.status_code == 402 and "storage" in r.json()["message"]
    assert (await up(200_000)).status_code == 201  # still room for a smaller file


# ── what the firm sees ────────────────────────────────────────────────────────
async def test_firm_can_read_its_plan_and_usage_but_not_change_it(client, mk, auth_headers):
    org = mk(plan="pro", seats=7)
    h = auth_headers("owner", provision=False)
    body = (await client.get(f"/api/v1/orgs/{org}/subscription", headers=h)).json()
    assert body["subscription"]["status"] == "active" and body["subscription"]["seats"] == 7
    assert body["plan"]["code"] == "pro" and body["seats"] == {"used": 1, "pending": 0, "limit": 7}
    usage = (await client.get(f"/api/v1/orgs/{org}/usage", headers=h)).json()
    assert usage["usage"]["period"] == current_period()
    for method in ("put", "patch", "delete", "post"):
        r = await getattr(client, method)(f"/api/v1/orgs/{org}/subscription", headers=h)
        assert r.status_code == 405


async def test_other_firms_cannot_read_a_subscription(client, mk, auth_headers):
    org = mk()
    assert (await client.get(f"/api/v1/orgs/{org}/subscription",
                             headers=auth_headers("outsider"))).status_code == 404


# ── the mid-run quota pause (engine) ──────────────────────────────────────────
async def test_engine_pauses_a_run_when_the_token_budget_is_spent(
    mk, seed, auth_headers, queued, db_path, monkeypatch
):
    """The budget is checked before every turn, so a run stops the moment it is gone."""
    from app.config import get_settings
    from app.db.stores import open_stores
    from app.simulation.engine import SimulationEngine

    monkeypatch.setenv("SIMULATION_TURN_DELAY_SECONDS", "0")
    get_settings.cache_clear()
    monkeypatch.setattr("app.simulation.engine.get_vector_store", lambda: None)

    org = mk(plan="tiny", plan_limits={"monthly_tokens": 100})
    sim = seed.simulation(seed.case("owner", org=org), "owner", status="running", max_turns=10)
    seed.agent(sim, "judge")
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO usage_counters (id, org_id, period, tokens) VALUES ('u1', ?, ?, 100)",
        [org, current_period()])
    conn.commit()
    conn.close()

    events: list[tuple[str, dict]] = []

    async def broadcast(event, payload):
        events.append((event, payload))

    await SimulationEngine().run_simulation(sim, broadcast_fn=broadcast)

    kinds = [e for e, _ in events]
    assert "quota.exceeded" in kinds and "simulation.paused" in kinds
    assert "turn.started" not in kinds  # not a single turn was spent
    conn = sqlite3.connect(db_path)
    (status,) = conn.execute("SELECT status FROM simulations WHERE id = ?", [sim]).fetchone()
    (reason,) = conn.execute(
        "SELECT payload FROM audit_events WHERE event_type = 'simulation.paused'").fetchone()
    conn.close()
    assert status == "paused" and "quota_exceeded" in reason
    assert tests.conftest._SYNC_MONGO["turns"].count_documents({"simulation_id": sim}) == 0

    async with open_stores() as stores:
        assert await EntitlementService(stores).tokens_exhausted(org)
