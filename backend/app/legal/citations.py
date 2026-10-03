"""Find legal citations in free text and check them against a jurisdiction pack.

The checks are deliberately deterministic: language models are most dangerous when they
produce a confident but invented section number or case name, and an LLM judging
another LLM's citations just moves the problem. A rule either finds the provision in
the index, proves it cannot exist (section number beyond the act's last section), or
admits it cannot tell.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Literal

from app.legal.corpus import (
    JurisdictionPack,
    normalise_party_name,
    normalise_reporter,
    normalise_section,
)

Kind = Literal["statute", "constitution", "case"]
Status = Literal["verified", "superseded", "unindexed", "unverified", "mismatch", "nonexistent"]
Severity = Literal["ok", "notice", "warning", "error"]

_SEVERITY: dict[str, Severity] = {
    "verified": "ok",
    "superseded": "notice",
    "unindexed": "notice",
    "unverified": "warning",
    "mismatch": "error",
    "nonexistent": "error",
}


@dataclass
class LegalCitation:
    kind: Kind
    raw: str
    status: Status
    message: str
    ref: str | None = None          # canonical key, e.g. "BNS 103" or "(1978) 1 SCC 248"
    title: str | None = None
    successor: str | None = None    # for repealed provisions, e.g. "BNS 103"
    span: tuple[int, int] = (0, 0)
    severity: Severity = "ok"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["span"] = list(self.span)
        return d


# ── regex construction ────────────────────────────────────────────────────────
_NUM = r"\d+[A-Za-z]{0,2}(?:\s*\(\s*\w+\s*\))*"
_NUMLIST = rf"{_NUM}(?:\s*(?:,|and|&|or|/)\s*{_NUM})*"
_ART_NUM = r"\d+[A-Za-z]{0,3}(?:\s*\(\s*\w+\s*\))*"
_ART_LIST = rf"{_ART_NUM}(?:\s*(?:,|and|&|or)\s*{_ART_NUM})*"
_SEC_KW = r"(?<![A-Za-z])(?:sections?|secs?\.?|ss?\.|u/s\.?|u\.s\.)"

_CASE_WINDOW = 140
_LEADING_FILLER = frozenset({
    "in", "see", "per", "also", "held", "cited", "case", "of", "the", "as", "decision",
    "judgment", "ruling", "reliance", "placed", "on", "and", "by", "vide", "v",
})

_SCC = re.compile(r"\(\s*((?:19|20)\d{2})\s*\)\s*(\d+)\s*SCC\s*(\d+)", re.I)
_AIR = re.compile(r"\bAIR\s*((?:19|20)\d{2})\s*(SC|[A-Z][A-Za-z]{1,5})\s*(\d+)")
_ONLINE = re.compile(r"\b((?:19|20)\d{2})\s*SCC\s*OnLine\s*([A-Za-z]+)\s*(\d+)", re.I)
_PARTY_BEFORE_CITE = re.compile(
    r"([A-Z][\w.&'’\-]*(?:\s+[\w.&'’\-]+){0,6}?)\s+v(?:s?\.|ersus|s)?\s+"
    r"([A-Z][\w.&'’\-]*(?:\s+[\w.&'’\-,]+){0,8}?)\s*[,(\[]*\s*$"
)
_NAMED_CASE = re.compile(
    r"\b([A-Z][\w.&'’\-]+(?:\s+[A-Z][\w.&'’\-]+){0,4})\s+v(?:s?\.|ersus)\s+"
    r"([A-Z][\w.&'’\-]*(?:\s+(?:of\s+|and\s+|the\s+)?[A-Z][\w.&'’\-]*){0,5})"
)


def _alias_pattern(pack: JurisdictionPack, *, acronyms_only: bool) -> str | None:
    names: list[str] = []
    for act in pack.acts.values():
        if act.unit != "Section":
            continue
        for alias in {act.code, act.name.split(",")[0], *act.aliases}:
            is_acronym = " " not in alias and len(alias) <= 6
            if acronyms_only and not is_acronym:
                continue
            names.append(alias)
    if not names:
        return None
    names.sort(key=len, reverse=True)
    escaped = [re.escape(n).replace(r"\ ", r"\s+") for n in names]
    return r"(?<![A-Za-z])(?:" + "|".join(escaped) + r")(?![A-Za-z])"


def _split_numbers(blob: str) -> list[str]:
    return [p.strip() for p in re.split(r"\s*(?:,|and|&|or|/)\s*", blob) if p.strip()]


# ── extraction ────────────────────────────────────────────────────────────────
def _statute_matches(text: str, pack: JurisdictionPack) -> list[tuple[str, str, tuple[int, int], str]]:
    """Yield (act_code, raw_number, span, raw_text) for every statute section cited."""
    found: list[tuple[str, str, tuple[int, int], str]] = []
    taken: list[tuple[int, int]] = []

    def overlaps(span: tuple[int, int]) -> bool:
        return any(span[0] < e and s < span[1] for s, e in taken)

    def collect(match: re.Match[str]) -> None:
        span = match.span()
        if overlaps(span):
            return
        act = pack.find_act(match.group("act"))
        if act is None or act.unit != "Section":
            return
        taken.append(span)
        for num in _split_numbers(match.group("nums")):
            found.append((act.code, num, span, match.group(0)))

    full = _alias_pattern(pack, acronyms_only=False)
    short = _alias_pattern(pack, acronyms_only=True)
    if full is None or short is None:
        return found

    # "Section 302 IPC", "Sections 302 and 34 of the Indian Penal Code"
    section_first = re.compile(
        rf"{_SEC_KW}\s*(?P<nums>{_NUMLIST})\s*,?\s*(?:of\s+(?:the\s+)?|read\s+with\s+)?(?P<act>{full})",
        re.I,
    )
    for m in section_first.finditer(text):
        collect(m)

    # "IPC Section 302", "Indian Penal Code, s. 302"
    act_then_keyword = re.compile(
        rf"(?P<act>{full})\s*,?\s*{_SEC_KW}\s*(?P<nums>{_NUMLIST})", re.I
    )
    for m in act_then_keyword.finditer(text):
        collect(m)

    # "BNS 103" - the bare acronym form; full names are skipped so "Evidence Act 1872"
    # is not read as a section number.
    acronym_number = re.compile(
        rf"(?P<act>{short})\s*(?:§\s*)?(?P<nums>{_NUMLIST})(?![\d/])", re.I
    )
    for m in acronym_number.finditer(text):
        # Require the acronym in its written (upper) form to avoid matching words like "cpc".
        if m.group("act").isupper() or m.group("act") in {"CrPC", "Cr.P.C."}:
            collect(m)
    return found


def _article_matches(text: str, pack: JurisdictionPack) -> list[tuple[str, str, tuple[int, int], str]]:
    article_act = next((a for a in pack.acts.values() if a.unit == "Article"), None)
    if article_act is None:
        return []
    pattern = re.compile(
        rf"(?<![A-Za-z])(?:articles?|arts?\.?)\s*(?P<nums>{_ART_LIST})"
        r"(?:\s+of\s+the\s+(?:Indian\s+)?Constitution(?:\s+of\s+India)?)?",
        re.I,
    )
    out = []
    for m in pattern.finditer(text):
        for num in _split_numbers(m.group("nums")):
            out.append((article_act.code, num, m.span(), m.group(0)))
    return out


def _case_cite_matches(text: str) -> list[tuple[str, str, tuple[int, int], str | None]]:
    """(canonical_cite, kind, span, party_name_before_cite) for each reporter citation."""
    out: list[tuple[str, str, tuple[int, int], str | None]] = []
    for rx, fmt in (
        (_SCC, lambda m: f"({m.group(1)}) {m.group(2)} SCC {m.group(3)}"),
        (_AIR, lambda m: f"AIR {m.group(1)} {m.group(2)} {m.group(3)}"),
        (_ONLINE, lambda m: f"{m.group(1)} SCC OnLine {m.group(2)} {m.group(3)}"),
    ):
        for m in rx.finditer(text):
            window = text[max(0, m.start() - _CASE_WINDOW): m.start()]
            party = _PARTY_BEFORE_CITE.search(window)
            name = None
            if party:
                left = party.group(1).split()
                while left and left[0].lower().strip(",.") in _LEADING_FILLER:
                    left.pop(0)
                if left:
                    name = f"{' '.join(left)} v. {party.group(2).strip(' ,')}"
            out.append((fmt(m), "reporter", m.span(), name))
    return out


# ── verification ──────────────────────────────────────────────────────────────
def _statute_citation(
    pack: JurisdictionPack, act_code: str, raw_num: str, span: tuple[int, int], raw: str
) -> LegalCitation:
    act = pack.acts[act_code]
    number = normalise_section(raw_num)
    digits = int(re.match(r"\d+", number).group(0))  # type: ignore[union-attr]
    label = f"{act.code} {number}"

    if act.max_section is not None and digits > act.max_section or digits == 0:
        return _make(
            "statute", raw, "nonexistent", span, ref=label,
            message=f"{act.name} has no {act.unit.lower()} {number}; it ends at {act.max_section}.",
        )

    provision = pack.provision(act_code, number)
    successor = pack.successor_of(act_code, number) if act.superseded_by_act else None
    if act.superseded_by_act:
        succ_prov = None
        if successor:
            succ_act, succ_num = successor.split(" ", 1)
            succ_prov = pack.provision(succ_act, succ_num)
        when = act.repealed or "2024-07-01"
        msg = f"{act.code} was repealed with effect from {when}; it still governs earlier conduct."
        if successor:
            msg += f" The corresponding current provision is {successor}"
            msg += f" ({succ_prov.title})." if succ_prov else "."
        return _make(
            "statute", raw, "superseded", span, ref=label, successor=successor,
            title=succ_prov.title if succ_prov else None, message=msg,
        )

    if provision:
        return _make("statute", raw, "verified", span, ref=label, title=provision.title,
                     message=f"{label}: {provision.title}.")
    return _make(
        "statute", raw, "unindexed", span, ref=label,
        message=f"{label} is within the act's range but is not in the reference index; verify the text.",
    )


def _constitution_citation(
    pack: JurisdictionPack, act_code: str, raw_num: str, span: tuple[int, int], raw: str
) -> LegalCitation:
    act = pack.acts[act_code]
    number = normalise_section(raw_num)
    digits = int(re.match(r"\d+", number).group(0))  # type: ignore[union-attr]
    label = f"{act.code} Article {number}"
    if act.max_section is not None and digits > act.max_section or digits == 0:
        return _make("constitution", raw, "nonexistent", span, ref=label,
                     message=f"The {act.name} has no Article {number}; it ends at {act.max_section}.")
    provision = pack.provision(act_code, number)
    if provision:
        return _make("constitution", raw, "verified", span, ref=label, title=provision.title,
                     message=f"Article {number}: {provision.title}.")
    return _make("constitution", raw, "unindexed", span, ref=label,
                 message=f"Article {number} is not in the reference index; verify the text.")


def _case_citation(
    pack: JurisdictionPack, cite: str, span: tuple[int, int], name: str | None
) -> LegalCitation:
    record = pack.find_case_by_citation(cite)
    raw = f"{name} {cite}" if name else cite
    if record is None:
        who = f"{name} " if name else ""
        return _make("case", raw, "unverified", span, ref=cite,
                     message=f"{who}{cite} is not in the reference index. Confirm that the case "
                             "exists and says what is claimed before relying on it.")
    if name:
        claimed = normalise_party_name(name).split(" v ")[0]
        actual = normalise_party_name(record.name).split(" v ")[0]
        if claimed and actual and claimed not in actual and actual not in claimed:
            return _make("case", raw, "mismatch", span, ref=cite, title=record.name,
                         message=f"{cite} is {record.name}, not {name}.")
    return _make("case", raw, "verified", span, ref=cite, title=record.name,
                 message=f"{record.name}, {cite} ({record.court}, {record.year}).")


def _case_name_only(pack: JurisdictionPack, name: str, span: tuple[int, int]) -> LegalCitation:
    record = pack.find_case_by_name(name)
    if record:
        return _make("case", name, "verified", span, ref=record.citations[0] if record.citations else None,
                     title=record.name, message=f"{record.name} ({record.court}, {record.year}).")
    return _make("case", name, "unverified", span,
                 message=f"No case named '{name}' is in the reference index. Confirm that it exists "
                         "and that it supports the proposition.")


def _make(kind: Kind, raw: str, status: Status, span: tuple[int, int], **kw: Any) -> LegalCitation:
    return LegalCitation(kind=kind, raw=raw.strip(), status=status, span=span,
                         severity=_SEVERITY[status], **kw)


def extract_and_verify(text: str, pack: JurisdictionPack) -> list[LegalCitation]:
    """All legal citations in ``text`` with a verification verdict each, in text order."""
    results: list[LegalCitation] = []
    seen: set[tuple[Any, ...]] = set()

    def add(c: LegalCitation, key: tuple[Any, ...]) -> None:
        if key not in seen:
            seen.add(key)
            results.append(c)

    for act_code, num, span, raw in _statute_matches(text, pack):
        add(_statute_citation(pack, act_code, num, span, raw),
            ("statute", act_code, normalise_section(num)))

    for act_code, num, span, raw in _article_matches(text, pack):
        add(_constitution_citation(pack, act_code, num, span, raw),
            ("article", act_code, normalise_section(num)))

    cite_spans: list[tuple[int, int]] = []
    for cite, _kind, span, name in _case_cite_matches(text):
        cite_spans.append((max(0, span[0] - _CASE_WINDOW), span[1]))
        add(_case_citation(pack, cite, span, name), ("case", normalise_reporter(cite)))

    for m in _NAMED_CASE.finditer(text):
        if any(s <= m.start() < e for s, e in cite_spans):
            continue  # already judged through its reporter citation
        name = f"{m.group(1).strip()} v. {m.group(2).strip(' ,')}"
        add(_case_name_only(pack, name, m.span()), ("casename", normalise_party_name(name)))

    results.sort(key=lambda c: c.span[0])
    return results
