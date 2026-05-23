from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass
class CaseMemoryEntry:
    turn_id: str
    content: str
    evidence_refs: list[str]
    summary: str = ""


class CaseMemory:
    """
    Persistent memory linked to the case and agent.
    In production this is stored in the DB and retrieved semantically.
    For now uses an in-memory list with simple keyword matching.
    """

    def __init__(self, case_id: UUID, agent_id: UUID) -> None:
        self.case_id = case_id
        self.agent_id = agent_id
        self._entries: list[CaseMemoryEntry] = []

    async def remember_statement(
        self,
        turn_id: str,
        content: str,
        evidence_refs: list[str] | None = None,
    ) -> None:
        self._entries.append(CaseMemoryEntry(
            turn_id=turn_id,
            content=content,
            evidence_refs=evidence_refs or [],
            summary=content[:150],
        ))

    async def recall_relevant(self, query: str, top_k: int = 5) -> list[CaseMemoryEntry]:
        """Simple keyword recall. Replace with semantic search in production."""
        query_words = set(query.lower().split())
        scored = []
        for entry in self._entries:
            entry_words = set(entry.content.lower().split())
            overlap = len(query_words & entry_words)
            scored.append((overlap, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:top_k]]

    async def has_stated(self, claim: str) -> bool:
        """Check if this agent has made a similar claim before."""
        claim_words = set(claim.lower().split())
        for entry in self._entries:
            entry_words = set(entry.content.lower().split())
            if len(claim_words & entry_words) / max(len(claim_words), 1) > 0.7:
                return True
        return False

    def prior_statements_summary(self) -> str:
        if not self._entries:
            return ""
        return "\n".join(f"- {e.summary}" for e in self._entries[-5:])

    def clear(self) -> None:
        self._entries.clear()
