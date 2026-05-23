from __future__ import annotations

from app.ingestion.base import IngestionResult


class ImageIngester:
    supported_mime_types = ["image/jpeg", "image/png", "image/tiff", "image/bmp", "image/webp"]

    async def ingest(self, file_path: str) -> IngestionResult:
        from PIL import Image
        import io
        img = Image.open(file_path)
        meta = {
            "width": img.width,
            "height": img.height,
            "format": img.format,
            "mode": img.mode,
            "source": "image",
        }
        # For now, produce a placeholder text. In production, use OCR or vision model.
        raw_text = f"[Image evidence: {img.width}x{img.height} {img.format}]"
        return IngestionResult(
            raw_text=raw_text,
            modality="image",
            metadata=meta,
        )
