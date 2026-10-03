"""Jurisdiction packs: the reference index agents and the citation verifier rely on.

A pack lists a jurisdiction's acts (with their highest valid section number), an index
of provisions and landmark cases, and a concordance from repealed to current law. It is
deliberately an *index with paraphrased summaries*, not a copy of the statutes: the
verifier answers "does this provision / case exist, and does the citation match?", and
never claims more than the pack knows.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import structlog

from app.config import get_settings

logger = structlog.get_logger()

PACKS_DIR = Path(__file__).parent / "packs"


@dataclass(frozen=True)
class Act:
    code: str
    name: str
    aliases: tuple[str, ...]
    unit: str = "Section"
    max_section: int | None = None
    in_force: str | None = None
    repealed: str | None = None
    superseded_by_act: str | None = None
    replaces_act: str | None = None


@dataclass(frozen=True)
class Provision:
    act: str
    section: str
    title: str
    summary: str
    replaces: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()

    @property
    def ref(self) -> str:
        return f"{self.act} {self.section}"


@dataclass(frozen=True)
class CaseRecord:
    name: str
    citations: tuple[str, ...]
    court: str
    year: int
    holding: str
    keywords: tuple[str, ...] = ()


@dataclass
class JurisdictionPack:
    id: str
    name: str
    country_aliases: tuple[str, ...]
    legal_system: str
    status: str
    notice: str
    prompt_notes: tuple[str, ...] = ()
    procedure_notes: dict[str, str] = field(default_factory=dict)
    acts: dict[str, Act] = field(default_factory=dict)
    provisions: dict[str, Provision] = field(default_factory=dict)  # key: "BNS 103"
    concordance: dict[str, str] = field(default_factory=dict)       # "IPC 302" -> "BNS 103"
    cases: list[CaseRecord] = field(default_factory=list)

    # ── lookups ───────────────────────────────────────────────────────────────
    def find_act(self, name: str) -> Act | None:
        needle = _norm_act(name)
        for act in self.acts.values():
            if needle == _norm_act(act.code) or needle in {_norm_act(a) for a in act.aliases} \
                    or needle == _norm_act(act.name):
                return act
        return None

    def provision(self, act_code: str, section: str) -> Provision | None:
        return self.provisions.get(f"{act_code} {normalise_section(section)}")

    def successor_of(self, act_code: str, section: str) -> str | None:
        return self.concordance.get(f"{act_code} {normalise_section(section)}")

    def find_case_by_citation(self, citation: str) -> CaseRecord | None:
        key = normalise_reporter(citation)
        for c in self.cases:
            if key in {normalise_reporter(x) for x in c.citations}:
                return c
        return None

    def find_case_by_name(self, name: str) -> CaseRecord | None:
        key = normalise_party_name(name)
        if not key:
            return None
        for c in self.cases:
            if normalise_party_name(c.name) == key:
                return c
        # Tolerate a missing "State of" / "Union of India" style tail: match on the lead party.
        lead = key.split(" v ")[0]
        for c in self.cases:
            if normalise_party_name(c.name).split(" v ")[0] == lead and len(lead) > 6:
                return c
        return None

    def search(self, query: str, limit: int = 6) -> list[Provision]:
        """Keyword search over provision titles, summaries and keywords."""
        tokens = {t for t in re.findall(r"[a-z0-9]{3,}", query.lower()) if t not in _STOPWORDS}
        if not tokens:
            return []
        scored: list[tuple[float, Provision]] = []
        for p in self.provisions.values():
            haystack_title = p.title.lower()
            haystack = f"{haystack_title} {p.summary.lower()}"
            score = 0.0
            for kw in p.keywords:
                if kw.lower() in query.lower():
                    score += 3.0
            for t in tokens:
                if t in haystack_title:
                    score += 2.0
                elif t in haystack:
                    score += 0.5
            if score >= 3.0:
                scored.append((score, p))
        scored.sort(key=lambda sp: (-sp[0], sp[1].ref))
        return [p for _, p in scored[:limit]]

    def search_cases(self, query: str, limit: int = 3) -> list[CaseRecord]:
        q = query.lower()
        hits: list[tuple[int, CaseRecord]] = []
        for c in self.cases:
            score = sum(3 for kw in c.keywords if kw.lower() in q)
            if score:
                hits.append((score, c))
        hits.sort(key=lambda sc: -sc[0])
        return [c for _, c in hits[:limit]]

    def summary(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "notice": self.notice,
            "acts": [{"code": a.code, "name": a.name, "repealed": a.repealed} for a in self.acts.values()],
            "provision_count": len(self.provisions),
            "case_count": len(self.cases),
        }


_STOPWORDS = frozenset({
    "the", "and", "for", "that", "with", "this", "from", "was", "were", "which", "not", "are",
    "has", "had", "have", "his", "her", "its", "any", "under", "into", "case", "court",
    "evidence", "witness", "accused", "state", "section", "act",
})


# ── normalisation helpers (shared with the citation extractor) ────────────────
def _norm_act(s: str) -> str:
    return re.sub(r"[^a-z]", "", s.lower().replace("the ", ""))


def normalise_section(section: str) -> str:
    """'65b(4)(a)' -> '65B'; sub-sections never change which section is meant."""
    base = re.match(r"\s*(\d+)\s*([A-Za-z]{0,2})", section)
    if not base:
        return section.strip().upper()
    return f"{int(base.group(1))}{base.group(2).upper()}"


def normalise_reporter(citation: str) -> str:
    return re.sub(r"[\s.,]", "", citation.lower())


def normalise_party_name(name: str) -> str:
    n = name.lower()
    n = re.sub(r"\bversus\b|\bvs?\b\.?", " v ", n)
    n = re.sub(r"[^a-z0-9 ]", " ", n)
    n = re.sub(r"\b(the|of|and|ors|anr|others|another|retd)\b", " ", n)
    return re.sub(r"\s+", " ", n).strip()


# ── loading ───────────────────────────────────────────────────────────────────
def load_pack(path: Path) -> JurisdictionPack:
    raw = json.loads(path.read_text(encoding="utf-8"))
    pack = JurisdictionPack(
        id=raw["id"],
        name=raw["name"],
        country_aliases=tuple(a.lower() for a in raw.get("country_aliases", [])),
        legal_system=raw.get("legal_system", "common_law"),
        status=raw.get("status", "custom"),
        notice=raw.get("notice", ""),
        prompt_notes=tuple(raw.get("prompt_notes", [])),
        procedure_notes=dict(raw.get("procedure_notes", {})),
    )
    for a in raw.get("acts", []):
        act = Act(
            code=a["code"], name=a["name"], aliases=tuple(a.get("aliases", [])),
            unit=a.get("unit", "Section"), max_section=a.get("max_section"),
            in_force=a.get("in_force"), repealed=a.get("repealed"),
            superseded_by_act=a.get("superseded_by_act"), replaces_act=a.get("replaces_act"),
        )
        pack.acts[act.code] = act
    for p in raw.get("provisions", []):
        prov = Provision(
            act=p["act"], section=normalise_section(p["section"]), title=p["title"],
            summary=p["summary"], replaces=tuple(p.get("replaces", [])),
            keywords=tuple(p.get("keywords", [])),
        )
        pack.provisions[prov.ref] = prov
    for c in raw.get("concordance", []):
        old_act, old_sec = c["old"].split(" ", 1)
        pack.concordance[f"{old_act} {normalise_section(old_sec)}"] = c["new"]
    for c in raw.get("cases", []):
        pack.cases.append(CaseRecord(
            name=c["name"], citations=tuple(c.get("citations", [])), court=c.get("court", ""),
            year=int(c.get("year", 0)), holding=c.get("holding", ""),
            keywords=tuple(c.get("keywords", [])),
        ))
    return pack


class LegalCorpus:
    def __init__(self, packs: list[JurisdictionPack]) -> None:
        self.packs = {p.id: p for p in packs}

    def resolve(self, country: str | None, jurisdiction: str | None = None) -> JurisdictionPack | None:
        """Pick the pack for a case from its country (and, failing that, jurisdiction) text."""
        for text in (country, jurisdiction):
            needle = (text or "").strip().lower()
            if not needle:
                continue
            for pack in self.packs.values():
                if needle == pack.id.lower() or needle in pack.country_aliases:
                    return pack
        return None

    def get(self, pack_id: str) -> JurisdictionPack | None:
        return self.packs.get(pack_id.upper())

    def list(self) -> list[dict[str, Any]]:
        return [p.summary() for p in self.packs.values()]


@lru_cache
def get_corpus() -> LegalCorpus:
    paths = sorted(PACKS_DIR.glob("*.json"))
    extra = get_settings().LEGAL_PACKS_DIR
    if extra:
        paths += sorted(Path(extra).glob("*.json"))
    packs: list[JurisdictionPack] = []
    for path in paths:
        try:
            packs.append(load_pack(path))
        except (OSError, ValueError, KeyError) as exc:
            # A broken pack must not take the app down; the others stay usable.
            logger.error("legal_pack_load_failed", path=str(path), error=str(exc))
    return LegalCorpus(packs)
