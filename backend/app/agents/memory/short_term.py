from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any

from app.llm.base import LLMMessage


@dataclass
class MemoryEntry:
    perceived_query: str
    response_content: str
    citations: list[dict[str, Any]]
    turn_number: int


class ShortTermMemory:
    """
    Sliding-window in-process memory of the last N turns this agent responded in.
    Reset when the simulation restarts.
    """

    def __init__(self, window_size: int = 20) -> None:
        self.window_size = window_size
        self._entries: deque[MemoryEntry] = deque(maxlen=window_size)

    def record(self, perceived, response) -> None:
        self._entries.append(MemoryEntry(
            perceived_query=perceived.query,
            response_content=response.content,
            citations=response.citations,
            turn_number=getattr(perceived, "turn_number", 0),
        ))

    def as_messages(self) -> list[LLMMessage]:
        """Format memory as assistant message history for LLM prompt."""
        messages = []
        for entry in self._entries:
            messages.append(LLMMessage(role="assistant", content=entry.response_content))
        return messages

    def prior_statements_summary(self) -> str:
        if not self._entries:
            return ""
        summaries = []
        for i, e in enumerate(self._entries, 1):
            snippet = e.response_content[:200].replace("\n", " ")
            summaries.append(f"[Statement {i}]: {snippet}...")
        return "\n".join(summaries)

    def clear(self) -> None:
        self._entries.clear()

    def __len__(self) -> int:
        return len(self._entries)
