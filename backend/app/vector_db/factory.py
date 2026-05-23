from __future__ import annotations

from functools import lru_cache

from app.config import get_settings
from app.vector_db.base import VectorStore


@lru_cache
def get_vector_store() -> VectorStore:
    settings = get_settings()
    backend = settings.VECTOR_DB_BACKEND

    if backend == "qdrant":
        from app.vector_db.qdrant import QdrantVectorStore
        return QdrantVectorStore(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)

    if backend == "chroma":
        from app.vector_db.chroma import ChromaVectorStore
        return ChromaVectorStore(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)

    raise NotImplementedError(f"Vector DB backend '{backend}' not implemented. "
                              f"Add a class to app/vector_db/ and register it here.")
