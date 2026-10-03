from __future__ import annotations

"""Firm tenancy: who sees which case, roles, sharing and member management."""

import pytest


@pytest.fixture
def firm(seed):
    """One firm with an owner, an admin and two attorneys, plus an unrelated firm."""
    org = seed.org("Acme LLP", seats=10)
    for uid, role in (("owner", "owner"), ("boss", "admin"), ("amy", "attorney"), ("raj", "attorney")):
        seed.member(org, uid, role)
    return org


async def test_attorney_sees_only_own_and_shared_cases(client, seed, firm, auth_headers):
    mine = seed.case("amy", org=firm, title="Amy's case")
    theirs = seed.case("raj", org=firm, title="Raj's case")
    h = auth_headers("amy", provision=False)

    listing = (await client.get("/api/v1/cases/", headers=h)).json()
    assert [c["id"] for c in listing["items"]] == [mine] and listing["total"] == 1
    assert (await client.get(f"/api/v1/cases/{mine}", headers=h)).status_code == 200
    assert (await client.get(f"/api/v1/cases/{theirs}", headers=h)).status_code == 404


async def test_owner_and_admin_see_every_case_in_the_firm(client, seed, firm, auth_headers):
    a = seed.case("amy", org=firm)
    b = seed.case("raj", org=firm)
    for uid in ("owner", "boss"):
        h = auth_headers(uid, provision=False)
        ids = {c["id"] for c in (await client.get("/api/v1/cases/", headers=h)).json()["items"]}
        assert ids == {a, b}
        assert (await client.get(f"/api/v1/cases/{a}", headers=h)).status_code == 200


async def test_sharing_a_case_gives_the_attorney_access_to_everything_under_it(
    client, seed, firm, auth_headers
):
    case = seed.case("amy", org=firm)
    sim = seed.simulation(case, "amy")
    agent = seed.agent(sim)
    seed.turn(sim, agent)
    ev = seed.evidence(case, "amy")
    raj = auth_headers("raj", provision=False)
    paths = (f"/api/v1/cases/{case}", f"/api/v1/simulations/{sim}",
             f"/api/v1/simulations/{sim}/turns", f"/api/v1/cases/{case}/evidence/{ev}")
    for p in paths:
        assert (await client.get(p, headers=raj)).status_code == 404

    r = await client.post(f"/api/v1/cases/{case}/members", json={"user_id": "raj"},
                          headers=auth_headers("amy", provision=False))
    assert r.status_code == 201
    for p in paths:
        assert (await client.get(p, headers=raj)).status_code == 200, p
    assert [c["id"] for c in (await client.get("/api/v1/cases/", headers=raj)).json()["items"]] == [case]

    # sharing is not management: raj still cannot delete or re-share it
    assert (await client.delete(f"/api/v1/cases/{case}", headers=raj)).status_code == 403
    assert (await client.post(f"/api/v1/cases/{case}/members", json={"user_id": "owner"},
                              headers=raj)).status_code == 403


async def test_unshare_removes_access(client, seed, firm, auth_headers):
    case = seed.case("amy", org=firm)
    amy = auth_headers("amy", provision=False)
    await client.post(f"/api/v1/cases/{case}/members", json={"user_id": "raj"}, headers=amy)
    assert (await client.delete(f"/api/v1/cases/{case}/members/raj", headers=amy)).status_code == 204
    assert (await client.get(f"/api/v1/cases/{case}",
                             headers=auth_headers("raj", provision=False))).status_code == 404


async def test_cannot_share_with_someone_outside_the_firm(client, seed, firm, auth_headers):
    case = seed.case("amy", org=firm)
    seed.ensure_user("stranger")
    r = await client.post(f"/api/v1/cases/{case}/members", json={"user_id": "stranger"},
                          headers=auth_headers("amy", provision=False))
    assert r.status_code == 404


async def test_sharing_twice_is_a_conflict(client, seed, firm, auth_headers):
    case = seed.case("amy", org=firm)
    amy = auth_headers("amy", provision=False)
    await client.post(f"/api/v1/cases/{case}/members", json={"user_id": "raj"}, headers=amy)
    assert (await client.post(f"/api/v1/cases/{case}/members", json={"user_id": "raj"},
                              headers=amy)).status_code == 409


async def test_firm_admin_can_delete_an_attorneys_case_but_a_peer_cannot(
    client, seed, firm, auth_headers
):
    case = seed.case("amy", org=firm)
    assert (await client.delete(f"/api/v1/cases/{case}",
                                headers=auth_headers("raj", provision=False))).status_code == 404
    assert (await client.delete(f"/api/v1/cases/{case}",
                                headers=auth_headers("boss", provision=False))).status_code == 204


async def test_new_cases_belong_to_the_callers_firm(client, firm, auth_headers):
    r = await client.post("/api/v1/cases/", headers=auth_headers("amy", provision=False),
                          json={"title": "New matter", "country": "India"})
    assert r.status_code == 201
    owner_view = (await client.get("/api/v1/cases/", headers=auth_headers("owner", provision=False))).json()
    assert [c["title"] for c in owner_view["items"]] == ["New matter"]


async def test_other_firms_never_see_this_firms_data(client, seed, firm, auth_headers):
    case = seed.case("amy", org=firm)
    sim = seed.simulation(case, "amy")
    outsider = auth_headers("outsider")  # own firm
    for p in (f"/api/v1/cases/{case}", f"/api/v1/simulations/{sim}"):
        assert (await client.get(p, headers=outsider)).status_code == 404
    assert (await client.get("/api/v1/cases/", headers=outsider)).json()["total"] == 0


# ── acting for a firm ─────────────────────────────────────────────────────────
async def test_user_without_a_firm_gets_a_clear_403(client, auth_headers):
    r = await client.get("/api/v1/cases/", headers=auth_headers("nobody", provision=False))
    assert r.status_code == 403 and r.json()["error"] == "NO_ORGANIZATION"


async def test_x_org_id_selects_between_firms_and_rejects_foreign_ones(
    client, seed, auth_headers
):
    first, second = seed.org("First"), seed.org("Second")
    seed.member(first, "dual", "owner")
    seed.member(second, "dual", "attorney")
    case = seed.case("dual", org=second, title="In second")

    default = (await client.get("/api/v1/cases/", headers=auth_headers("dual", provision=False))).json()
    assert default["total"] == 0  # the oldest membership is the default firm
    chosen = (await client.get("/api/v1/cases/",
                               headers=auth_headers("dual", provision=False, org=second))).json()
    assert [c["id"] for c in chosen["items"]] == [case]
    other = seed.org("Third")
    r = await client.get("/api/v1/cases/", headers=auth_headers("dual", provision=False, org=other))
    assert r.status_code == 403


async def test_suspended_firm_is_locked_out(client, seed, auth_headers):
    org = seed.org("Frozen", status="suspended")
    seed.member(org, "frozen-user", "owner")
    r = await client.get("/api/v1/cases/", headers=auth_headers("frozen-user", provision=False))
    assert r.status_code == 403 and r.json()["error"] == "ORG_SUSPENDED"


async def test_removed_members_lose_access(client, seed, firm, auth_headers):
    case = seed.case("amy", org=firm)
    owner = auth_headers("owner", provision=False)
    assert (await client.delete(f"/api/v1/orgs/{firm}/members/amy", headers=owner)).status_code == 204
    r = await client.get(f"/api/v1/cases/{case}", headers=auth_headers("amy", provision=False))
    assert r.status_code == 403  # no longer in any firm


# ── member management ─────────────────────────────────────────────────────────
async def test_members_list_and_firms_me(client, firm, auth_headers):
    h = auth_headers("amy", provision=False)
    members = (await client.get(f"/api/v1/orgs/{firm}/members", headers=h)).json()
    assert {m["user_id"]: m["role"] for m in members} == {
        "owner": "owner", "boss": "admin", "amy": "attorney", "raj": "attorney"}
    me = (await client.get("/api/v1/orgs/me", headers=h)).json()
    assert [(f["name"], f["role"]) for f in me["firms"]] == [("Acme LLP", "attorney")]


async def test_non_members_cannot_see_a_firms_members(client, firm, auth_headers):
    assert (await client.get(f"/api/v1/orgs/{firm}/members",
                             headers=auth_headers("outsider"))).status_code == 404


async def test_role_changes_follow_the_hierarchy(client, firm, auth_headers):
    owner, boss, amy = (auth_headers(u, provision=False) for u in ("owner", "boss", "amy"))
    # attorneys cannot manage roles
    assert (await client.patch(f"/api/v1/orgs/{firm}/members/raj", json={"role": "admin"},
                               headers=amy)).status_code == 403
    # an admin can promote an attorney to admin, but not make or touch owners
    assert (await client.patch(f"/api/v1/orgs/{firm}/members/raj", json={"role": "admin"},
                               headers=boss)).status_code == 200
    assert (await client.patch(f"/api/v1/orgs/{firm}/members/amy", json={"role": "owner"},
                               headers=boss)).status_code == 403
    assert (await client.patch(f"/api/v1/orgs/{firm}/members/owner", json={"role": "attorney"},
                               headers=boss)).status_code == 403
    # an owner can
    assert (await client.patch(f"/api/v1/orgs/{firm}/members/amy", json={"role": "owner"},
                               headers=owner)).status_code == 200
    assert (await client.patch(f"/api/v1/orgs/{firm}/members/amy", json={"role": "wizard"},
                               headers=owner)).status_code == 422


async def test_a_firm_always_keeps_an_owner(client, firm, auth_headers):
    owner = auth_headers("owner", provision=False)
    r = await client.patch(f"/api/v1/orgs/{firm}/members/owner", json={"role": "admin"}, headers=owner)
    assert r.status_code == 409
    assert (await client.delete(f"/api/v1/orgs/{firm}/members/owner", headers=owner)).status_code == 409


async def test_admins_can_only_remove_attorneys(client, firm, auth_headers):
    boss = auth_headers("boss", provision=False)
    assert (await client.delete(f"/api/v1/orgs/{firm}/members/owner", headers=boss)).status_code == 403
    assert (await client.delete(f"/api/v1/orgs/{firm}/members/raj", headers=boss)).status_code == 204
    assert (await client.delete(f"/api/v1/orgs/{firm}/members/raj", headers=boss)).status_code == 404
