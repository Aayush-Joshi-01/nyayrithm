from __future__ import annotations

import json
import sqlite3

import pytest

import tests.conftest

H = "user-a"


async def make_sim(client, auth_headers, seed, **body):
    case = seed.case(H)
    r = await client.post(
        f"/api/v1/cases/{case}/simulations/",
        json={"title": "Trial", **body}, headers=auth_headers(H),
    )
    assert r.status_code == 201, r.text
    return case, r.json()


# ── creation ──────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("mode,roles", [
    ("courtroom", {"judge", "prosecutor", "defense", "accused", "witness"}),
    ("deposition", {"plaintiff", "defense", "witness", "investigator"}),
    ("strategy", {"defense", "investigator", "expert_witness"}),
])
async def test_default_roster_is_seeded_per_mode(client, auth_headers, seed, mode, roles):
    _, sim = await make_sim(client, auth_headers, seed, mode=mode)
    agents = (await client.get(f"/api/v1/simulations/{sim['id']}/agents",
                               headers=auth_headers(H))).json()
    assert {a["role"] for a in agents} == roles
    assert all(a["is_predefined"] and a["llm_provider"] == "gemini" for a in agents)


async def test_roster_seeding_can_be_disabled(client, auth_headers, seed):
    _, sim = await make_sim(client, auth_headers, seed, config={"seed_default_agents": False})
    assert (await client.get(f"/api/v1/simulations/{sim['id']}/agents",
                             headers=auth_headers(H))).json() == []


async def test_simulation_carries_the_disclaimer(client, auth_headers, seed):
    _, sim = await make_sim(client, auth_headers, seed)
    assert "not a court" in sim["disclaimer"]
    assert sim["status"] == "draft" and sim["current_turn"] == 0


@pytest.mark.parametrize("body", [
    {"title": "x", "mode": "kangaroo"},
    {"title": "x", "max_turns": 0},
    {"title": "x", "max_turns": 501},
    {"title": ""},
])
async def test_invalid_simulation_is_rejected(client, auth_headers, seed, body):
    case = seed.case(H)
    r = await client.post(f"/api/v1/cases/{case}/simulations/", json=body, headers=auth_headers(H))
    assert r.status_code == 422


# ── lifecycle ─────────────────────────────────────────────────────────────────
async def test_start_queues_the_run_and_marks_it_running(client, auth_headers, seed, queued):
    _, sim = await make_sim(client, auth_headers, seed)
    r = await client.post(f"/api/v1/simulations/{sim['id']}/start", headers=auth_headers(H))
    assert r.status_code == 202
    queued["run"].assert_called_once_with(sim["id"])
    state = (await client.get(f"/api/v1/simulations/{sim['id']}", headers=auth_headers(H))).json()
    assert state["status"] == "running" and state["started_at"]


async def test_cannot_start_twice(client, auth_headers, seed, queued):
    _, sim = await make_sim(client, auth_headers, seed)
    h = auth_headers(H)
    await client.post(f"/api/v1/simulations/{sim['id']}/start", headers=h)
    r = await client.post(f"/api/v1/simulations/{sim['id']}/start", headers=h)
    assert r.status_code == 409 and "running" in r.json()["message"]
    assert queued["run"].call_count == 1


async def test_pause_then_resume(client, auth_headers, seed, queued):
    _, sim = await make_sim(client, auth_headers, seed)
    h, base = auth_headers(H), f"/api/v1/simulations/{sim['id']}"
    await client.post(f"{base}/start", headers=h)
    assert (await client.post(f"{base}/pause", headers=h)).status_code == 202
    assert (await client.get(base, headers=h)).json()["status"] == "paused"
    assert (await client.post(f"{base}/start", headers=h)).status_code == 202
    assert queued["run"].call_count == 2


async def test_cannot_pause_a_simulation_that_is_not_running(client, auth_headers, seed):
    _, sim = await make_sim(client, auth_headers, seed)
    r = await client.post(f"/api/v1/simulations/{sim['id']}/pause", headers=auth_headers(H))
    assert r.status_code == 409


async def test_stop_completes_it(client, auth_headers, seed, queued):
    _, sim = await make_sim(client, auth_headers, seed)
    h, base = auth_headers(H), f"/api/v1/simulations/{sim['id']}"
    await client.post(f"{base}/start", headers=h)
    assert (await client.post(f"{base}/stop", headers=h)).status_code == 202
    state = (await client.get(base, headers=h)).json()
    assert state["status"] == "completed" and state["ended_at"]
    assert (await client.post(f"{base}/start", headers=h)).status_code == 409


# ── agents ────────────────────────────────────────────────────────────────────
async def test_add_and_remove_agents(client, auth_headers, seed):
    _, sim = await make_sim(client, auth_headers, seed, config={"seed_default_agents": False})
    h, base = auth_headers(H), f"/api/v1/simulations/{sim['id']}"
    r = await client.post(f"{base}/agents", headers=h, json={
        "role": "witness", "name": "Meera", "persona": {"age": 31},
    })
    assert r.status_code == 201
    agent = r.json()
    assert agent["name"] == "Meera" and agent["persona"] == {"age": 31}
    assert agent["llm_provider"] == "gemini"  # role default

    assert (await client.delete(f"{base}/agents/{agent['id']}", headers=h)).status_code == 204
    assert (await client.get(f"{base}/agents", headers=h)).json() == []
    assert (await client.delete(f"{base}/agents/{agent['id']}", headers=h)).status_code == 404


async def test_unknown_role_is_rejected(client, auth_headers, seed):
    _, sim = await make_sim(client, auth_headers, seed)
    r = await client.post(f"/api/v1/simulations/{sim['id']}/agents", headers=auth_headers(H),
                          json={"role": "bailiff-of-doom", "name": "X"})
    assert r.status_code == 422


async def test_agents_are_frozen_while_running(client, auth_headers, seed, queued):
    _, sim = await make_sim(client, auth_headers, seed)
    h, base = auth_headers(H), f"/api/v1/simulations/{sim['id']}"
    agents = (await client.get(f"{base}/agents", headers=h)).json()
    await client.post(f"{base}/start", headers=h)
    added = await client.post(f"{base}/agents", headers=h, json={"role": "witness", "name": "Late"})
    removed = await client.delete(f"{base}/agents/{agents[0]['id']}", headers=h)
    assert added.status_code == 409 and removed.status_code == 409


async def test_graph_links_spawned_agents_to_their_parent(client, auth_headers, seed):
    _, sim = await make_sim(client, auth_headers, seed, config={"seed_default_agents": False})
    parent = seed.agent(sim["id"], "judge", name="Judge")
    child = seed.agent(sim["id"], "expert_witness", name="Expert", is_predefined=0,
                       parent_agent_id=parent, spawn_reason="needed forensics")
    graph = (await client.get(f"/api/v1/simulations/{sim['id']}/graph",
                              headers=auth_headers(H))).json()
    assert {n["id"] for n in graph["nodes"]} == {parent, child}
    assert graph["edges"] == [{"source": parent, "target": child, "reason": "needed forensics"}]


# ── clone & delete ────────────────────────────────────────────────────────────
async def test_clone_copies_only_the_predefined_roster(client, auth_headers, seed):
    case, sim = await make_sim(client, auth_headers, seed)
    h = auth_headers(H)
    original = (await client.get(f"/api/v1/simulations/{sim['id']}/agents", headers=h)).json()
    seed.agent(sim["id"], "expert_witness", is_predefined=0,
               parent_agent_id=original[0]["id"], name="Spawned")

    r = await client.post(f"/api/v1/simulations/{sim['id']}/clone", headers=h)
    assert r.status_code == 201
    copy = r.json()
    assert copy["id"] != sim["id"] and copy["title"] == "Trial (copy)"
    assert copy["case_id"] == case and copy["status"] == "draft"

    copied = (await client.get(f"/api/v1/simulations/{copy['id']}/agents", headers=h)).json()
    assert len(copied) == len(original) == 5
    assert all(a["name"] != "Spawned" for a in copied)
    assert {a["id"] for a in copied}.isdisjoint({a["id"] for a in original})


async def test_delete_removes_agents_turns_and_audit_but_not_the_case(
    client, auth_headers, seed, db_path
):
    case, sim = await make_sim(client, auth_headers, seed)
    h = auth_headers(H)
    agent = seed.agent(sim["id"])
    seed.turn(sim["id"], agent)
    assert (await client.delete(f"/api/v1/simulations/{sim['id']}", headers=h)).status_code == 204

    assert (await client.get(f"/api/v1/simulations/{sim['id']}", headers=h)).status_code == 404
    assert (await client.get(f"/api/v1/cases/{case}", headers=h)).status_code == 200
    conn = sqlite3.connect(db_path)
    for table in ("agent_definitions", "audit_events"):
        count = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE simulation_id = ?",
                             [sim["id"]]).fetchone()[0]
        assert count == 0, table
    conn.close()
    assert tests.conftest._SYNC_MONGO["turns"].count_documents({"simulation_id": sim["id"]}) == 0


# ── turns ─────────────────────────────────────────────────────────────────────
async def test_turns_expose_legal_review_and_procedure(client, auth_headers, seed, db_path):
    _, sim = await make_sim(client, auth_headers, seed, config={"seed_default_agents": False})
    agent = seed.agent(sim["id"])
    seed.turn(sim["id"], agent, content="Section 9999 BNS", metadata={
        "legal_review": {"status": "flagged", "citations": []},
        "procedure": {"stage": "opening", "violations": []},
    })

    body = (await client.get(f"/api/v1/simulations/{sim['id']}/turns",
                             headers=auth_headers(H))).json()
    assert body["items"][0]["legal_review"]["status"] == "flagged"
    assert body["items"][0]["procedure"]["stage"] == "opening"
    assert "not a court" in body["disclaimer"]


async def test_editing_a_turn_marks_it_and_is_audited(client, auth_headers, seed):
    _, sim = await make_sim(client, auth_headers, seed, config={"seed_default_agents": False})
    agent = seed.agent(sim["id"])
    turn = seed.turn(sim["id"], agent, content="original words")
    h, base = auth_headers(H), f"/api/v1/simulations/{sim['id']}"

    r = await client.patch(f"{base}/turns/{turn}", json={"content": "edited words"}, headers=h)
    assert r.status_code == 200
    assert r.json()["content_edited"] == "edited words" and r.json()["is_human_override"]
    assert r.json()["content"] == "original words"  # the agent's words are never overwritten

    events = (await client.get(f"{base}/audit", headers=h)).json()["items"]
    edit = next(e for e in events if e["event_type"] == "turn.edited")
    assert edit["actor"] == f"user:{H}"
    assert edit["payload"]["original_sha256"] != edit["payload"]["edited_sha256"]
    assert "edited words" not in json.dumps(edit)  # hashes only, never the text
    assert (await client.get(f"{base}/audit/verify", headers=h)).json()["valid"]


async def test_turn_from_another_simulation_is_not_found(client, auth_headers, seed):
    _, sim1 = await make_sim(client, auth_headers, seed, config={"seed_default_agents": False})
    _, sim2 = await make_sim(client, auth_headers, seed, config={"seed_default_agents": False})
    other_turn = seed.turn(sim2["id"], seed.agent(sim2["id"]))
    r = await client.patch(f"/api/v1/simulations/{sim1['id']}/turns/{other_turn}",
                           json={"content": "x"}, headers=auth_headers(H))
    assert r.status_code == 404


# ── audit & procedure endpoints ───────────────────────────────────────────────
async def test_lifecycle_is_recorded_in_a_verifiable_audit_trail(
    client, auth_headers, seed, queued
):
    _, sim = await make_sim(client, auth_headers, seed)
    h, base = auth_headers(H), f"/api/v1/simulations/{sim['id']}"
    await client.post(f"{base}/start", headers=h)
    await client.post(f"{base}/pause", headers=h)
    await client.post(f"{base}/stop", headers=h)

    items = (await client.get(f"{base}/audit", headers=h)).json()["items"]
    assert [e["event_type"] for e in items] == [
        "simulation.created", "simulation.started", "simulation.paused", "simulation.stopped",
    ]
    assert [e["seq"] for e in items] == [0, 1, 2, 3]
    assert items[0]["prev_hash"] == "0" * 64
    assert all(e["actor"] == f"user:{H}" for e in items)
    verdict = (await client.get(f"{base}/audit/verify", headers=h)).json()
    assert verdict["valid"] and verdict["events"] == 4 and verdict["head_hash"] == items[-1]["hash"]


async def test_audit_verification_detects_database_tampering(
    client, auth_headers, seed, queued, db_path
):
    _, sim = await make_sim(client, auth_headers, seed)
    h, base = auth_headers(H), f"/api/v1/simulations/{sim['id']}"
    await client.post(f"{base}/start", headers=h)
    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE audit_events SET actor = 'user:mallory' WHERE seq = 1")
    conn.commit()
    conn.close()
    verdict = (await client.get(f"{base}/audit/verify", headers=h)).json()
    assert verdict["valid"] is False and verdict["broken_at"] == 1


async def test_procedure_endpoint_reports_the_plan_and_current_stage(client, auth_headers, seed):
    _, sim = await make_sim(client, auth_headers, seed, max_turns=40)
    body = (await client.get(f"/api/v1/simulations/{sim['id']}/procedure",
                             headers=auth_headers(H))).json()
    assert body["enforced"] and body["current_stage"] == "opening"
    assert body["stages"][0]["key"] == "opening"
    assert body["stages"][-1]["key"] == "judgment" and body["stages"][-1]["end_turn"] == 39


async def test_procedure_is_not_reported_for_strategy_mode(client, auth_headers, seed):
    _, sim = await make_sim(client, auth_headers, seed, mode="strategy")
    body = (await client.get(f"/api/v1/simulations/{sim['id']}/procedure",
                             headers=auth_headers(H))).json()
    assert body == {"enforced": False, "mode": "strategy", "stages": [], "current_stage": None}


async def test_procedure_can_be_switched_off(client, auth_headers, seed):
    _, sim = await make_sim(client, auth_headers, seed, config={"enforce_procedure": False})
    body = (await client.get(f"/api/v1/simulations/{sim['id']}/procedure",
                             headers=auth_headers(H))).json()
    assert body["enforced"] is False
