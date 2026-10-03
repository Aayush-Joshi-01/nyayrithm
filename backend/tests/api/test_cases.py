from __future__ import annotations

import pytest

NEW_CASE = {
    "title": "State v. Sharma",
    "description": "Alleged breach of trust",
    "country": "India",
    "jurisdiction": "Delhi",
    "legal_system": "common_law",
}


async def test_create_case_records_the_authenticated_owner(client, auth_headers):
    r = await client.post("/api/v1/cases/", json=NEW_CASE, headers=auth_headers("alice"))
    assert r.status_code == 201
    body = r.json()
    assert body["created_by"] == "alice"
    assert body["status"] == "open" and body["title"] == "State v. Sharma"


async def test_client_cannot_choose_the_owner(client, auth_headers):
    r = await client.post(
        "/api/v1/cases/", json={**NEW_CASE, "created_by": "someone-else"},
        headers=auth_headers("alice"),
    )
    assert r.status_code == 201 and r.json()["created_by"] == "alice"


@pytest.mark.parametrize("patch", [
    {"title": "x"},          # too short
    {"country": ""},
    {"title": None},
])
async def test_invalid_case_is_rejected(client, auth_headers, patch):
    body = {**NEW_CASE, **patch}
    if body.get("title") is None:
        body.pop("title")
    r = await client.post("/api/v1/cases/", json=body, headers=auth_headers())
    assert r.status_code == 422


async def test_get_update_delete_roundtrip(client, auth_headers):
    h = auth_headers("alice")
    case_id = (await client.post("/api/v1/cases/", json=NEW_CASE, headers=h)).json()["id"]

    r = await client.put(f"/api/v1/cases/{case_id}", json={"title": "State v. Sharma (appeal)"},
                         headers=h)
    assert r.status_code == 200
    assert r.json()["title"] == "State v. Sharma (appeal)"
    assert r.json()["country"] == "India"  # untouched fields survive a partial update

    assert (await client.delete(f"/api/v1/cases/{case_id}", headers=h)).status_code == 204
    assert (await client.get(f"/api/v1/cases/{case_id}", headers=h)).status_code == 404
    assert (await client.delete(f"/api/v1/cases/{case_id}", headers=h)).status_code == 404


async def test_update_cannot_reassign_ownership(client, auth_headers):
    h = auth_headers("alice")
    case_id = (await client.post("/api/v1/cases/", json=NEW_CASE, headers=h)).json()["id"]
    await client.put(f"/api/v1/cases/{case_id}", json={"created_by": "bob"}, headers=h)
    assert (await client.get(f"/api/v1/cases/{case_id}", headers=h)).json()["created_by"] == "alice"


async def test_list_paginates_and_filters_by_status(client, auth_headers):
    h = auth_headers("alice")
    ids = []
    for i in range(5):
        ids.append((await client.post(
            "/api/v1/cases/", json={**NEW_CASE, "title": f"Case number {i}"}, headers=h
        )).json()["id"])
    await client.put(f"/api/v1/cases/{ids[0]}", json={"status": "closed"}, headers=h)

    page = (await client.get("/api/v1/cases/?page=1&size=2", headers=h)).json()
    assert page["total"] == 5 and len(page["items"]) == 2 and page["size"] == 2
    last = (await client.get("/api/v1/cases/?page=3&size=2", headers=h)).json()
    assert len(last["items"]) == 1

    closed = (await client.get("/api/v1/cases/?status=closed", headers=h)).json()
    assert [c["id"] for c in closed["items"]] == [ids[0]]


@pytest.mark.parametrize("query", ["page=0", "size=0", "size=101"])
async def test_list_rejects_bad_paging(client, auth_headers, query):
    assert (await client.get(f"/api/v1/cases/?{query}", headers=auth_headers())).status_code == 422


async def test_malformed_id_is_a_validation_error_not_a_server_error(client, auth_headers):
    assert (await client.get("/api/v1/cases/not-a-uuid", headers=auth_headers())).status_code == 422
