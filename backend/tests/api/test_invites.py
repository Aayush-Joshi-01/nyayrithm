from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timedelta, timezone

import pytest


@pytest.fixture
def sent(monkeypatch):
    """Capture invite emails instead of queueing Celery tasks."""
    calls: list[dict] = []
    from app.tasks.notification_tasks import send_invite_email

    monkeypatch.setattr(send_invite_email, "delay", lambda **kw: calls.append(kw))
    return calls


def _members(seed, org):
    seed.member(org, "owner", "owner")
    seed.member(org, "boss", "admin")
    seed.member(org, "amy", "attorney")
    return org


@pytest.fixture
def firm(seed):
    return _members(seed, seed.org("Acme LLP", seats=10))


@pytest.fixture
def tight(seed):
    """A firm whose three seats are all taken."""
    return _members(seed, seed.org("Acme LLP", seats=3))


def token_from(url: str) -> str:
    return url.rsplit("/", 1)[1]


async def invite(client, auth_headers, firm, email="new@example.test", role="attorney", by="owner"):
    return await client.post(f"/api/v1/orgs/{firm}/invites", json={"email": email, "role": role},
                             headers=auth_headers(by, provision=False))


async def test_owner_invites_and_the_email_carries_a_working_link(client, firm, auth_headers, sent):
    r = await invite(client, auth_headers, firm, "New@Example.test")
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "new@example.test" and body["status"] == "pending"
    assert body["invite_url"].startswith("http://localhost:3000/invite/")
    assert len(sent) == 1
    assert sent[0]["to"] == "new@example.test" and sent[0]["org_name"] == "Acme LLP"
    assert sent[0]["url"] == body["invite_url"] and sent[0]["role"] == "attorney"


async def test_only_the_token_hash_is_stored(client, firm, auth_headers, sent, db_path):
    token = token_from((await invite(client, auth_headers, firm)).json()["invite_url"])
    conn = sqlite3.connect(db_path)
    (stored,) = conn.execute("SELECT token_hash FROM invites").fetchone()
    conn.close()
    assert stored == hashlib.sha256(token.encode()).hexdigest() and token not in stored


async def test_listing_never_exposes_the_link(client, firm, auth_headers, sent):
    await invite(client, auth_headers, firm)
    items = (await client.get(f"/api/v1/orgs/{firm}/invites",
                              headers=auth_headers("owner", provision=False))).json()
    assert len(items) == 1 and items[0]["invite_url"] is None


async def test_attorneys_cannot_invite_or_list(client, firm, auth_headers, sent):
    assert (await invite(client, auth_headers, firm, by="amy")).status_code == 403
    assert (await client.get(f"/api/v1/orgs/{firm}/invites",
                             headers=auth_headers("amy", provision=False))).status_code == 403
    assert sent == []


async def test_outsiders_cannot_invite_into_a_firm(client, firm, auth_headers, sent):
    assert (await invite(client, auth_headers, firm, by="outsider")).status_code == 404


async def test_only_owners_can_invite_owners(client, firm, auth_headers, sent):
    assert (await invite(client, auth_headers, firm, role="owner", by="boss")).status_code == 403
    assert (await invite(client, auth_headers, firm, role="owner", by="owner")).status_code == 201


@pytest.mark.parametrize("email,role,code", [("not-an-email", "attorney", 422),
                                             ("a@example.test", "wizard", 422)])
async def test_invalid_invites_are_rejected(client, firm, auth_headers, sent, email, role, code):
    assert (await invite(client, auth_headers, firm, email, role)).status_code == code


async def test_existing_member_cannot_be_invited(client, firm, auth_headers, sent):
    r = await invite(client, auth_headers, firm, "amy@example.test")
    assert r.status_code == 409


async def test_reinviting_replaces_the_earlier_invite(client, firm, auth_headers, sent):
    first = (await invite(client, auth_headers, firm)).json()
    second = (await invite(client, auth_headers, firm)).json()
    assert first["id"] != second["id"]
    pending = (await client.get(f"/api/v1/orgs/{firm}/invites",
                                headers=auth_headers("owner", provision=False))).json()
    assert [i["id"] for i in pending] == [second["id"]]
    old = await client.post("/api/v1/invites/accept", json={"token": token_from(first["invite_url"])},
                            headers=auth_headers("new"))
    assert old.status_code == 410


# ── accepting ─────────────────────────────────────────────────────────────────
async def accept(client, auth_headers, url, user="new"):
    return await client.post("/api/v1/invites/accept", json={"token": token_from(url)},
                             headers=auth_headers(user, provision=False))


async def test_invitee_accepts_and_joins_with_the_invited_role(client, seed, firm, auth_headers, sent):
    url = (await invite(client, auth_headers, firm, "new@example.test", "admin")).json()["invite_url"]
    r = await accept(client, auth_headers, url)
    assert r.status_code == 200 and r.json()["role"] == "admin" and r.json()["user_id"] == "new"

    # they now work inside the firm, and the invite is spent
    h = auth_headers("new", provision=False)
    assert (await client.get("/api/v1/cases/", headers=h)).status_code == 200
    assert (await client.get(f"/api/v1/orgs/{firm}/members", headers=h)).status_code == 200
    assert (await client.get(f"/api/v1/orgs/{firm}/invites",
                             headers=auth_headers("owner", provision=False))).json() == []


async def test_preview_works_before_sign_in_and_reveals_little(client, firm, auth_headers, sent):
    url = (await invite(client, auth_headers, firm)).json()["invite_url"]
    r = await client.get("/api/v1/invites/preview", params={"token": token_from(url)})
    assert r.status_code == 200
    assert set(r.json()) == {"org_name", "email", "role", "expires_at"}
    assert r.json()["org_name"] == "Acme LLP"
    assert (await client.get("/api/v1/invites/preview",
                             params={"token": "x" * 40})).status_code == 404


async def test_a_used_link_cannot_be_replayed(client, firm, auth_headers, sent):
    url = (await invite(client, auth_headers, firm)).json()["invite_url"]
    assert (await accept(client, auth_headers, url)).status_code == 200
    again = await accept(client, auth_headers, url)
    assert again.status_code == 410 and "already been used" in again.json()["message"]


async def test_someone_else_cannot_use_the_link(client, seed, firm, auth_headers, sent):
    url = (await invite(client, auth_headers, firm, "new@example.test")).json()["invite_url"]
    r = await accept(client, auth_headers, url, user="intruder")
    assert r.status_code == 403 and r.json()["error"] == "INVITE_EMAIL_MISMATCH"
    # and the real invitee is unaffected
    assert (await accept(client, auth_headers, url, user="new")).status_code == 200


async def test_expired_invites_are_refused(client, firm, auth_headers, sent, db_path):
    url = (await invite(client, auth_headers, firm)).json()["invite_url"]
    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE invites SET expires_at = ?",
                 [(datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()])
    conn.commit()
    conn.close()
    r = await accept(client, auth_headers, url)
    assert r.status_code == 410 and "expired" in r.json()["message"]
    assert (await client.get("/api/v1/invites/preview",
                             params={"token": token_from(url)})).status_code == 410


async def test_revoked_invites_are_refused(client, firm, auth_headers, sent):
    created = (await invite(client, auth_headers, firm)).json()
    owner = auth_headers("owner", provision=False)
    assert (await client.delete(f"/api/v1/orgs/{firm}/invites/{created['id']}",
                                headers=owner)).status_code == 204
    r = await accept(client, auth_headers, created["invite_url"])
    assert r.status_code == 410 and "withdrawn" in r.json()["message"]


async def test_resend_issues_a_fresh_link_and_kills_the_old_one(client, firm, auth_headers, sent):
    created = (await invite(client, auth_headers, firm)).json()
    r = await client.post(f"/api/v1/orgs/{firm}/invites/{created['id']}/resend",
                          headers=auth_headers("owner", provision=False))
    assert r.status_code == 200 and r.json()["invite_url"] != created["invite_url"]
    assert len(sent) == 2
    assert (await accept(client, auth_headers, created["invite_url"])).status_code == 404
    assert (await accept(client, auth_headers, r.json()["invite_url"])).status_code == 200


async def test_other_firms_cannot_touch_this_firms_invites(client, seed, firm, auth_headers, sent):
    created = (await invite(client, auth_headers, firm)).json()
    other = seed.org("Rival LLP")
    seed.member(other, "rival", "owner")
    h = auth_headers("rival", provision=False)
    path = f"/api/v1/orgs/{other}/invites/{created['id']}"
    assert (await client.delete(path, headers=h)).status_code == 404
    assert (await client.post(path + "/resend", headers=h)).status_code == 404


# ── seats ─────────────────────────────────────────────────────────────────────
async def test_pending_invites_hold_seats(client, tight, auth_headers, sent):
    # 3 seats, 3 members -> already full
    r = await invite(client, auth_headers, tight)
    assert r.status_code == 402 and r.json()["error"] == "SEAT_LIMIT"
    assert sent == []


async def test_a_freed_seat_can_be_reinvited_and_the_invite_holds_it(
    client, tight, auth_headers, sent
):
    owner = auth_headers("owner", provision=False)
    await client.delete(f"/api/v1/orgs/{tight}/members/amy", headers=owner)
    first = await invite(client, auth_headers, tight, "one@example.test")
    assert first.status_code == 201
    second = await invite(client, auth_headers, tight, "two@example.test")
    assert second.status_code == 402  # the first invite reserved the freed seat
    # accepting does not need a second seat
    assert (await accept(client, auth_headers, first.json()["invite_url"], user="one")).status_code == 200


async def test_seat_limit_is_rechecked_at_accept_time(client, seed, tight, auth_headers, sent, db_path):
    owner = auth_headers("owner", provision=False)
    await client.delete(f"/api/v1/orgs/{tight}/members/amy", headers=owner)
    url = (await invite(client, auth_headers, tight, "one@example.test")).json()["invite_url"]
    # someone is added directly while the invite is outstanding
    seed.member(tight, "sneaky", "attorney")
    r = await accept(client, auth_headers, url, user="one")
    assert r.status_code == 402


async def test_inactive_subscription_blocks_invites_and_accepts(client, seed, auth_headers, sent):
    org = seed.org("Lapsed", sub_status="cancelled")
    seed.member(org, "boss2", "owner")
    r = await client.post(f"/api/v1/orgs/{org}/invites", json={"email": "a@example.test"},
                          headers=auth_headers("boss2", provision=False))
    assert r.status_code == 402 and r.json()["error"] == "SUBSCRIPTION_INACTIVE"


async def test_accepting_into_a_second_firm_keeps_the_first(client, seed, firm, auth_headers, sent):
    other = seed.org("Other LLP")
    seed.member(other, "x-owner", "owner")
    seed.member(firm, "dual", "attorney")
    url = (await client.post(f"/api/v1/orgs/{other}/invites",
                             json={"email": "dual@example.test", "role": "attorney"},
                             headers=auth_headers("x-owner", provision=False))).json()["invite_url"]
    assert (await accept(client, auth_headers, url, user="dual")).status_code == 200
    firms = (await client.get("/api/v1/orgs/me", headers=auth_headers("dual", provision=False))).json()
    assert {f["name"] for f in firms["firms"]} == {"Acme LLP", "Other LLP"}


async def test_accept_requires_authentication(client, firm, auth_headers, sent):
    url = (await invite(client, auth_headers, firm)).json()["invite_url"]
    r = await client.post("/api/v1/invites/accept", json={"token": token_from(url)})
    assert r.status_code == 401
