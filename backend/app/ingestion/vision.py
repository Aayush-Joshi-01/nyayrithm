"""Image → text transcription (OCR + description) through a vision-capable LLM.

Scanned court documents, photographs of exhibits and handwritten notes all reach the
RAG pipeline as text, so this is what makes image evidence searchable. The provider is
chosen from whatever API key is configured; with none, callers get ``None`` and fall
back to metadata-only text rather than failing the whole ingestion.
"""

from __future__ import annotations

import base64
import io
from typing import Protocol

import httpx
import structlog

from app.config import get_settings

logger = structlog.get_logger()

TRANSCRIBE_PROMPT = (
    "You are a legal evidence transcriber. Transcribe ALL text visible in this image "
    "exactly as written, preserving the original language and script (including "
    "Devanagari and other Indic scripts), line breaks, stamps, signatures and dates. "
    "Mark anything illegible as [illegible]. Do not translate, summarise or correct. "
    "If the image contains no text, write 'No text.'\n\n"
    "Then, after a line containing only '---', give a short neutral factual description "
    "of what the image shows (people, objects, places, damage, visible markings). "
    "Do not speculate about guilt, intent or identity."
)

_MAX_EDGE = 2000  # downscale very large scans; vision models cap input resolution anyway


class VisionTranscriber(Protocol):
    name: str

    async def transcribe(self, image_bytes: bytes, mime_type: str) -> str: ...


def normalize_image(image_bytes: bytes, mime_type: str) -> tuple[bytes, str]:
    """Convert to PNG/JPEG the vision APIs accept and cap the longest edge."""
    from PIL import Image

    with Image.open(io.BytesIO(image_bytes)) as img:
        img.load()
        if max(img.size) > _MAX_EDGE:
            img.thumbnail((_MAX_EDGE, _MAX_EDGE))
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        out = io.BytesIO()
        img.save(out, format="PNG")
        return out.getvalue(), "image/png"


class GeminiVision:
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-flash-lite-latest") -> None:
        self._key = api_key
        self._model = model

    async def transcribe(self, image_bytes: bytes, mime_type: str) -> str:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._model}:generateContent"
        )
        body = {
            "contents": [{"parts": [
                {"text": TRANSCRIBE_PROMPT},
                {"inline_data": {
                    "mime_type": mime_type,
                    "data": base64.b64encode(image_bytes).decode(),
                }},
            ]}],
            "generationConfig": {"temperature": 0.0},
        }
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(url, params={"key": self._key}, json=body)
            resp.raise_for_status()
        parts = resp.json()["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts).strip()


class OpenAIVision:
    name = "openai"

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self._key = api_key
        self._model = model

    async def transcribe(self, image_bytes: bytes, mime_type: str) -> str:
        data_url = f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode()}"
        body = {
            "model": self._model,
            "temperature": 0,
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": TRANSCRIBE_PROMPT},
                {"type": "image_url", "image_url": {"url": data_url}},
            ]}],
        }
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self._key}"},
                json=body,
            )
            resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()


class AnthropicVision:
    name = "anthropic"

    def __init__(self, api_key: str, model: str = "claude-haiku-4-5-20251001") -> None:
        self._key = api_key
        self._model = model

    async def transcribe(self, image_bytes: bytes, mime_type: str) -> str:
        body = {
            "model": self._model,
            "max_tokens": 4096,
            "temperature": 0,
            "messages": [{"role": "user", "content": [
                {"type": "image", "source": {
                    "type": "base64",
                    "media_type": mime_type,
                    "data": base64.b64encode(image_bytes).decode(),
                }},
                {"type": "text", "text": TRANSCRIBE_PROMPT},
            ]}],
        }
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": self._key, "anthropic-version": "2023-06-01"},
                json=body,
            )
            resp.raise_for_status()
        return "".join(
            b.get("text", "") for b in resp.json()["content"] if b.get("type") == "text"
        ).strip()


_PROVIDERS: dict[str, type] = {
    "gemini": GeminiVision,
    "openai": OpenAIVision,
    "anthropic": AnthropicVision,
}


def get_vision_transcriber() -> VisionTranscriber | None:
    """The default provider if it has a key, else any provider that does, else None."""
    settings = get_settings()
    default = settings.LLM_DEFAULT_PROVIDER
    order = [default, *(p for p in _PROVIDERS if p != default)]
    for name in order:
        key = settings.get_api_key(name)
        if key:
            return _PROVIDERS[name](api_key=key)
    return None


async def transcribe_image(
    image_bytes: bytes,
    mime_type: str,
    transcriber: VisionTranscriber | None = None,
) -> tuple[str | None, str]:
    """Return ``(text, status)``; status is 'ok', 'unavailable' or 'failed'."""
    transcriber = transcriber or get_vision_transcriber()
    if transcriber is None:
        return None, "unavailable"
    try:
        data, mime = normalize_image(image_bytes, mime_type)
        text = (await transcriber.transcribe(data, mime) or "").strip()
    except Exception as exc:  # noqa: BLE001 - never let OCR sink the whole ingestion
        logger.warning("vision_transcription_failed", provider=transcriber.name, error=str(exc))
        return None, "failed"
    return (text or None), ("ok" if text else "failed")
