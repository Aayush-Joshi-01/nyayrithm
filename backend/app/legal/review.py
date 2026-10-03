"""Per-turn legal review: verify citations and build the 'applicable law' prompt context."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.legal.citations import LegalCitation, extract_and_verify
from app.legal.corpus import JurisdictionPack, LegalCorpus, get_corpus


@dataclass
class LegalReview:
    pack_id: str | None
    status: str  # clean | notices | flagged | no_pack
    citations: list[LegalCitation] = field(default_factory=list)

    @property
    def flagged(self) -> list[LegalCitation]:
        return [c for c in self.citations if c.severity in ("warning", "error")]

    @property
    def errors(self) -> list[LegalCitation]:
        return [c for c in self.citations if c.severity == "error"]

    def to_dict(self) -> dict[str, Any]:
        counts: dict[str, int] = {}
        for c in self.citations:
            counts[c.status] = counts.get(c.status, 0) + 1
        return {
            "pack_id": self.pack_id,
            "status": self.status,
            "counts": counts,
            "citations": [c.to_dict() for c in self.citations],
        }

    def correction_note(self) -> str:
        """Feedback for the agent's next turn when it cited law that cannot be right."""
        bad = self.errors
        if not bad:
            return ""
        lines = [f"- {c.raw}: {c.message}" for c in bad]
        return (
            "CORRECTION FROM THE COURT REGISTRY: authorities cited in your previous turn "
            "could not be verified as stated:\n" + "\n".join(lines) +
            "\nDo not repeat them. Cite only provisions and cases you are certain exist, "
            "or argue from the evidence without citing authority."
        )


def correction_note_from(review: dict[str, Any] | None) -> str:
    """Feedback for an agent's next turn when it cited law that cannot be right.

    Takes the serialised review (as stored on the turn) so it works on rehydrated history.
    """
    bad = [c for c in (review or {}).get("citations", []) if c.get("severity") == "error"]
    if not bad:
        return ""
    lines = [f"- {c['raw']}: {c['message']}" for c in bad]
    return (
        "CORRECTION FROM THE COURT REGISTRY: authorities cited in your previous turn "
        "could not be verified as stated:\n" + "\n".join(lines) +
        "\nDo not repeat them. Cite only provisions and cases you are certain exist, "
        "or argue from the evidence without citing authority."
    )


class LegalReviewer:
    def __init__(self, corpus: LegalCorpus | None = None) -> None:
        self.corpus = corpus or get_corpus()

    def pack_for(self, country: str | None, jurisdiction: str | None = None) -> JurisdictionPack | None:
        return self.corpus.resolve(country, jurisdiction)

    def review(self, text: str, country: str | None, jurisdiction: str | None = None) -> LegalReview:
        pack = self.pack_for(country, jurisdiction)
        if pack is None:
            return LegalReview(pack_id=None, status="no_pack")
        citations = extract_and_verify(text, pack)
        if any(c.severity in ("warning", "error") for c in citations):
            status = "flagged"
        elif any(c.severity == "notice" for c in citations):
            status = "notices"
        else:
            status = "clean"
        return LegalReview(pack_id=pack.id, status=status, citations=citations)

    def context_for(
        self, query: str, country: str | None, jurisdiction: str | None = None, limit: int = 6
    ) -> tuple[str, list[str]]:
        """A compact 'applicable law' block for the prompt, and the refs it contains."""
        pack = self.pack_for(country, jurisdiction)
        if pack is None:
            return "", []
        provisions = pack.search(query, limit=limit)
        cases = pack.search_cases(query, limit=2)
        if not provisions and not cases:
            return "", []
        lines = ["Reference index of the law in force (paraphrased; verify before quoting):"]
        refs: list[str] = []
        for p in provisions:
            lines.append(f"- {p.ref} — {p.title}: {p.summary}")
            refs.append(p.ref)
        for c in cases:
            cite = c.citations[0] if c.citations else ""
            lines.append(f"- {c.name}, {cite} ({c.court}, {c.year}): {c.holding}")
            refs.append(cite or c.name)
        lines.extend(f"- {note}" for note in pack.prompt_notes)
        return "\n".join(lines), refs
