from __future__ import annotations

from app.ingestion.base import IngestionResult


class DOCXIngester:
    supported_mime_types = [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ]

    async def ingest(self, file_path: str) -> IngestionResult:
        from docx import Document
        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        full_text = "\n\n".join(paragraphs)
        return IngestionResult(
            raw_text=full_text,
            modality="text",
            metadata={"paragraph_count": len(paragraphs), "source": "docx"},
        )
