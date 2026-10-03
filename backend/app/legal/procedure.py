"""Courtroom procedure: who may speak when, and what the proceeding requires of them.

Unconstrained LLM judges drift: they pronounce a verdict in the middle of
cross-examination, let witnesses give closing speeches and rule on nothing. The engine
fixes the order of stages for a mode and, for every turn, decides the speaker and the
instruction. It is stateless on purpose - the simulation engine rebuilds the
orchestrator every turn - so the stage is a pure function of the turn number and the
turn budget, and the only context it reads is the previous turn (for objections).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

COUNSEL_ROLES = frozenset({"prosecutor", "defense", "plaintiff"})


@dataclass(frozen=True)
class Stage:
    key: str
    label: str
    weight: float
    cycle: tuple[str, ...]  # speaker roles in order; "a|b" means "a, else b"
    directives: dict[str, str]  # role -> instruction; "*" is the default


@dataclass(frozen=True)
class Slot:
    stage: Stage
    stage_turn: int   # 0-based turn index within the stage
    budget: int       # turns allotted to the stage


@dataclass
class ProcedureReview:
    stage_key: str
    stage_label: str
    objection: dict[str, str | None] | None = None
    ruling: str | None = None
    violations: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage_key,
            "stage_label": self.stage_label,
            "objection": self.objection,
            "ruling": self.ruling,
            "violations": self.violations,
        }


# ── stage templates ───────────────────────────────────────────────────────────
COURTROOM_STAGES: tuple[Stage, ...] = (
    Stage("opening", "Opening", 0.06, ("judge", "prosecutor", "defense"), {
        "judge": "Call the matter, identify the parties and state that proceedings begin. Be brief.",
        "prosecutor": "Give a short opening statement: what the prosecution alleges and what it will prove. Do not argue the law at length.",
        "defense": "Give a short opening statement: the defence position and what you will challenge. Do not argue the law at length.",
    }),
    Stage("charge", "Framing of charge", 0.06, ("judge", "accused"), {
        "judge": "Read out and explain the charge to the accused and ask how the accused pleads.",
        "accused": "Enter your plea in a sentence or two. Do not narrate your account yet.",
    }),
    Stage("prosecution_evidence", "Prosecution evidence", 0.34,
          ("prosecutor", "witness", "defense|prosecutor", "witness"), {
        "prosecutor": "Examine the witness in chief. Ask short, non-leading questions about what the witness personally saw or did; refer to exhibits by their evidence markers. One or two questions only.",
        "witness": "Answer only the question just put, from your own knowledge. Do not volunteer opinions or argue.",
        "defense": "Cross-examine the witness. Leading questions are allowed here; test reliability, consistency and opportunity to observe. You may raise a proper objection (state the ground) if the prosecution's question was improper.",
        "*": "Take your turn in the evidence stage, staying within your role.",
    }),
    Stage("accused_statement", "Examination of the accused", 0.08, ("judge", "accused"), {
        "judge": "Put the incriminating circumstances appearing in the evidence to the accused and invite an explanation.",
        "accused": "Respond to the circumstances put to you. You are not sworn and may decline to explain.",
    }),
    Stage("defence_evidence", "Defence evidence", 0.20,
          ("defense", "witness", "prosecutor", "witness"), {
        "defense": "Examine the defence witness in chief with short, non-leading questions. One or two questions only.",
        "witness": "Answer only the question just put, from your own knowledge.",
        "prosecutor": "Cross-examine the defence witness. Leading questions are allowed; you may raise a proper objection (state the ground) to an improper defence question.",
        "*": "Take your turn in the evidence stage, staying within your role.",
    }),
    Stage("final_arguments", "Final arguments", 0.18, ("prosecutor", "defense"), {
        "prosecutor": "Deliver your closing argument: marshal the evidence (with markers), apply the law and say what the court should find. No new evidence.",
        "defense": "Deliver your closing argument: attack gaps and contradictions, apply the law (including burden and standard of proof) and say what the court should find. No new evidence.",
    }),
    Stage("judgment", "Judgment", 0.08, ("judge",), {
        "judge": "Pronounce judgment: state the points for determination, decide each with reasons grounded in the evidence and law, and state the verdict clearly (guilty / not guilty, with any sentence).",
    }),
)

DEPOSITION_STAGES: tuple[Stage, ...] = (
    Stage("examination", "Examination of the deponent", 0.50, ("plaintiff|prosecutor", "witness"), {
        "*": "Take your turn in the examination of the deponent, staying within your role.",
        "witness": "Answer only the question put, from your own direct knowledge.",
        "plaintiff": "Put one or two clear, non-leading questions to the deponent.",
        "prosecutor": "Put one or two clear, non-leading questions to the deponent.",
    }),
    Stage("cross_examination", "Cross-examination", 0.35, ("defense", "witness"), {
        "defense": "Cross-examine the deponent with short leading questions; you may state an objection for the record.",
        "witness": "Answer only the question put, from your own direct knowledge.",
    }),
    Stage("re_examination", "Re-examination", 0.15, ("plaintiff|prosecutor", "witness"), {
        "*": "Clarify only matters raised in cross-examination.",
        "witness": "Answer only the question put.",
    }),
)

_TEMPLATES: dict[str, tuple[Stage, ...]] = {
    "courtroom": COURTROOM_STAGES,
    "deposition": DEPOSITION_STAGES,
}

# ── text detection ────────────────────────────────────────────────────────────
_OBJECTION = re.compile(
    r"\bobjection\b[\s,:!.\-–—]*"
    r"(?P<ground>leading|hearsay|relevan\w+|speculat\w+|asked and answered|compound|"
    r"argumentative|privilege\w*|assumes facts|beyond the scope|calls for (?:a )?(?:conclusion|narrative)|"
    r"lack of foundation|foundation|misleading|badgering)?",
    re.I,
)
_RULING = re.compile(r"\b(sustained|overruled)\b", re.I)
_VERDICT = re.compile(
    r"\b(?:find|found|hold|held|declare|pronounce)\b[^.\n]{0,80}\b(not guilty|guilty|liable|not liable)\b"
    r"|\bI\s+(?:hereby\s+)?(convict|acquit)\b",
    re.I,
)
_VERDICT_WORDS = re.compile(
    r"\b(guilty|not guilty|acquit\w*|convict\w*|liable|not liable|decree|dismiss\w*)\b", re.I
)


def detect_objection(text: str) -> dict[str, str | None] | None:
    """An objection raised by the speaker: 'Objection, hearsay.' (not 'no objection')."""
    for m in _OBJECTION.finditer(text):
        before = text[max(0, m.start() - 6): m.start()].lower()
        if before.endswith("no "):
            continue
        ground = (m.group("ground") or "").lower().strip() or None
        return {"ground": ground}
    return None


def detect_ruling(text: str) -> str | None:
    m = _RULING.search(text)
    return m.group(1).lower() if m else None


class ProcedureEngine:
    def __init__(
        self,
        stages: tuple[Stage, ...],
        max_turns: int,
        notes: dict[str, str] | None = None,
    ) -> None:
        self.stages = stages
        self.max_turns = max(1, max_turns)
        self.notes = notes or {}
        self.budgets = self._allocate(stages, self.max_turns)

    @classmethod
    def for_mode(
        cls, mode: str, max_turns: int, notes: dict[str, str] | None = None
    ) -> ProcedureEngine | None:
        stages = _TEMPLATES.get(mode)
        return cls(stages, max_turns, notes) if stages else None

    # ── planning ──────────────────────────────────────────────────────────────
    @staticmethod
    def _allocate(stages: tuple[Stage, ...], total: int) -> list[int]:
        """Largest-remainder split of ``total`` turns by weight; every stage gets a turn
        when the budget allows it."""
        weight_sum = sum(s.weight for s in stages)
        raw = [total * s.weight / weight_sum for s in stages]
        budgets = [int(r) for r in raw]
        if total >= len(stages):
            budgets = [max(1, b) for b in budgets]
        # Settle the rounding difference on the largest fractional remainders.
        while sum(budgets) < total:
            i = max(range(len(stages)), key=lambda k: raw[k] - budgets[k])
            budgets[i] += 1
        while sum(budgets) > total:
            i = max(range(len(stages)), key=lambda k: budgets[k])
            if budgets[i] <= (1 if total >= len(stages) else 0):
                break
            budgets[i] -= 1
        return budgets

    def slot(self, turn_number: int) -> Slot:
        """The stage a turn falls in. Turns past the plan stay in the final stage."""
        remaining = max(0, turn_number)
        last_with_budget = max(i for i, b in enumerate(self.budgets) if b > 0) \
            if any(self.budgets) else len(self.stages) - 1
        for stage, budget in zip(self.stages, self.budgets, strict=True):
            if budget == 0:
                continue
            if remaining < budget:
                return Slot(stage, remaining, budget)
            remaining -= budget
        stage = self.stages[last_with_budget]
        return Slot(stage, remaining + self.budgets[last_with_budget] - 1, self.budgets[last_with_budget])

    def plan(self) -> list[dict[str, Any]]:
        out, start = [], 0
        for stage, budget in zip(self.stages, self.budgets, strict=True):
            if budget == 0:
                continue
            out.append({
                "key": stage.key,
                "label": stage.label,
                "start_turn": start,
                "end_turn": start + budget - 1,
                "turns": budget,
                "speakers": [c for c in stage.cycle],
                "note": self.notes.get(stage.key),
            })
            start += budget
        return out

    # ── per-turn decisions ────────────────────────────────────────────────────
    @staticmethod
    def _pick(spec: str, available: set[str]) -> str | None:
        return next((r for r in spec.split("|") if r in available), None)

    def ruling_due(self, last_turn: dict[str, Any] | None, available: set[str]) -> bool:
        """The previous speaker was counsel who objected, and a judge can rule on it."""
        if not last_turn or "judge" not in available:
            return False
        if last_turn.get("role") not in COUNSEL_ROLES:
            return False
        return detect_objection(last_turn.get("content", "")) is not None

    def next_speaker_role(
        self, turn_number: int, last_turn: dict[str, Any] | None, available: set[str]
    ) -> str | None:
        if self.ruling_due(last_turn, available):
            return "judge"
        slot = self.slot(turn_number)
        cycle = slot.stage.cycle
        for offset in range(len(cycle)):
            role = self._pick(cycle[(slot.stage_turn + offset) % len(cycle)], available)
            if role:
                return role
        return None

    def directive(
        self, turn_number: int, role: str, last_turn: dict[str, Any] | None, available: set[str]
    ) -> str:
        slot = self.slot(turn_number)
        header = (
            f"PROCEEDING STAGE: {slot.stage.label} "
            f"(turn {slot.stage_turn + 1} of {slot.budget} in this stage)."
        )
        if self.ruling_due(last_turn, available) and role == "judge":
            ground = (detect_objection(last_turn.get("content", "")) or {}).get("ground")  # type: ignore[union-attr]
            return (
                f"{header}\nCounsel has just objected"
                + (f" ({ground})" if ground else "")
                + ". Rule on it now: say SUSTAINED or OVERRULED, give a one-sentence reason "
                "grounded in the law of evidence, and direct the examination to continue."
            )
        text = slot.stage.directives.get(role) or slot.stage.directives.get("*") \
            or "Take your turn, staying within your role."
        parts = [header, f"Your task now: {text}"]
        note = self.notes.get(slot.stage.key)
        if note:
            parts.append(f"Procedural basis: {note}")
        if slot.stage.key != "judgment":
            parts.append("Do not pronounce a verdict at this stage.")
        return "\n".join(parts)

    def review_turn(
        self, turn_number: int, role: str, content: str, last_turn: dict[str, Any] | None
    ) -> ProcedureReview:
        slot = self.slot(turn_number)
        review = ProcedureReview(stage_key=slot.stage.key, stage_label=slot.stage.label)
        review.objection = detect_objection(content)
        review.ruling = detect_ruling(content) if role == "judge" else None

        if review.objection and role not in COUNSEL_ROLES and role != "judge":
            review.violations.append({
                "code": "objection_by_non_counsel",
                "message": f"A {role} raised an objection; only counsel may object.",
            })

        objection_pending = (
            last_turn is not None
            and last_turn.get("role") in COUNSEL_ROLES
            and detect_objection(last_turn.get("content", "")) is not None
        )
        if objection_pending and role == "judge" and review.ruling is None:
            review.violations.append({
                "code": "ruling_missing",
                "message": "Counsel objected but the judge did not say sustained or overruled.",
            })

        if role == "judge" and slot.stage.key != "judgment" and _VERDICT.search(content):
            review.violations.append({
                "code": "premature_verdict",
                "message": f"A verdict was pronounced during '{slot.stage.label}', before final arguments.",
            })
        if slot.stage.key == "judgment" and role == "judge" and not _VERDICT_WORDS.search(content):
            review.violations.append({
                "code": "verdict_missing",
                "message": "The judgment does not state a clear verdict.",
            })
        return review
