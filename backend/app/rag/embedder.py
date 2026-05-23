from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Embedder(Protocol):
    """
    Modality-aware embedding interface.
    Implementations: openai, anthropic, cohere, gemini, sentence-transformers, local.
    """

    modalities: list[str]
    dimension: int

    async def embed_text(self, text: str) -> list[float]: ...

    async def embed_image(self, image_bytes: bytes) -> list[float]: ...

    async def embed_audio(self, audio_bytes: bytes) -> list[float]: ...

    async def embed_multimodal(self, inputs: dict) -> list[float]: ...


class OpenAIEmbedder:
    modalities = ["text"]
    dimension = 1536

    def __init__(self, model: str = "text-embedding-3-small", api_key: str = "") -> None:
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model
        # Update dimension for large model
        if "large" in model:
            self.dimension = 3072

    async def embed_text(self, text: str) -> list[float]:
        response = await self._client.embeddings.create(
            model=self._model,
            input=text,
        )
        return response.data[0].embedding

    async def embed_image(self, image_bytes: bytes) -> list[float]:
        raise NotImplementedError("Use OpenAIVisionEmbedder for image embeddings")

    async def embed_audio(self, audio_bytes: bytes) -> list[float]:
        raise NotImplementedError("Transcribe audio first, then embed as text")

    async def embed_multimodal(self, inputs: dict) -> list[float]:
        # Fallback: embed text component only
        return await self.embed_text(inputs.get("text", ""))


class SentenceTransformerEmbedder:
    """Local embedder — no API key needed. Good for offline/air-gapped deployments."""

    modalities = ["text"]
    dimension = 384  # all-MiniLM-L6-v2 default

    def __init__(self, model: str = "all-MiniLM-L6-v2") -> None:
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(model)
        self.dimension = self._model.get_sentence_embedding_dimension()

    async def embed_text(self, text: str) -> list[float]:
        import asyncio
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(None, self._model.encode, text)
        return embedding.tolist()

    async def embed_image(self, image_bytes: bytes) -> list[float]:
        raise NotImplementedError("Use a multimodal model for image embeddings")

    async def embed_audio(self, audio_bytes: bytes) -> list[float]:
        raise NotImplementedError("Transcribe audio first")

    async def embed_multimodal(self, inputs: dict) -> list[float]:
        return await self.embed_text(inputs.get("text", ""))
