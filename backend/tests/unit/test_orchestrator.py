from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

import pytest

from app.agents.base import AgentResponse, TurnContext, TurnResult
from app.agents.orchestrator import AgentOrchestrator
from app.legal.procedure import ProcedureEngine
from app.legal.review import LegalReviewer
from app.models.simulation import Simulation

CASE = {"title": "State v. Kumar", "description": "Murder", "country": "India", "jurisdiction": ""}


@dataclass
class StubAgent:
    role: str
    replies: list[str]
    contexts: list[TurnContext] = field(default_factory=list)

    async def run_turn(self, context: TurnContext, vector_store=None, stream_callback=None):
        self.contexts.append(context)
        text = self.replies[min(len(self.contexts) - 1, len(self.replies) - 1)]
        return TurnResult(
            response=AgentResponse(
                content=text, citations=[], token_count=1, latency_ms=1,
                provider="stub", model="stub-1", prompt_sha256="p" * 64,
            ),
            spawns=[],
        )


@dataclass
class StubNode:
    agent_id: str
    role: str
    name: str
    agent: StubAgent


class StubGraph:
    def __init__(self, agents: list[tuple[str, str, list[str]]]) -> None:
        self.nodes: dict[str, StubNode] = {}
        self.root_agents: list[str] = []
        for role, name, replies in agents:
            aid = str(uuid4())
            self.nodes[aid] = StubNode(aid, role, name, StubAgent(role, replies))
            self.root_agents.append(aid)

    def get_turn_order(self) -> list[str]:
        return list(self.root_agents)

    def agent(self, name: str) -> StubAgent:
        return next(n.agent for n in self.nodes.values() if n.name == name)


def make(agents, *, max_turns=30, procedure=True, review=True, audit=None):
    graph = StubGraph(agents)
    sim = Simulation(case_id=uuid4(), title="t", mode="courtroom", created_by="u", max_turns=max_turns)
    sim.status = "running"
    persisted: list[tuple[TurnResult, str]] = []
    events: list[tuple[str, dict]] = []

    async def persist(result, agent_id, sim_id):
        persisted.append((result, agent_id))

    async def broadcast(event, payload):
        events.append((event, payload))

    orch = AgentOrchestrator(
        simulation=sim, graph=graph, case_metadata=dict(CASE),  # type: ignore[arg-type]
        turn_persist_fn=persist, broadcast_fn=broadcast,
        procedure=ProcedureEngine.for_mode("courtroom", max_turns) if procedure else None,
        reviewer=LegalReviewer() if review else None,
        audit_fn=audit,
    )
    return orch, graph, persisted, events


ROSTER = [
    ("judge", "Judge", ["Order."]),
    ("prosecutor", "Prosecutor", ["Prosecution speaks."]),
    ("defense", "Defense", ["Defence speaks."]),
    ("accused", "Accused", ["Accused speaks."]),
    ("witness", "Witness", ["Witness speaks."]),
]


async def roles_over(orch, n):
    out = []
    for _ in range(n):
        result = await orch.run_next_turn()
        assert result is not None
        out.append(orch._recent_turns[-1]["role"])
    return out


async def test_without_a_procedure_engine_agents_take_turns_round_robin():
    orch, *_ = make(ROSTER, procedure=False)
    assert await roles_over(orch, 6) == [
        "judge", "prosecutor", "defense", "accused", "witness", "judge",
    ]


async def test_procedure_engine_chooses_the_speaker_by_stage():
    orch, *_ = make(ROSTER, max_turns=7)
    assert await roles_over(orch, 7) == [
        "judge", "judge", "prosecutor", "judge", "defense", "prosecutor", "judge",
    ]


async def test_each_turn_gets_its_stage_directive():
    orch, graph, *_ = make(ROSTER, max_turns=7)
    await roles_over(orch, 3)
    first = graph.agent("Judge").contexts[0].extra["procedure_directive"]
    assert "Opening" in first and "Do not pronounce a verdict" in first
    prosecutor = graph.agent("Prosecutor").contexts[0].extra["procedure_directive"]
    assert "Prosecution evidence" in prosecutor


async def test_final_turn_is_a_judgment_that_may_state_a_verdict():
    orch, graph, *_ = make(ROSTER, max_turns=7)
    await roles_over(orch, 6)
    await orch.run_next_turn()
    last = graph.agent("Judge").contexts[-1].extra["procedure_directive"]
    assert "Judgment" in last and "Do not pronounce a verdict" not in last


async def test_counsel_objection_gives_the_next_turn_to_the_judge():
    roster = [
        ("judge", "Judge", ["Overruled. Continue."]),
        ("prosecutor", "Prosecutor", ["Please state your name."]),
        ("defense", "Defense", ["Objection, hearsay."]),
        ("witness", "Witness", ["My name is Meera."]),
    ]
    orch, graph, _, events = make(roster, max_turns=100)
    # Fast-forward to the examination stage: turn numbers 12.. are prosecution evidence.
    orch.simulation.current_turn = ProcedureEngine.for_mode("courtroom", 100).plan()[2]["start_turn"] + 2
    await orch.run_next_turn()  # the cycle gives the defence this slot and it objects
    assert orch._recent_turns[-1]["role"] == "defense"
    await orch.run_next_turn()
    assert orch._recent_turns[-1]["role"] == "judge"
    ruling_prompt = graph.agent("Judge").contexts[-1].extra["procedure_directive"]
    assert "SUSTAINED or OVERRULED" in ruling_prompt and "hearsay" in ruling_prompt
    completed = [p for e, p in events if e == "turn.completed"][-1]
    assert completed["procedure"]["ruling"] == "overruled"
    assert completed["procedure"]["violations"] == []


async def test_turn_is_reviewed_and_the_review_is_persisted_and_broadcast():
    roster = [("judge", "Judge", ["The State relies on Section 9999 BNS and Section 103 BNS."])]
    orch, _, persisted, events = make(roster)
    await orch.run_next_turn()

    meta = persisted[0][0].response.metadata
    assert meta["legal_review"]["status"] == "flagged"
    statuses = {c["ref"]: c["status"] for c in meta["legal_review"]["citations"]}
    assert statuses == {"BNS 9999": "nonexistent", "BNS 103": "verified"}
    assert meta["procedure"]["stage"] == "opening"

    names = [e for e, _ in events]
    assert names.index("citation.flagged") < names.index("turn.completed")
    flagged = next(p for e, p in events if e == "citation.flagged")
    assert [c["ref"] for c in flagged["citations"]] == ["BNS 9999"]
    completed = next(p for e, p in events if e == "turn.completed")
    assert completed["legal_review"]["status"] == "flagged"


async def test_an_agent_is_told_about_its_bad_citation_on_its_next_turn():
    roster = [("judge", "Judge", ["Under Section 9999 BNS I hold...", "Understood."])]
    orch, graph, *_ = make(roster, procedure=False)
    await orch.run_next_turn()
    await orch.run_next_turn()
    second = graph.agent("Judge").contexts[1].extra
    assert "CORRECTION FROM THE COURT REGISTRY" in second["corrections"]
    assert "9999" in second["corrections"]
    assert "corrections" not in graph.agent("Judge").contexts[0].extra


async def test_acceptable_but_dated_citations_do_not_trigger_corrections():
    roster = [("judge", "Judge", ["Section 302 IPC applies.", "Noted."])]
    orch, graph, *_ = make(roster, procedure=False)
    await orch.run_next_turn()
    await orch.run_next_turn()
    assert "corrections" not in graph.agent("Judge").contexts[1].extra


async def test_applicable_law_is_supplied_for_a_known_jurisdiction():
    orch, graph, *_ = make([("judge", "Judge", ["Order."])], procedure=False)
    await orch.run_next_turn()
    law = graph.agent("Judge").contexts[0].extra["legal_context"]
    assert "BNS 103" in law and "Do not invent section numbers" in law


async def test_no_legal_context_for_an_unknown_jurisdiction():
    orch, graph, *_ = make([("judge", "Judge", ["Order."])], procedure=False)
    orch.case_metadata["country"] = "Atlantis"
    await orch.run_next_turn()
    assert "legal_context" not in graph.agent("Judge").contexts[0].extra


async def test_review_can_be_disabled():
    orch, graph, persisted, events = make(
        [("judge", "Judge", ["Section 9999 BNS"])], procedure=False, review=False
    )
    await orch.run_next_turn()
    assert "legal_review" not in persisted[0][0].response.metadata
    assert "citation.flagged" not in [e for e, _ in events]
    assert "legal_context" not in graph.agent("Judge").contexts[0].extra


async def test_audit_events_record_provenance_without_the_text():
    seen: list[tuple[str, str, dict[str, Any]]] = []

    async def audit(event_type, actor, payload):
        seen.append((event_type, actor, payload))

    roster = [("judge", "Judge", ["Section 9999 BNS is relied upon."])]
    orch, graph, *_ = make(roster, audit=audit)
    await orch.run_next_turn()

    kinds = [k for k, _, _ in seen]
    assert kinds == ["turn.generated", "citation.flagged"]
    generated = seen[0][2]
    assert seen[0][1].startswith("agent:")
    assert generated["provider"] == "stub" and generated["model"] == "stub-1"
    assert generated["prompt_sha256"] == "p" * 64
    assert len(generated["content_sha256"]) == 64
    assert generated["legal_status"] == "flagged" and generated["stage"] == "opening"
    assert "Section 9999" not in str(generated)  # hashes, never the content


async def test_a_failing_audit_log_never_aborts_the_turn():
    async def broken_audit(*_):
        raise RuntimeError("audit store down")

    orch, _, persisted, events = make(ROSTER, audit=broken_audit)
    result = await orch.run_next_turn()
    assert result is not None and len(persisted) == 1
    assert "turn.completed" in [e for e, _ in events]


async def test_a_missing_role_in_the_roster_does_not_stall_the_proceeding():
    roster = [("judge", "Judge", ["Order."]), ("prosecutor", "Prosecutor", ["State speaks."])]
    orch, *_ = make(roster, max_turns=12)
    assert len(await roles_over(orch, 12)) == 12


@pytest.mark.parametrize("n", [2, 5])
async def test_simulation_stops_at_max_turns(n):
    orch, *_ = make(ROSTER, max_turns=n)
    count = 0
    async for _ in orch.run_all():
        count += 1
    assert count == n
