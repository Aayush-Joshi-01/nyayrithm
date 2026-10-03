from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest

import tests.conftest
from app.llm.pricing import price_book

ADMIN = {"roles": ["user", "platform_admin"]}


@pytest.fixture
def admin(auth_headers):
    return auth_headers("root", provision=False, **ADMIN)


@pytest.fixture
def sent(monkeypatch):
    calls: list[dict] = []
    from app.tasks.notification_tasks import send_invite_email

    monkeypatch.setattr(send_invite_email, "delay", lambda **kw: calls.append(kw))
    return calls


@pytest.fixture(autouse=True)
def _prices():
    price_book.set_overrides([])
    yield
    price_book.set_overrides([])


@pytest.fixture
def plans(seed):
    seed.plan("pro")
    seed.plan("trial", seat_limit=3)


ADMIN_ROUTES = [
    ("GET", "/api/v1/admin/overview", None),
    ("GET", "/api/v1/admin/system", None),
    ("GET", "/api/v1/admin/events", None),
    ("GET", "/api/v1/admin/firms", None),
    ("POST", "/api/v1/admin/firms", {"name": "X Co", "plan_code": "pro", "owner_email": "a@b.co"}),
    ("GET", "/api/v1/admin/firms/6f1c3a3e-0000-4000-8000-000000000000", None),
    ("PATCH", "/api/v1/admin/firms/6f1c3a3e-0000-4000-8000-000000000000", {"status": "suspended"}),
    ("PUT", "/api/v1/admin/firms/6f1c3a3e-0000-4000-8000-000000000000/subscription",
     {"plan_code": "pro"}),
    ("GET", "/api/v1/admin/plans", None),
    ("PUT", "/api/v1/admin/plans/x", {"name": "X"}),
    ("DELETE", "/api/v1/admin/plans/pro", None),
    ("GET", "/api/v1/admin/users", None),
    ("POST", "/api/v1/admin/users/u1/disable", None),
    ("GET", "/api/v1/admin/llmops/summary", None),
    ("GET", "/api/v1/admin/llmops/timeseries", None),
    ("GET", "/api/v1/admin/llmops/breakdown", None),
    ("GET", "/api/v1/admin/llmops/failures", None),
    ("GET", "/api/v1/admin/llmops/quota", None),
    ("GET", "/api/v1/admin/llmops/prices", None),
    ("PUT", "/api/v1/admin/llmops/prices",
     {"provider": "a", "model": "b", "input_per_mtok": 1, "output_per_mtok": 1}),
]


# ── authorization ─────────────────────────────────────────────────────────────
async def test_anonymous_callers_are_401_on_every_admin_route(client):
    for method, path, body in ADMIN_ROUTES:
        r = await client.request(method, path, json=body)
        assert r.status_code == 401, f"{method} {path}"


async def test_firm_users_are_403_on_every_admin_route(client, auth_headers):
    for who in ("owner", "someone"):
        h = auth_headers(who, roles=["user", "admin"])  # even a role named 'admin'
        for method, path, body in ADMIN_ROUTES:
            r = await client.request(method, path, json=body, headers=h)
            assert r.status_code == 403, f"{method} {path} as {who}"


# ── firms ─────────────────────────────────────────────────────────────────────
async def test_create_firm_sets_up_subscription_and_invites_the_owner(client, admin, plans, sent):
    r = await client.post("/api/v1/admin/firms", headers=admin, json={
        "name": "Nair & Co", "plan_code": "pro", "seats": 8, "owner_email": "Priya@NairCo.test",
        "invoice_ref": "INV-001", "period_end": (datetime.now(timezone.utc)
                                                  + timedelta(days=365)).isoformat(),
    })
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Nair & Co" and body["slug"].startswith("nair-co")
    assert body["plan"] == "pro" and body["subscription_status"] == "active"
    assert body["seats"] == {"used": 0, "pending": 1, "limit": 8}
    assert body["owner_invite_url"].startswith("http://localhost:3000/invite/")
    assert sent[0]["to"] == "priya@nairco.test" and sent[0]["role"] == "owner"


async def test_the_invited_owner_can_join_and_work(client, admin, plans, sent, auth_headers):
    r = await client.post("/api/v1/admin/firms", headers=admin, json={
        "name": "Nair & Co", "plan_code": "pro", "owner_email": "priya@example.test"})
    token = r.json()["owner_invite_url"].rsplit("/", 1)[1]
    priya = auth_headers("priya", provision=False)
    assert (await client.post("/api/v1/invites/accept", json={"token": token},
                              headers=priya)).json()["role"] == "owner"
    made = await client.post("/api/v1/cases/", headers=priya,
                             json={"title": "First matter", "country": "India"})
    assert made.status_code == 201


async def test_unknown_plan_and_bad_status_are_rejected(client, admin, plans, sent):
    base = {"name": "Nair & Co", "owner_email": "p@example.test"}
    assert (await client.post("/api/v1/admin/firms", headers=admin,
                              json={**base, "plan_code": "nope"})).status_code == 404
    assert (await client.post("/api/v1/admin/firms", headers=admin,
                              json={**base, "plan_code": "pro", "status": "free"})).status_code == 422


async def test_list_search_and_detail(client, admin, seed):
    a = seed.org("Alpha Legal")
    seed.member(a, "a-owner", "owner")
    seed.org("Beta Chambers")
    listing = (await client.get("/api/v1/admin/firms", headers=admin)).json()
    assert listing["total"] == 2
    found = (await client.get("/api/v1/admin/firms", params={"q": "alpha"}, headers=admin)).json()
    assert [f["name"] for f in found["items"]] == ["Alpha Legal"]
    assert found["items"][0]["seats"]["used"] == 1

    detail = (await client.get(f"/api/v1/admin/firms/{a}", headers=admin)).json()
    assert detail["members"][0]["email"] == "a-owner@example.test"
    assert detail["plan_detail"]["code"] == "pro" and detail["counts"] == {
        "cases": 0, "simulations": 0, "evidence": 0}


async def test_firm_detail_exposes_counts_but_never_case_content(client, admin, seed):
    org = seed.org("Secretive LLP")
    seed.member(org, "lawyer", "owner")
    case = seed.case("lawyer", org=org, title="State v. TOP-SECRET-TITLE",
                     description="privileged strategy notes")
    sim = seed.simulation(case, "lawyer")
    seed.turn(sim, seed.agent(sim), content="confidential testimony")
    seed.evidence(case, "lawyer")

    detail = (await client.get(f"/api/v1/admin/firms/{org}", headers=admin)).json()
    assert detail["counts"] == {"cases": 1, "simulations": 1, "evidence": 1}
    blob = json.dumps(detail, default=str)
    for secret in ("TOP-SECRET-TITLE", "privileged strategy", "confidential testimony"):
        assert secret not in blob

    # and no admin route returns a case, simulation, evidence or turn
    for path in (f"/api/v1/cases/{case}", f"/api/v1/simulations/{sim}",
                 f"/api/v1/simulations/{sim}/turns"):
        assert (await client.get(path, headers=admin)).status_code in (403, 404)


async def test_suspending_a_firm_locks_its_members_out(client, admin, seed, auth_headers):
    org = seed.org("Doomed LLP")
    seed.member(org, "worker", "owner")
    worker = auth_headers("worker", provision=False)
    assert (await client.get("/api/v1/cases/", headers=worker)).status_code == 200
    r = await client.patch(f"/api/v1/admin/firms/{org}", json={"status": "suspended"}, headers=admin)
    assert r.status_code == 200 and r.json()["status"] == "suspended"
    assert (await client.get("/api/v1/cases/", headers=worker)).json()["error"] == "ORG_SUSPENDED"
    await client.patch(f"/api/v1/admin/firms/{org}", json={"status": "active"}, headers=admin)
    assert (await client.get("/api/v1/cases/", headers=worker)).status_code == 200
    assert (await client.patch(f"/api/v1/admin/firms/{org}", json={"status": "weird"},
                               headers=admin)).status_code == 422


async def test_subscription_changes_take_effect_immediately(client, admin, seed, auth_headers):
    org = seed.org("Billing LLP")
    seed.member(org, "worker", "owner")
    worker = auth_headers("worker", provision=False)
    ok = {"title": "Matter", "country": "India"}
    assert (await client.post("/api/v1/cases/", json=ok, headers=worker)).status_code == 201

    put = lambda **kw: client.put(f"/api/v1/admin/firms/{org}/subscription", headers=admin,  # noqa: E731
                                  json={"plan_code": "pro", **kw})
    assert (await put(status="past_due", seats=5, invoice_ref="INV-7")).status_code == 200
    assert (await client.post("/api/v1/cases/", json=ok, headers=worker)).status_code == 402
    assert (await put(status="active", seats=5)).status_code == 200
    assert (await client.post("/api/v1/cases/", json=ok, headers=worker)).status_code == 201
    assert (await put(plan_code="missing")).status_code in (404, 422)


async def test_firm_without_a_subscription_row_can_be_given_one(client, admin, seed):
    org = seed.org("Fresh LLP")
    conn = __import__("sqlite3").connect(seed.path)
    conn.execute("DELETE FROM subscriptions WHERE org_id = ?", [org])
    conn.commit()
    conn.close()
    r = await client.put(f"/api/v1/admin/firms/{org}/subscription", headers=admin,
                         json={"plan_code": "pro", "seats": 4, "status": "trialing"})
    assert r.status_code == 200 and r.json()["subscription_status"] == "trialing"


async def test_owner_invite_for_an_existing_firm(client, admin, seed, sent):
    org = seed.org("Existing LLP")
    r = await client.post(f"/api/v1/admin/firms/{org}/owner-invite", headers=admin,
                          json={"email": "new.owner@example.test"})
    assert r.status_code == 201 and r.json()["invite_url"]
    assert sent[0]["role"] == "owner"


# ── plans ─────────────────────────────────────────────────────────────────────
async def test_plan_crud_and_retire_guard(client, admin, seed):
    seed.org("On Pro")  # puts a firm on 'pro'
    made = await client.put("/api/v1/admin/plans/boutique", headers=admin, json={
        "name": "Boutique", "seat_limit": 12, "monthly_tokens": 5_000_000})
    assert made.status_code == 200 and made.json()["seat_limit"] == 12
    edited = await client.put("/api/v1/admin/plans/boutique", headers=admin, json={
        "name": "Boutique", "seat_limit": 15})
    assert edited.json()["seat_limit"] == 15
    plans = {p["code"]: p for p in (await client.get("/api/v1/admin/plans", headers=admin)).json()}
    assert plans["pro"]["firms"] == 1 and plans["boutique"]["firms"] == 0

    assert (await client.delete("/api/v1/admin/plans/pro", headers=admin)).status_code == 409
    assert (await client.delete("/api/v1/admin/plans/boutique", headers=admin)).status_code == 204
    plans = {p["code"]: p for p in (await client.get("/api/v1/admin/plans", headers=admin)).json()}
    assert plans["boutique"]["is_active"] is False


async def test_a_retired_plan_cannot_be_assigned(client, admin, seed, plans, sent):
    org = seed.org("Legacy LLP", plan="old")
    assert (await client.put(f"/api/v1/admin/firms/{org}/subscription", headers=admin,
                             json={"plan_code": "pro"})).status_code == 200  # move off 'old'
    assert (await client.delete("/api/v1/admin/plans/old", headers=admin)).status_code == 204
    again = await client.put(f"/api/v1/admin/firms/{org}/subscription", headers=admin,
                             json={"plan_code": "old"})
    assert again.status_code == 409 and "retired" in again.json()["message"]
    created = await client.post("/api/v1/admin/firms", headers=admin, json={
        "name": "New LLP", "plan_code": "old", "owner_email": "o@example.test"})
    assert created.status_code == 409


# ── users ─────────────────────────────────────────────────────────────────────
async def test_user_directory_groups_firms_per_person(client, admin, seed):
    a, b = seed.org("Alpha"), seed.org("Beta")
    seed.member(a, "amy", "owner")
    seed.member(b, "amy", "attorney")
    seed.member(b, "bob", "attorney")
    users = (await client.get("/api/v1/admin/users", headers=admin)).json()
    assert users["total"] == 2
    amy = next(u for u in users["items"] if u["user_id"] == "amy")
    assert {(f["name"], f["role"]) for f in amy["firms"]} == {("Alpha", "owner"), ("Beta", "attorney")}
    found = (await client.get("/api/v1/admin/users", params={"q": "bob"}, headers=admin)).json()
    assert [u["user_id"] for u in found["items"]] == ["bob"]


def keycloak_double(monkeypatch, calls):
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, request.url.path))
        path = request.url.path
        if path.endswith("/openid-connect/token"):
            return httpx.Response(200, json={"access_token": "kc-token"})
        if request.headers.get("authorization") != "Bearer kc-token":
            return httpx.Response(401)
        if path.endswith("/users/u-404") and request.method == "GET":
            return httpx.Response(404)
        if request.method == "GET":
            return httpx.Response(200, json={"id": "u1", "username": "x", "enabled": True})
        return httpx.Response(204)

    original = httpx.AsyncClient

    def factory(*a, **kw):
        kw["transport"] = httpx.MockTransport(handler)
        return original(*a, **kw)

    monkeypatch.setattr(httpx, "AsyncClient", factory)


async def test_disable_and_enable_users_through_keycloak(client, admin, monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("KEYCLOAK_ADMIN_USER", "kcadmin")
    monkeypatch.setenv("KEYCLOAK_ADMIN_PASS", "pw")
    get_settings.cache_clear()
    calls: list[tuple[str, str]] = []
    keycloak_double(monkeypatch, calls)

    assert (await client.post("/api/v1/admin/users/u1/disable", headers=admin)).status_code == 204
    assert ("PUT", "/admin/realms/nyayrithm/users/u1") in calls
    assert ("POST", "/admin/realms/nyayrithm/users/u1/logout") in calls  # live sessions ended
    calls.clear()
    assert (await client.post("/api/v1/admin/users/u1/enable", headers=admin)).status_code == 204
    assert ("POST", "/admin/realms/nyayrithm/users/u1/logout") not in calls
    assert (await client.post("/api/v1/admin/users/u-404/disable", headers=admin)).status_code == 404

    events = (await client.get("/api/v1/admin/events", headers=admin)).json()["items"]
    assert [e["action"] for e in events][:2] == ["user.enabled", "user.disabled"]


async def test_keycloak_not_configured_is_a_clear_503(client, admin, monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("KEYCLOAK_ADMIN_USER", "")
    monkeypatch.setenv("KEYCLOAK_ADMIN_PASS", "")
    get_settings.cache_clear()
    r = await client.post("/api/v1/admin/users/u1/disable", headers=admin)
    assert r.status_code == 503 and "not configured" in r.json()["message"]


# ── activity log, overview ────────────────────────────────────────────────────
async def test_every_mutation_is_logged_with_the_acting_admin(client, admin, plans, sent):
    await client.post("/api/v1/admin/firms", headers=admin, json={
        "name": "Logged LLP", "plan_code": "pro", "owner_email": "o@example.test"})
    await client.put("/api/v1/admin/plans/extra", headers=admin, json={"name": "Extra"})
    events = (await client.get("/api/v1/admin/events", headers=admin)).json()
    assert {e["action"] for e in events["items"]} == {"firm.created", "plan.created"}
    assert all(e["actor"] == "root@example.test" for e in events["items"])
    only = (await client.get("/api/v1/admin/events", params={"action": "plan.created"},
                             headers=admin)).json()
    assert only["total"] == 1


async def test_overview_totals(client, admin, seed):
    a = seed.org("A")
    seed.member(a, "u1", "owner")
    seed.org("B", status="suspended", sub_status="past_due")
    body = (await client.get("/api/v1/admin/overview", headers=admin)).json()
    assert body["firms"] == {"total": 2, "active": 1, "suspended": 1}
    assert body["users"] == 1 and body["subscriptions"]["active"] == 1
    assert body["subscriptions"]["past_due"] == 1


async def test_system_health_reports_each_component(client, admin, monkeypatch):
    # Redis and Celery are made deterministically unreachable (a developer's own stack may be
    # listening on localhost); the HTTP services answer.
    def no_redis(*a, **k):
        raise ConnectionError("redis down")

    monkeypatch.setattr("redis.asyncio.from_url", no_redis)
    monkeypatch.setattr("app.tasks.celery_app.celery_app.control.inspect",
                        lambda **kw: type("I", (), {"ping": staticmethod(lambda: None)})())
    monkeypatch.setattr("app.services.system_health._http_ok", lambda url: _ok())
    body = (await client.get("/api/v1/admin/system", headers=admin)).json()
    names = [c["name"] for c in body["checks"]]
    assert names == ["PostgreSQL", "MongoDB", "Redis", "Qdrant", "Keycloak", "Celery workers",
                     "Legal packs"]
    by = {c["name"]: c for c in body["checks"]}
    assert by["PostgreSQL"]["ok"] is True and by["Legal packs"]["ok"] is True
    assert "IN" in by["Legal packs"]["detail"]
    assert by["Redis"]["ok"] is False and by["Celery workers"]["ok"] is False
    assert body["ok"] is False


async def _ok() -> str:
    return "HTTP 200"


# ── LLMOps ────────────────────────────────────────────────────────────────────
def usage(org, *, minutes_ago=5, **kw):
    doc = {
        "id": f"u-{minutes_ago}-{kw.get('model')}-{kw.get('agent_role')}-{org}", "kind": "chat",
        "provider": "gemini", "model": "gemini-flash-lite-latest", "org_id": org, "user_id": "u",
        "simulation_id": "s", "agent_role": "judge", "input_tokens": 1000, "output_tokens": 200,
        "estimated": False, "cost_usd": 0.0002, "priced": True, "latency_ms": 800, "ttft_ms": 300,
        "status": "ok", "error_code": None,
        "created_at": datetime.now(timezone.utc) - timedelta(minutes=minutes_ago), **kw,
    }
    tests.conftest._SYNC_MONGO["llm_usage"].insert_one(doc)


@pytest.fixture
def traffic(seed):
    a, b = seed.org("Alpha LLP"), seed.org("Beta LLP")
    for i in range(10):
        usage(a, minutes_ago=i + 1, latency_ms=100 * (i + 1), agent_role="judge",
              id=f"a{i}")
    usage(a, minutes_ago=30, provider="openai", model="gpt-4o-mini", cost_usd=0.01,
          agent_role="prosecutor", id="a-openai")
    usage(b, minutes_ago=40, status="error", error_code="TimeoutError", input_tokens=50,
          output_tokens=0, cost_usd=0.0, agent_role="witness", id="b-err")
    usage(b, minutes_ago=60 * 24 * 3, estimated=True, priced=False, cost_usd=0.0,
          kind="vision", model="mystery", id="b-old")
    usage(a, minutes_ago=60 * 24 * 60, id="a-ancient")  # outside a 30-day window
    return a, b


async def test_summary_totals_percentiles_and_flags(client, admin, traffic):
    s = (await client.get("/api/v1/admin/llmops/summary", params={"days": 30}, headers=admin)).json()
    assert s["requests"] == 13 and s["errors"] == 1
    assert s["error_rate"] == pytest.approx(1 / 13, abs=1e-3)
    assert s["input_tokens"] == 11 * 1000 + 50 + 1000 and s["tokens"] == s["input_tokens"] + s["output_tokens"]
    assert s["cost_usd"] == pytest.approx(10 * 0.0002 + 0.01 + 0.0002 * 0 + 0.0)
    assert s["latency_ms"]["p50"] is not None and s["latency_ms"]["p95"] >= s["latency_ms"]["p50"]
    assert s["estimated_share"] == pytest.approx(1 / 13, abs=1e-3) and s["unpriced_requests"] == 1
    assert "estimates" in s["note"]
    wide = (await client.get("/api/v1/admin/llmops/summary", params={"days": 90}, headers=admin)).json()
    assert wide["requests"] == 14


async def test_summary_can_be_scoped_to_one_firm(client, admin, traffic):
    a, b = traffic
    sa = (await client.get("/api/v1/admin/llmops/summary", params={"org_id": a}, headers=admin)).json()
    sb = (await client.get("/api/v1/admin/llmops/summary", params={"org_id": b}, headers=admin)).json()
    assert (sa["requests"], sb["requests"]) == (11, 2) and sb["errors"] == 1


async def test_timeseries_buckets_by_day_and_hour(client, admin, traffic):
    days = (await client.get("/api/v1/admin/llmops/timeseries", params={"days": 30},
                             headers=admin)).json()
    assert sum(d["requests"] for d in days) == 13
    assert [d["t"] for d in days] == sorted(d["t"] for d in days)
    hours = (await client.get("/api/v1/admin/llmops/timeseries",
                              params={"days": 1, "bucket": "hour"}, headers=admin)).json()
    assert sum(h["requests"] for h in hours) == 12 and "T" in hours[0]["t"]
    assert (await client.get("/api/v1/admin/llmops/timeseries", params={"bucket": "week"},
                             headers=admin)).status_code == 422


@pytest.mark.parametrize("by,expected_keys", [
    ("provider", {"gemini", "openai"}),
    ("role", {"judge", "prosecutor", "witness", "(none)"}),
    ("kind", {"chat", "vision"}),
])
async def test_breakdowns(client, admin, traffic, by, expected_keys):
    rows = (await client.get("/api/v1/admin/llmops/breakdown", params={"by": by, "days": 30},
                             headers=admin)).json()
    assert {r["key"] for r in rows} <= expected_keys | {"(none)"}
    assert sum(r["requests"] for r in rows) == 13
    costs = [r["cost_usd"] for r in rows]
    assert costs == sorted(costs, reverse=True)


async def test_breakdown_by_model_and_firm(client, admin, traffic):
    rows = (await client.get("/api/v1/admin/llmops/breakdown", params={"by": "model", "days": 30},
                             headers=admin)).json()
    assert rows[0]["key"] == "openai/gpt-4o-mini"  # the dearest model first
    firms = (await client.get("/api/v1/admin/llmops/breakdown", params={"by": "firm", "days": 30},
                              headers=admin)).json()
    assert {r["key"] for r in firms} == {"Alpha LLP", "Beta LLP"}
    beta = next(r for r in firms if r["key"] == "Beta LLP")
    assert beta["errors"] == 1 and beta["error_rate"] == 0.5


async def test_failures_list_names_the_firm_and_error(client, admin, traffic):
    rows = (await client.get("/api/v1/admin/llmops/failures", headers=admin)).json()
    assert len(rows) == 1
    assert rows[0]["error_code"] == "TimeoutError" and rows[0]["firm"] == "Beta LLP"
    assert "prompt" not in json.dumps(rows) and "content" not in rows[0]


async def test_quota_utilisation_is_ranked(client, admin, seed):
    from app.services.entitlements import current_period

    hot = seed.org("Hot LLP", plan="small", plan_limits={"monthly_tokens": 1000})
    seed.org("Cold LLP", plan="big", plan_limits={"monthly_tokens": 1_000_000})
    conn = __import__("sqlite3").connect(seed.path)
    conn.execute("INSERT INTO usage_counters (id, org_id, period, tokens, simulations) "
                 "VALUES ('c1', ?, ?, 900, 3)", [hot, current_period()])
    conn.commit()
    conn.close()
    rows = (await client.get("/api/v1/admin/llmops/quota", headers=admin)).json()
    assert rows[0]["name"] == "Hot LLP" and rows[0]["token_utilisation"] == 0.9
    assert rows[0]["simulations"] == 3 and rows[1]["tokens"] == 0


async def test_price_overrides_roundtrip_and_change_cost_estimates(client, admin):
    prices = (await client.get("/api/v1/admin/llmops/prices", headers=admin)).json()
    assert prices["overrides"] == [] and any(p["model"] == "gpt-4o-mini" for p in prices["defaults"])
    body = {"provider": "openai", "model": "gpt-4o-mini", "input_per_mtok": 1.0, "output_per_mtok": 2.0}
    assert (await client.put("/api/v1/admin/llmops/prices", json=body, headers=admin)).status_code == 204
    body["input_per_mtok"] = 3.0
    assert (await client.put("/api/v1/admin/llmops/prices", json=body, headers=admin)).status_code == 204
    prices = (await client.get("/api/v1/admin/llmops/prices", headers=admin)).json()
    assert [(o["model"], o["input_per_mtok"]) for o in prices["overrides"]] == [("gpt-4o-mini", 3.0)]
    assert (await client.put("/api/v1/admin/llmops/prices", headers=admin,
                             json={**body, "input_per_mtok": -1})).status_code == 422

    assert (await client.delete("/api/v1/admin/llmops/prices/openai/gpt-4o-mini",
                                headers=admin)).status_code == 204
    assert (await client.get("/api/v1/admin/llmops/prices", headers=admin)).json()["overrides"] == []


# ── granting the operator role (make admin-user) ──────────────────────────────
async def test_grant_platform_admin_by_email(monkeypatch):
    from app.config import get_settings
    from app.core.exceptions import NotFoundError
    from app.services.keycloak_admin import KeycloakAdmin

    monkeypatch.setenv("KEYCLOAK_ADMIN_USER", "kcadmin")
    monkeypatch.setenv("KEYCLOAK_ADMIN_PASS", "pw")
    get_settings.cache_clear()
    seen: list[tuple[str, str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        body = json.loads(request.content) if request.content and request.method == "POST" \
            and "json" in request.headers.get("content-type", "") else None
        seen.append((request.method, path, body))
        if path.endswith("/openid-connect/token"):
            return httpx.Response(200, json={"access_token": "t"})
        if path.endswith("/users") and request.url.params.get("email") == "ops@example.test":
            return httpx.Response(200, json=[{"id": "user-9"}])
        if path.endswith("/users"):
            return httpx.Response(200, json=[])
        if path.endswith("/roles/platform_admin"):
            return httpx.Response(200, json={"id": "r1", "name": "platform_admin"})
        return httpx.Response(204)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    kc = KeycloakAdmin(client)
    assert await kc.grant_role_by_email("ops@example.test") == "user-9"
    assert ("POST", "/admin/realms/nyayrithm/users/user-9/role-mappings/realm",
            [{"id": "r1", "name": "platform_admin"}]) in seen
    with pytest.raises(NotFoundError):
        await kc.grant_role_by_email("ghost@example.test")
