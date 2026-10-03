from __future__ import annotations

H = "user-a"


async def test_jurisdictions_lists_the_bundled_pack_with_its_caveat(client, auth_headers):
    body = (await client.get("/api/v1/legal/jurisdictions", headers=auth_headers(H))).json()
    india = next(j for j in body["jurisdictions"] if j["id"] == "IN")
    assert india["status"] == "starter_index"
    assert "verify" in india["notice"].lower()
    assert india["provision_count"] > 50 and india["case_count"] >= 10
    assert any(a["code"] == "IPC" and a["repealed"] for a in india["acts"])


async def test_provision_search(client, auth_headers):
    body = (await client.get("/api/v1/legal/provisions", params={"q": "anticipatory bail"},
                             headers=auth_headers(H))).json()
    refs = [f"{p['act']} {p['section']}" for p in body["provisions"]]
    assert "BNSS 482" in refs
    assert body["pack_status"] == "starter_index"


async def test_provision_search_unknown_jurisdiction_is_404(client, auth_headers):
    r = await client.get("/api/v1/legal/provisions", params={"q": "murder", "jurisdiction": "ZZ"},
                         headers=auth_headers(H))
    assert r.status_code == 404


async def test_verify_text_with_an_explicit_country(client, auth_headers):
    r = await client.post("/api/v1/legal/verify", headers=auth_headers(H), json={
        "text": "Under Section 302 IPC and Section 9999 BNS, as held in "
                "Maneka Gandhi v. Union of India (1978) 1 SCC 248.",
        "country": "India",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "flagged"
    by_ref = {c["ref"]: c["status"] for c in body["citations"]}
    assert by_ref["IPC 302"] == "superseded"
    assert by_ref["BNS 9999"] == "nonexistent"
    assert by_ref["(1978) 1 SCC 248"] == "verified"
    assert body["counts"]["nonexistent"] == 1
    assert "not a court" in body["disclaimer"]


async def test_verify_uses_the_cases_own_jurisdiction(client, auth_headers, seed):
    case = seed.case(H)  # country = India
    r = await client.post("/api/v1/legal/verify", headers=auth_headers(H),
                          json={"text": "Section 103 BNS", "case_id": case})
    assert r.json()["pack_id"] == "IN" and r.json()["status"] == "clean"


async def test_verify_without_a_pack_says_so_instead_of_guessing(client, auth_headers):
    body = (await client.post("/api/v1/legal/verify", headers=auth_headers(H), json={
        "text": "Section 302 IPC", "country": "Atlantis",
    })).json()
    assert body["status"] == "no_pack" and body["citations"] == []
    assert "cannot be checked" in body["notice"]


async def test_verify_rejects_empty_and_oversized_text(client, auth_headers):
    h = auth_headers(H)
    assert (await client.post("/api/v1/legal/verify", headers=h, json={"text": ""})
            ).status_code == 422
    assert (await client.post("/api/v1/legal/verify", headers=h, json={"text": "x" * 20_001})
            ).status_code == 422
