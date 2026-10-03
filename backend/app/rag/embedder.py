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


class UnsupportedModalityError(ValueError):
    """Raised when an embedder is asked for a modality it cannot represent."""


class TextEmbeddingMixin:
    """Gives text-only embedders sane image / audio / multimodal behaviour.

    Evidence is embedded as *text*: images are transcribed by a vision model and audio
    is transcribed during ingestion, so the embedder only ever sees their transcript.
    """

    async def embed_image(self, image_bytes: bytes) -> list[float]:
        from app.ingestion.vision import transcribe_image

        text, status = await transcribe_image(image_bytes, "image/png")
        if not text:
            raise UnsupportedModalityError(
                f"Could not turn the image into text (vision status: {status}); "
                "configure a vision-capable provider API key."
            )
        return await self.embed_text(text)  # type: ignore[attr-defined]

    async def embed_audio(self, audio_bytes: bytes) -> list[float]:
        raise UnsupportedModalityError(
            "Audio is transcribed during ingestion; embed the transcript with embed_text()."
        )

    async def embed_multimodal(self, inputs: dict) -> list[float]:
        """Embed the text component, falling back to a transcribed image."""
        if inputs.get("text"):
            return await self.embed_text(inputs["text"])  # type: ignore[attr-defined]
        if inputs.get("image"):
            return await self.embed_image(inputs["image"])
        raise UnsupportedModalityError("embed_multimodal needs a 'text' or 'image' input")


class OpenAIEmbedder(TextEmbeddingMixin):
    modalities = ["text"]
    dimension = 1536
    provider_name = "openai"

    def __init__(self, model: str = "text-embedding-3-small", api_key: str = "") -> None:
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model
        self.model_name = model
        # Update dimension for large model
        if "large" in model:
            self.dimension = 3072

    async def embed_text(self, text: str) -> list[float]:
        response = await self._client.embeddings.create(
            model=self._model,
            input=text,
        )
        return response.data[0].embedding





class GeminiEmbedder(TextEmbeddingMixin):
    """Google Gemini embedder, implemented over the REST API via httpx
    (no `google-genai` SDK dependency needed)."""

    modalities = ["text"]
    dimension = 768
    provider_name = "gemini"

    # gemini-embedding-001 returns 3072 dims unless outputDimensionality is set,
    # so we always request 768 explicitly to keep vector length stable and match
    # the Qdrant collection created from `self.dimension`.
    def __init__(self, model: str = "gemini-embedding-001", api_key: str = "") -> None:
        self._model = model
        self.model_name = model
        self._api_key = api_key

    async def embed_text(self, text: str) -> list[float]:
        import asyncio
        import random

        import httpx

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:embedContent"
        body = {
            "model": f"models/{self._model}",
            "content": {"parts": [{"text": text}]},
            "outputDimensionality": self.dimension,
        }
        max_retries = 6
        async with httpx.AsyncClient(timeout=60.0) as client:
            for attempt in range(max_retries + 1):
                resp = await client.post(url, params={"key": self._api_key}, json=body)
                if resp.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                    # exponential backoff with full jitter
                    await asyncio.sleep(random.uniform(4.0, min(4.0 * (2 ** attempt), 90.0)))
                    continue
                resp.raise_for_status()
                values = resp.json()["embedding"]["values"]
                # Some models ignore outputDimensionality; hard-trim as a safety net.
                return values[: self.dimension]
        resp.raise_for_status()
        return []





class SentenceTransformerEmbedder(TextEmbeddingMixin):
    """Local embedder — no API key needed. Good for offline/air-gapped deployments."""

    modalities = ["text"]
    dimension = 384  # all-MiniLM-L6-v2 default
    provider_name = "local"

    def __init__(self, model: str = "all-MiniLM-L6-v2") -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "EMBEDDER_BACKEND=sentence-transformers needs the optional local-embeddings "
                "extra (it installs PyTorch). Rebuild with `--build-arg EXTRAS=local-embeddings`, "
                "or use EMBEDDER_BACKEND=gemini/openai."
            ) from exc
        self.model_name = model
        self._model = SentenceTransformer(model)
        self.dimension = self._model.get_sentence_embedding_dimension()

    async def embed_text(self, text: str) -> list[float]:
        import asyncio
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(None, self._model.encode, text)
        return embedding.tolist()



