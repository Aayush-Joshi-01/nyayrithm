from __future__ import annotations

from app.ingestion.base import EvidenceIngester


def get_ingester(mime_type: str) -> EvidenceIngester:
    """Return the appropriate ingester for the given MIME type."""
    from app.ingestion.pdf import PDFIngester
    from app.ingestion.docx import DOCXIngester
    from app.ingestion.audio import AudioIngester
    from app.ingestion.video import VideoIngester
    from app.ingestion.text import PlainTextIngester
    from app.ingestion.image import ImageIngester

    all_ingesters: list[EvidenceIngester] = [
        PDFIngester(),
        DOCXIngester(),
        AudioIngester(),
        VideoIngester(),
        PlainTextIngester(),
        ImageIngester(),
    ]

    for ingester in all_ingesters:
        if mime_type in ingester.supported_mime_types:
            return ingester

    # Fallback: try plain text
    return PlainTextIngester()


def detect_modality(mime_type: str) -> str:
    if mime_type.startswith("audio/"):
        return "audio"
    if mime_type.startswith("video/"):
        return "video"
    if mime_type.startswith("image/"):
        return "image"
    return "text"
