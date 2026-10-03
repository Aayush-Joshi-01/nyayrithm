from __future__ import annotations

from app.ingestion.base import IngestionResult
from app.ingestion.vision import VisionTranscriber, transcribe_image


class ImageIngester:
    supported_mime_types = [
        "image/jpeg", "image/png", "image/tiff", "image/bmp", "image/webp", "image/gif",
    ]

    def __init__(self, transcriber: VisionTranscriber | None = None) -> None:
        self._transcriber = transcriber

    async def ingest(self, file_path: str) -> IngestionResult:
        from PIL import Image

        with Image.open(file_path) as img:
            meta = {
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "mode": img.mode,
                "source": "image",
            }

        with open(file_path, "rb") as fh:
            raw = fh.read()
        text, status = await transcribe_image(raw, f"image/{(meta['format'] or 'png').lower()}",
                                              self._transcriber)
        meta["ocr_status"] = status

        if text is None:
            # Keep the evidence indexable and searchable by its existence even when no
            # vision provider is configured; ocr_status tells the UI why it is thin.
            text = (
                f"[Image evidence: {meta['width']}x{meta['height']} {meta['format']}; "
                "text not extracted]"
            )
        return IngestionResult(raw_text=text, transcription=text, modality="image", metadata=meta)
