from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class TextChunk:
    text: str
    index: int
    metadata: dict[str, Any]


def _split_by_tokens_approx(text: str, max_tokens: int, overlap: int) -> list[str]:
    """Approximate token-based split (4 chars ≈ 1 token)."""
    char_limit = max_tokens * 4
    overlap_chars = overlap * 4
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + char_limit, len(text))
        chunks.append(text[start:end])
        start = end - overlap_chars
        if start >= end:
            break
    return chunks


class RecursiveTextChunker:
    """Splits text recursively on paragraph → sentence → word boundaries."""

    separators = ["\n\n", "\n", ". ", "! ", "? ", " "]

    def __init__(self, max_tokens: int = 512, overlap: int = 50) -> None:
        self.max_tokens = max_tokens
        self.overlap = overlap
        self._char_limit = max_tokens * 4

    def chunk(self, text: str, base_metadata: dict | None = None) -> list[TextChunk]:
        meta = base_metadata or {}
        raw_chunks = self._split(text)
        return [
            TextChunk(text=c, index=i, metadata={**meta, "chunk_index": i})
            for i, c in enumerate(raw_chunks)
            if c.strip()
        ]

    def _split(self, text: str) -> list[str]:
        if len(text) <= self._char_limit:
            return [text]

        for sep in self.separators:
            parts = text.split(sep)
            if len(parts) > 1:
                return self._merge_parts(parts, sep)

        return _split_by_tokens_approx(text, self.max_tokens, self.overlap)

    def _merge_parts(self, parts: list[str], sep: str) -> list[str]:
        chunks = []
        current = ""
        for part in parts:
            candidate = current + sep + part if current else part
            if len(candidate) <= self._char_limit:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                if len(part) > self._char_limit:
                    chunks.extend(self._split(part))
                    current = ""
                else:
                    current = part
        if current:
            chunks.append(current)
        return chunks


class TimeWindowChunker:
    """For audio/video: splits transcript into fixed time windows."""

    def __init__(self, window_seconds: int = 30, overlap_seconds: int = 5) -> None:
        self.window = window_seconds
        self.overlap = overlap_seconds

    def chunk(self, segments: list[dict], base_metadata: dict | None = None) -> list[TextChunk]:
        """
        segments: list of {start, end, text} dicts (from Whisper output)
        """
        meta = base_metadata or {}
        if not segments:
            return []

        chunks = []
        chunk_idx = 0
        i = 0

        while i < len(segments):
            start_time = segments[i]["start"]
            end_time = start_time + self.window
            texts = []
            j = i
            while j < len(segments) and segments[j]["start"] < end_time:
                texts.append(segments[j]["text"])
                j += 1

            chunk_text = " ".join(texts).strip()
            if chunk_text:
                chunks.append(TextChunk(
                    text=chunk_text,
                    index=chunk_idx,
                    metadata={
                        **meta,
                        "chunk_index": chunk_idx,
                        "start_time": start_time,
                        "end_time": segments[j - 1]["end"] if j > i else end_time,
                    }
                ))
                chunk_idx += 1

            # Advance with overlap
            overlap_start = end_time - self.overlap
            while i < len(segments) and segments[i]["start"] < overlap_start:
                i += 1
            if i >= j:
                i = j  # prevent infinite loop

        return chunks
