from __future__ import annotations

from typing import Any
from uuid import UUID

from app.agents.memory.short_term import ShortTermMemory
from app.agents.memory.case_memory import CaseMemory
from app.llm.base import LLMMessage


class CombinedAgentMemory:
    """
    Combines short-term (session) and case-level (persistent) memory.
    This is the object passed to BaseAgent as `memory`.
    """

    def __init__(self, case_id: UUID, agent_id: UUID, window_size: int = 20) -> None:
        self.short_term = ShortTermMemory(window_size=window_size)
        self.case_mem = CaseMemory(case_id=case_id, agent_id=agent_id)

    def record(self, perceived: Any, response: Any) -> None:
        self.short_term.record(perceived, response)

    def as_messages(self) -> list[LLMMessage]:
        return self.short_term.as_messages()

    def prior_statements_summary(self) -> str:
        return self.short_term.prior_statements_summary()

    async def persist_turn(self, turn_id: str, content: str, evidence_refs: list[str]) -> None:
        await self.case_mem.remember_statement(turn_id, content, evidence_refs)

    def clear(self) -> None:
        self.short_term.clear()
        self.case_mem.clear()
