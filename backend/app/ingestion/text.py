from __future__ import annotations

from app.ingestion.base import IngestionResult


class PlainTextIngester:
    supported_mime_types = ["text/plain", "text/markdown", "text/csv"]

    async def ingest(self, file_path: str) -> IngestionResult:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return IngestionResult(
            raw_text=content,
            modality="text",
            metadata={"char_count": len(content), "source": "text"},
        )
