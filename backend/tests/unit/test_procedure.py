from __future__ import annotations

import pytest

from app.legal.procedure import (
    COURTROOM_STAGES,
    ProcedureEngine,
    detect_objection,
    detect_ruling,
)

ALL_ROLES = {"judge", "prosecutor", "defense", "accused", "witness"}


def engine(max_turns: int = 50, mode: str = "courtroom") -> ProcedureEngine:
    eng = ProcedureEngine.for_mode(mode, max_turns)
    assert eng is not None
    return eng


# ── budgeting and stage mapping ───────────────────────────────────────────────
@pytest.mark.parametrize("max_turns", [7, 10, 25, 50, 100, 500])
def test_budgets_use_exactly_the_turn_limit(max_turns):
    eng = engine(max_turns)
    assert sum(eng.budgets) == max_turns
    assert all(b >= 1 for b in eng.budgets)


def test_tiny_budgets_still_sum_correctly():
    eng = engine(3)
    assert sum(eng.budgets) == 3


def test_stage_order_and_boundaries():
    eng = engine(50)
    plan = eng.plan()
    assert [p["key"] for p in plan] == [s.key for s in COURTROOM_STAGES]
    assert plan[0]["start_turn"] == 0
    for a, b in zip(plan, plan[1:], strict=False):
        assert b["start_turn"] == a["end_turn"] + 1
    assert plan[-1]["end_turn"] == 49
    assert eng.slot(0).stage.key == "opening"
    assert eng.slot(49).stage.key == "judgment"
    assert eng.slot(plan[2]["start_turn"]).stage.key == "prosecution_evidence"


def test_turns_past_the_plan_stay_in_the_final_stage():
    assert engine(20).slot(500).stage.key == "judgment"


def test_unknown_mode_has_no_procedure():
    assert ProcedureEngine.for_mode("strategy", 30) is None


# ── speaker selection ─────────────────────────────────────────────────────────
def first_turn_of(eng: ProcedureEngine, key: str) -> int:
    return next(p["start_turn"] for p in eng.plan() if p["key"] == key)


def test_examination_cycle_alternates_counsel_and_witness():
    eng = engine(100)
    start = first_turn_of(eng, "prosecution_evidence")
    roles = [eng.next_speaker_role(start + i, None, ALL_ROLES) for i in range(4)]
    assert roles == ["prosecutor", "witness", "defense", "witness"]


def test_judge_opens_and_pronounces_judgment():
    eng = engine(50)
    assert eng.next_speaker_role(0, None, ALL_ROLES) == "judge"
    assert eng.next_speaker_role(49, None, ALL_ROLES) == "judge"


def test_missing_role_is_skipped_rather_than_deadlocking():
    eng = engine(100)
    start = first_turn_of(eng, "prosecution_evidence")
    roles = {eng.next_speaker_role(start + i, None, {"judge", "prosecutor", "witness"})
             for i in range(8)}
    assert roles <= {"judge", "prosecutor", "witness"} and None not in roles


def test_no_available_roles_returns_none():
    assert engine().next_speaker_role(0, None, set()) is None


def test_deposition_uses_plaintiff_or_prosecutor_as_questioner():
    eng = engine(20, "deposition")
    assert eng.next_speaker_role(0, None, {"plaintiff", "witness", "defense"}) == "plaintiff"
    assert eng.next_speaker_role(0, None, {"prosecutor", "witness", "defense"}) == "prosecutor"


# ── objections and rulings ────────────────────────────────────────────────────
@pytest.mark.parametrize("text,ground", [
    ("Objection, hearsay.", "hearsay"),
    ("Objection! Leading question, my lord.", "leading"),
    ("Objection — relevance.", "relevance"),
    ("Objection, your honour.", None),
])
def test_objection_detection(text, ground):
    assert detect_objection(text) == {"ground": ground}


def test_no_objection_is_not_an_objection():
    assert detect_objection("The defence has no objection to the exhibit.") is None
    assert detect_objection("Counsel may proceed.") is None


def test_ruling_detection():
    assert detect_ruling("Sustained. Rephrase the question.") == "sustained"
    assert detect_ruling("Objection overruled.") == "overruled"
    assert detect_ruling("Proceed.") is None


def test_objection_by_counsel_hands_the_floor_to_the_judge():
    eng = engine(100)
    start = first_turn_of(eng, "prosecution_evidence")
    last = {"role": "defense", "content": "Objection, hearsay."}
    assert eng.ruling_due(last, ALL_ROLES)
    assert eng.next_speaker_role(start + 1, last, ALL_ROLES) == "judge"
    assert "SUSTAINED or OVERRULED" in eng.directive(start + 1, "judge", last, ALL_ROLES)
    assert "hearsay" in eng.directive(start + 1, "judge", last, ALL_ROLES)


def test_witness_objection_does_not_trigger_a_ruling():
    eng = engine()
    last = {"role": "witness", "content": "Objection!"}
    assert not eng.ruling_due(last, ALL_ROLES)


def test_no_ruling_without_a_judge():
    assert not engine().ruling_due(
        {"role": "defense", "content": "Objection, hearsay."}, {"defense", "witness"}
    )


# ── directives ────────────────────────────────────────────────────────────────
def test_directive_names_the_stage_and_forbids_early_verdicts():
    eng = engine(100)
    start = first_turn_of(eng, "prosecution_evidence")
    text = eng.directive(start, "prosecutor", None, ALL_ROLES)
    assert "Prosecution evidence" in text
    assert "non-leading" in text
    assert "Do not pronounce a verdict" in text


def test_judgment_directive_asks_for_a_verdict():
    eng = engine(50)
    text = eng.directive(49, "judge", None, ALL_ROLES)
    assert "verdict" in text and "Do not pronounce a verdict" not in text


def test_procedural_notes_are_included_when_supplied():
    eng = ProcedureEngine.for_mode("courtroom", 50, {"accused_statement": "BNSS s.351 applies."})
    start = first_turn_of(eng, "accused_statement")
    assert "BNSS s.351" in eng.directive(start, "judge", None, ALL_ROLES)


# ── turn review ───────────────────────────────────────────────────────────────
def test_premature_verdict_is_flagged():
    eng = engine(50)
    review = eng.review_turn(
        10, "judge", "I find the accused guilty of the offence charged.", None
    )
    assert [v["code"] for v in review.violations] == ["premature_verdict"]


def test_verdict_in_judgment_stage_is_fine():
    eng = engine(50)
    review = eng.review_turn(49, "judge", "I find the accused not guilty and acquit him.", None)
    assert review.violations == []


def test_judgment_without_a_verdict_is_flagged():
    eng = engine(50)
    review = eng.review_turn(49, "judge", "The court has heard the parties at length.", None)
    assert [v["code"] for v in review.violations] == ["verdict_missing"]


def test_judge_who_does_not_rule_on_an_objection_is_flagged():
    eng = engine(100)
    start = first_turn_of(eng, "prosecution_evidence")
    last = {"role": "prosecutor", "content": "Objection, relevance."}
    review = eng.review_turn(start + 3, "judge", "Please continue.", last)
    assert [v["code"] for v in review.violations] == ["ruling_missing"]
    ok = eng.review_turn(start + 3, "judge", "Overruled. Continue.", last)
    assert ok.violations == [] and ok.ruling == "overruled"


def test_witness_objecting_is_flagged():
    review = engine().review_turn(15, "witness", "Objection, that is leading!", None)
    assert [v["code"] for v in review.violations] == ["objection_by_non_counsel"]


def test_review_reports_stage_and_objection():
    eng = engine(100)
    start = first_turn_of(eng, "prosecution_evidence")
    review = eng.review_turn(start + 2, "defense", "Objection, hearsay.", None).to_dict()
    assert review["stage"] == "prosecution_evidence"
    assert review["objection"] == {"ground": "hearsay"}
    assert review["violations"] == []
