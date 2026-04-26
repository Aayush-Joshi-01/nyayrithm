from __future__ import annotations

from app.ingestion.base import IngestionResult


class PDFIngester:
    supported_mime_types = ["application/pdf"]

    async def ingest(self, file_path: str) -> IngestionResult:
        import pdfplumber
        pages = []
        page_count = 0

        with pdfplumber.open(file_path) as pdf:
            page_count = len(pdf.pages)
            for page in pdf.pages:
                text = page.extract_text() or ""
                pages.append(text)

        full_text = "\n\n".join(pages)
        return IngestionResult(
            raw_text=full_text,
            modality="text",
            metadata={"page_count": page_count, "source": "pdf"},
        )
