from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


CITATION_PATTERN = re.compile(r"\[EVIDENCE:([a-f0-9\-]+):(\d+)\]")


@dataclass
class ParsedCitation:
    evidence_id: str
    chunk_index: int
    raw: str


def parse_citations(text: str) -> list[ParsedCitation]:
    """Extract [EVIDENCE:uuid:chunk_index] markers from agent output."""
    matches = CITATION_PATTERN.findall(text)
    seen = set()
    citations = []
    for evidence_id, chunk_idx in matches:
        key = (evidence_id, int(chunk_idx))
        if key not in seen:
            seen.add(key)
            citations.append(ParsedCitation(
                evidence_id=evidence_id,
                chunk_index=int(chunk_idx),
                raw=f"[EVIDENCE:{evidence_id}:{chunk_idx}]",
            ))
    return citations


def strip_citations(text: str) -> str:
    """Remove citation markers from text for clean display."""
    return CITATION_PATTERN.sub("", text).strip()


def build_citation_dict(
    citation: ParsedCitation,
    chunk_text: str,
    evidence_title: str,
    score: float = 1.0,
    modality: str = "text",
) -> dict[str, Any]:
    return {
        "evidence_id": citation.evidence_id,
        "chunk_index": citation.chunk_index,
        "chunk_text": chunk_text[:500],  # truncate for storage
        "evidence_title": evidence_title,
        "score": score,
        "modality": modality,
    }
