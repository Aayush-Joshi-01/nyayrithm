from __future__ import annotations

from app.ingestion.base import IngestionResult
from app.ingestion.vision import VisionTranscriber, transcribe_image

# A page with fewer extracted characters than this is treated as a scan.
_MIN_TEXT_CHARS = 25
_OCR_DPI = 150
_MAX_OCR_PAGES = 60


class PDFIngester:
    supported_mime_types = ["application/pdf"]

    def __init__(self, transcriber: VisionTranscriber | None = None) -> None:
        self._transcriber = transcriber

    async def ingest(self, file_path: str) -> IngestionResult:
        import pdfplumber

        pages: list[str] = []
        with pdfplumber.open(file_path) as pdf:
            page_count = len(pdf.pages)
            for page in pdf.pages:
                pages.append(page.extract_text() or "")

        # Scanned pages carry no text layer; OCR just those pages.
        scanned = [i for i, t in enumerate(pages) if len(t.strip()) < _MIN_TEXT_CHARS]
        ocr_pages = 0
        ocr_status = "not_needed"
        if scanned:
            ocr_status = "unavailable"
            for i in scanned[:_MAX_OCR_PAGES]:
                png = self._render_page(file_path, i)
                text, status = await transcribe_image(png, "image/png", self._transcriber)
                ocr_status = status
                if text is None:
                    if status == "unavailable":
                        break
                    continue
                pages[i] = text
                ocr_pages += 1

        return IngestionResult(
            raw_text="\n\n".join(pages),
            modality="text",
            metadata={
                "page_count": page_count,
                "source": "pdf",
                "scanned_pages": len(scanned),
                "ocr_pages": ocr_pages,
                "ocr_status": ocr_status,
            },
        )

    @staticmethod
    def _render_page(file_path: str, index: int) -> bytes:
        import fitz  # PyMuPDF

        with fitz.open(file_path) as doc:
            return doc[index].get_pixmap(dpi=_OCR_DPI).tobytes("png")
