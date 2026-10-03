"""Every route must refuse another user's data, and refuse anonymous callers.

Resources the caller does not own look exactly like resources that do not exist (404), so
ids cannot be probed for existence.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

import pytest

from tests.conftest import Seeder


@dataclass
class World:
    case: str
    sim: str
    agent: str
    turn: str
    evidence: str


@pytest.fixture
def world(seed: Seeder) -> World:
    case = seed.case("user-a")
    sim = seed.simulation(case, "user-a")
    agent = seed.agent(sim)
    return World(
        case=case, sim=sim, agent=agent,
        turn=seed.turn(sim, agent), evidence=seed.evidence(case, "user-a"),
    )


def routes(w: World) -> list[tuple[str, str, dict]]:
    """(method, path, request kwargs) for every endpoint that touches a case's data."""
    new_id = str(uuid.uuid4())
    return [
        ("GET", f"/api/v1/cases/{w.case}", {}),
        ("PUT", f"/api/v1/cases/{w.case}", {"json": {"title": "hijacked"}}),
        ("DELETE", f"/api/v1/cases/{w.case}", {}),
        ("GET", f"/api/v1/cases/{w.case}/evidence/", {}),
        ("GET", f"/api/v1/cases/{w.case}/evidence/{w.evidence}", {}),
        ("DELETE", f"/api/v1/cases/{w.case}/evidence/{w.evidence}", {}),
        ("POST", f"/api/v1/cases/{w.case}/evidence/{w.evidence}/reindex", {}),
        ("POST", f"/api/v1/cases/{w.case}/search", {"json": {"query": "anything"}}),
        ("POST", f"/api/v1/cases/{w.case}/evidence/",
         {"files": {"file": ("a.txt", b"hello", "text/plain")}}),
        ("GET", f"/api/v1/cases/{w.case}/simulations/", {}),
        ("POST", f"/api/v1/cases/{w.case}/simulations/", {"json": {"title": "mine now"}}),
        ("GET", f"/api/v1/simulations/{w.sim}", {}),
        ("POST", f"/api/v1/simulations/{w.sim}/start", {}),
        ("POST", f"/api/v1/simulations/{w.sim}/pause", {}),
        ("POST", f"/api/v1/simulations/{w.sim}/stop", {}),
        ("POST", f"/api/v1/simulations/{w.sim}/clone", {}),
        ("DELETE", f"/api/v1/simulations/{w.sim}", {}),
        ("GET", f"/api/v1/simulations/{w.sim}/agents", {}),
        ("POST", f"/api/v1/simulations/{w.sim}/agents", {"json": {"role": "judge", "name": "J"}}),
        ("DELETE", f"/api/v1/simulations/{w.sim}/agents/{w.agent}", {}),
        ("GET", f"/api/v1/simulations/{w.sim}/graph", {}),
        ("GET", f"/api/v1/simulations/{w.sim}/turns", {}),
        ("PATCH", f"/api/v1/simulations/{w.sim}/turns/{w.turn}", {"json": {"content": "forged"}}),
        ("GET", f"/api/v1/simulations/{w.sim}/audit", {}),
        ("GET", f"/api/v1/simulations/{w.sim}/audit/verify", {}),
        ("GET", f"/api/v1/simulations/{w.sim}/procedure", {}),
        ("GET", f"/api/v1/agents/{w.agent}", {}),
        ("DELETE", f"/api/v1/agents/{w.agent}/memory", {}),
        ("POST", "/api/v1/legal/verify", {"json": {"text": "Section 103 BNS", "case_id": w.case}}),
        # ids that exist nowhere behave identically
        ("GET", f"/api/v1/cases/{new_id}", {}),
        ("GET", f"/api/v1/simulations/{new_id}", {}),
        ("GET", f"/api/v1/agents/{new_id}", {}),
    ]


def route_ids(w: World) -> list[str]:
    return [f"{m} {p.replace(w.case, '{case}').replace(w.sim, '{sim}')}" for m, p, _ in routes(w)]


async def test_anonymous_callers_get_401_everywhere(client, world):
    for method, path, kw in routes(world):
        r = await client.request(method, path, **kw)
        assert r.status_code == 401, f"{method} {path} -> {r.status_code}"
        assert r.headers["www-authenticate"] == "Bearer"


async def test_other_users_get_404_everywhere(client, world, auth_headers):
    headers = auth_headers("user-b")
    for method, path, kw in routes(world):
        r = await client.request(method, path, headers=headers, **kw)
        assert r.status_code == 404, f"{method} {path} -> {r.status_code}: {r.text}"


async def test_failed_attacks_leave_the_owners_data_untouched(client, world, auth_headers, seed):
    attacker = auth_headers("user-b")
    for method, path, kw in routes(world):
        await client.request(method, path, headers=attacker, **kw)

    owner = auth_headers("user-a")
    case = (await client.get(f"/api/v1/cases/{world.case}", headers=owner)).json()
    assert case["title"] == "State v. Test" and case["created_by"] == "user-a"
    assert (await client.get(f"/api/v1/simulations/{world.sim}", headers=owner)).status_code == 200
    assert (await client.get(f"/api/v1/agents/{world.agent}", headers=owner)).status_code == 200
    turns = (await client.get(f"/api/v1/simulations/{world.sim}/turns", headers=owner)).json()
    assert [t["content"] for t in turns["items"]] == ["Hello"]
    evidence = await client.get(f"/api/v1/cases/{world.case}/evidence/", headers=owner)
    assert evidence.json()["total"] == 1


async def test_owner_can_reach_every_read_endpoint(client, world, auth_headers):
    headers = auth_headers("user-a")
    for path in (
        f"/api/v1/cases/{world.case}",
        f"/api/v1/cases/{world.case}/evidence/",
        f"/api/v1/cases/{world.case}/evidence/{world.evidence}",
        f"/api/v1/cases/{world.case}/simulations/",
        f"/api/v1/simulations/{world.sim}",
        f"/api/v1/simulations/{world.sim}/agents",
        f"/api/v1/simulations/{world.sim}/graph",
        f"/api/v1/simulations/{world.sim}/turns",
        f"/api/v1/simulations/{world.sim}/audit",
        f"/api/v1/simulations/{world.sim}/audit/verify",
        f"/api/v1/simulations/{world.sim}/procedure",
        f"/api/v1/agents/{world.agent}",
    ):
        r = await client.get(path, headers=headers)
        assert r.status_code == 200, f"{path} -> {r.status_code}: {r.text}"


async def test_lists_only_contain_the_callers_cases(client, seed, auth_headers):
    seed.case("user-a", title="A's case")
    seed.case("user-b", title="B's case")
    for user, title in (("user-a", "A's case"), ("user-b", "B's case")):
        body = (await client.get("/api/v1/cases/", headers=auth_headers(user))).json()
        assert [c["title"] for c in body["items"]] == [title] and body["total"] == 1


async def test_a_case_id_does_not_grant_access_through_another_case(client, seed, auth_headers):
    # User B owns a case and a simulation, and tries to read A's evidence through B's case.
    a_case = seed.case("user-a")
    a_evidence = seed.evidence(a_case, "user-a")
    b_case = seed.case("user-b")
    r = await client.get(
        f"/api/v1/cases/{b_case}/evidence/{a_evidence}", headers=auth_headers("user-b")
    )
    assert r.status_code == 404


async def test_a_simulation_cannot_be_reached_through_a_different_case_or_user(
    client, seed, auth_headers
):
    a_case = seed.case("user-a")
    a_sim = seed.simulation(a_case, "user-a")
    a_agent = seed.agent(a_sim)
    b_case = seed.case("user-b")
    b_sim = seed.simulation(b_case, "user-b")

    # B's own simulation does not unlock A's agent
    headers = auth_headers("user-b")
    r = await client.delete(f"/api/v1/simulations/{b_sim}/agents/{a_agent}", headers=headers)
    assert r.status_code == 404
    assert (await client.get(f"/api/v1/agents/{a_agent}", headers=auth_headers("user-a"))).status_code == 200


async def test_platform_admin_has_no_access_to_firm_data(client, world, auth_headers, seed):
    """The operator role grants nothing inside a firm: no admin cross-tenant reads."""
    # not in any firm -> no workspace at all
    nofirm = auth_headers("root", roles=["user", "platform_admin"], provision=False)
    assert (await client.get(f"/api/v1/cases/{world.case}", headers=nofirm)).status_code == 403
    admin = auth_headers("root", roles=["user", "platform_admin", "admin"])
    # even once in their own firm, someone else's case is invisible
    assert (await client.get(f"/api/v1/cases/{world.case}", headers=admin)).status_code == 404
    assert (await client.get("/api/v1/cases/", headers=admin)).json()["total"] == 0


async def test_forged_expired_and_foreign_tokens_are_rejected(client, world, keycloak):
    from tests.conftest import FakeKeycloak

    path = f"/api/v1/cases/{world.case}"
    expired = {"Authorization": f"Bearer {keycloak.token('user-a', expires_in=-600)}"}
    foreign = {"Authorization": f"Bearer {FakeKeycloak().token('user-a')}"}
    wrong_issuer = {"Authorization": f"Bearer {keycloak.token('user-a', issuer='http://evil/realms/x')}"}
    garbage = {"Authorization": "Bearer not.a.jwt"}
    for headers in (expired, foreign, wrong_issuer, garbage):
        assert (await client.get(path, headers=headers)).status_code == 401


async def test_health_and_disclaimer_are_public(client):
    assert (await client.get("/api/v1/health")).status_code == 200
    r = await client.get("/api/v1/legal/disclaimer")
    assert r.status_code == 200 and "not a court" in r.json()["disclaimer"]


async def test_dev_bypass_acts_as_the_dev_user_without_a_token(
    client, seed, monkeypatch, auth_headers
):
    from app.config import get_settings

    own = seed.case("00000000-0000-4000-8000-0000000000b1", title="Pre-auth data")
    seed.case("user-a", title="Someone else's")
    monkeypatch.setenv("AUTH_DEV_BYPASS", "true")
    get_settings.cache_clear()

    body = (await client.get("/api/v1/cases/")).json()
    assert [c["id"] for c in body["items"]] == [own]
    # ...but bypass never lets an anonymous caller into another user's case
    other = seed.case("user-a")
    assert (await client.get(f"/api/v1/cases/{other}")).status_code == 404
