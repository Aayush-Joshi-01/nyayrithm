"""A whole simulation through the real engine, DB and API, with a scripted LLM."""

from __future__ import annotations

import tests.conftest
from collections.abc import AsyncIterator

import pytest

from app.legal.audit import sha256_text
from app.llm.base import LLMMessage, LLMResponse

H = "user-a"

SCRIPT: dict[str, list[str]] = {
    "judge": [
        "The court is in session.",
        "The charge under Section 103 BNS is read out. How does the accused plead?",
        "The accused is examined on the circumstances in the evidence.",
        "I find the accused not guilty and acquit him.",
    ],
    "prosecutor": [
        "The State relies on Section 9999 BNS and Section 302 IPC.",
        "In closing, the State rests on the exhibits.",
    ],
    "defense": ["The defence has no objection to the exhibit."],
}


class ScriptedLLM:
    """Replies from SCRIPT by role, and records every prompt it was given."""

    prompts: list[tuple[str, str]] = []
    calls: dict[str, int] = {}

    def __init__(self, role: str) -> None:
        self.role = role

    provider_name = "scripted"
    model_name = "scripted-1"

    def _next(self) -> str:
        n = ScriptedLLM.calls.get(self.role, 0)
        ScriptedLLM.calls[self.role] = n + 1
        replies = SCRIPT.get(self.role, ["Noted."])
        return replies[min(n, len(replies) - 1)]

    async def complete(self, messages: list[LLMMessage], **kw) -> LLMResponse:
        text = self._next()
        return LLMResponse(content=text, model="scripted-1", provider="scripted",
                           input_tokens=1, output_tokens=len(text.split()), latency_ms=1)

    async def stream(self, messages: list[LLMMessage], **kw) -> AsyncIterator[str]:
        ScriptedLLM.prompts.append((self.role, messages[-1].content))
        for word in self._next().split(" "):
            yield word + " "


@pytest.fixture
def scripted(monkeypatch):
    from app.config import get_settings

    ScriptedLLM.prompts, ScriptedLLM.calls = [], {}
    monkeypatch.setattr(
        "app.agents.graph.agent_graph.build_llm_provider",
        lambda role, override_provider=None, override_model=None: ScriptedLLM(role),
    )
    monkeypatch.setattr("app.simulation.engine.get_vector_store", lambda: None)
    monkeypatch.setenv("SIMULATION_TURN_DELAY_SECONDS", "0")
    get_settings.cache_clear()
    return ScriptedLLM


async def test_full_courtroom_simulation(client, auth_headers, seed, queued, scripted, db_path):
    from app.simulation.engine import SimulationEngine

    h = auth_headers(H)
    case = (await client.post("/api/v1/cases/", headers=h, json={
        "title": "State v. Kumar", "country": "India",
        "description": "Prosecution for murder and criminal conspiracy",
    })).json()["id"]
    sim = (await client.post(f"/api/v1/cases/{case}/simulations/", headers=h,
                             json={"title": "Trial", "max_turns": 7})).json()["id"]
    assert (await client.post(f"/api/v1/simulations/{sim}/start", headers=h)).status_code == 202

    events: list[tuple[str, dict]] = []

    async def broadcast(event, payload):
        events.append((event, payload))

    await SimulationEngine().run_simulation(sim, broadcast_fn=broadcast)

    # ── the simulation completed ──────────────────────────────────────────────
    state = (await client.get(f"/api/v1/simulations/{sim}", headers=h)).json()
    assert state["status"] == "completed" and state["current_turn"] == 7 and state["ended_at"]
    assert [e for e, _ in events].count("turn.completed") == 7
    assert events[-1][0] == "simulation.completed"

    # ── the procedure engine ran the courtroom, in order, across DB round-trips ─
    turns = (await client.get(f"/api/v1/simulations/{sim}/turns", headers=h)).json()["items"]
    agents = {a["id"]: a["role"] for a in
              (await client.get(f"/api/v1/simulations/{sim}/agents", headers=h)).json()}
    assert [agents[t["agent_id"]] for t in turns] == [
        "judge", "judge", "prosecutor", "judge", "defense", "prosecutor", "judge",
    ]
    assert [t["procedure"]["stage"] for t in turns] == [
        "opening", "charge", "prosecution_evidence", "accused_statement",
        "defence_evidence", "final_arguments", "judgment",
    ]
    assert all(t["procedure"]["violations"] == [] for t in turns)

    # ── citations were checked and the verdicts persisted with the turn ───────
    assert turns[1]["legal_review"]["status"] == "clean"
    bad = turns[2]["legal_review"]
    assert bad["status"] == "flagged"
    assert {c["ref"]: c["status"] for c in bad["citations"]} == {
        "BNS 9999": "nonexistent", "IPC 302": "superseded",
    }
    flagged = [p for e, p in events if e == "citation.flagged"]
    assert len(flagged) == 1 and flagged[0]["turn_number"] == 2

    # ── prompts carried the law, the stage, and the registry correction ───────
    by_role: dict[str, list[str]] = {}
    for role, prompt in scripted.prompts:
        by_role.setdefault(role, []).append(prompt)
    assert "PROCEEDING STAGE: Opening" in by_role["judge"][0]
    assert "BNS 103" in by_role["judge"][0]  # applicable-law context from the case text
    assert "Do not pronounce a verdict" in by_role["judge"][0]
    assert "Do not pronounce a verdict" not in by_role["judge"][-1]  # judgment stage
    assert "CORRECTION FROM THE COURT REGISTRY" not in by_role["prosecutor"][0]
    assert "CORRECTION FROM THE COURT REGISTRY" in by_role["prosecutor"][1]
    assert "Section 9999 BNS" in by_role["prosecutor"][1]

    # ── the audit trail is complete, hash-linked, and holds no speech ───────────
    audit = (await client.get(f"/api/v1/simulations/{sim}/audit?size=200", headers=h)).json()
    kinds = [e["event_type"] for e in audit["items"]]
    assert kinds[:2] == ["simulation.created", "simulation.started"]
    assert kinds.count("turn.generated") == 7 and kinds.count("citation.flagged") == 1
    assert kinds[-1] == "simulation.completed"
    generated = [e["payload"] for e in audit["items"] if e["event_type"] == "turn.generated"]
    assert generated[1]["content_sha256"] == sha256_text(turns[1]["content"])
    assert all(g["provider"] == "scripted" and len(g["prompt_sha256"]) == 64 for g in generated)
    assert "The State relies on" not in str(audit)  # flagged citations are logged, not the speech
    verdict = (await client.get(f"/api/v1/simulations/{sim}/audit/verify", headers=h)).json()
    assert verdict["valid"] and verdict["events"] == len(kinds)

    # ── provenance persisted on the turn row itself ───────────────────────────
    doc = tests.conftest._SYNC_MONGO["turns"].find_one({"simulation_id": sim, "turn_number": 0})
    assert len(doc["metadata"]["prompt_sha256"]) == 64 and doc["metadata"]["model"] == "scripted-1"
    assert doc["retrieved_chunks"] == []


async def test_simulation_for_an_unsupported_jurisdiction_runs_without_legal_review(
    client, auth_headers, seed, queued, scripted
):
    from app.simulation.engine import SimulationEngine

    h = auth_headers(H)
    case = (await client.post("/api/v1/cases/", headers=h, json={
        "title": "Atlantis v. Poseidon", "country": "Atlantis"})).json()["id"]
    sim = (await client.post(f"/api/v1/cases/{case}/simulations/", headers=h,
                             json={"title": "Trial", "max_turns": 3})).json()["id"]
    await client.post(f"/api/v1/simulations/{sim}/start", headers=h)
    await SimulationEngine().run_simulation(sim)

    turns = (await client.get(f"/api/v1/simulations/{sim}/turns", headers=h)).json()["items"]
    assert len(turns) == 3
    assert all(t["legal_review"]["status"] == "no_pack" for t in turns)
    assert all("Applicable law" not in p for _, p in scripted.prompts)


async def test_paused_simulation_does_not_run(client, auth_headers, seed, queued, scripted):
    from app.simulation.engine import SimulationEngine

    h = auth_headers(H)
    case = seed.case(H)
    sim = (await client.post(f"/api/v1/cases/{case}/simulations/", headers=h,
                             json={"title": "Trial", "max_turns": 3})).json()["id"]
    # still 'draft': the engine only runs simulations that were started
    await SimulationEngine().run_simulation(sim)
    assert (await client.get(f"/api/v1/simulations/{sim}/turns", headers=h)).json()["total"] == 0
