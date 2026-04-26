from __future__ import annotations

from functools import lru_cache

from app.config import get_settings
from app.rag.embedder import Embedder


@lru_cache
def get_embedder() -> Embedder:
    settings = get_settings()
    backend = settings.EMBEDDER_BACKEND

    if backend == "openai":
        from app.rag.embedder import OpenAIEmbedder
        return OpenAIEmbedder(api_key=settings.OPENAI_API_KEY or "")

    if backend in ("sentence-transformers", "local"):
        from app.rag.embedder import SentenceTransformerEmbedder
        return SentenceTransformerEmbedder()

    raise NotImplementedError(
        f"Embedder backend '{backend}' not implemented. "
        "Add a class to app/rag/embedder.py and register it here."
    )


def get_embedder_for_modality(modality: str, mime_type: str) -> Embedder:
    """Route to the appropriate embedder based on evidence modality."""
    settings = get_settings()
    backend = settings.EMBEDDER_BACKEND

    # For text-only backends, always return the text embedder
    # Multimodal routing can be extended here
    return get_embedder()
