from __future__ import annotations

import asyncio
import json
import random
import time
from typing import AsyncIterator

import httpx
import structlog

from app.llm.base import LLMMessage, LLMResponse

logger = structlog.get_logger()

_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

# Retry on transient / rate-limit responses. Free-tier Gemini is ~10-30 RPM.
_RETRY_STATUS = {429, 500, 502, 503, 504}
_MAX_RETRIES = 6
_BASE_DELAY = 4.0     # seconds
_MAX_DELAY = 90.0


def _retry_delay_from_body(body: str) -> float | None:
    """Honour the server-provided `retryDelay` in a 429 RESOURCE_EXHAUSTED body."""
    try:
        data = json.loads(body)
        for detail in data.get("error", {}).get("details", []):
            if "retryDelay" in detail:
                return float(str(detail["retryDelay"]).rstrip("s"))
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    return None


def _backoff(attempt: int, body: str = "") -> float:
    """Server hint if present, else exponential backoff with full jitter."""
    server = _retry_delay_from_body(body)
    if server is not None:
        return min(server + random.uniform(0, 1), _MAX_DELAY)
    ceiling = min(_BASE_DELAY * (2 ** attempt), _MAX_DELAY)
    return random.uniform(_BASE_DELAY, ceiling)


async def _request_with_retry(client: httpx.AsyncClient, method: str, url: str, **kw) -> httpx.Response:
    for attempt in range(_MAX_RETRIES + 1):
        resp = await client.request(method, url, **kw)
        if resp.status_code not in _RETRY_STATUS or attempt == _MAX_RETRIES:
            return resp
        wait = _backoff(attempt, resp.text)
        logger.warning("gemini_retry", status=resp.status_code, attempt=attempt + 1, wait=round(wait, 1))
        await asyncio.sleep(wait)
    return resp  # unreachable


class GeminiProvider:
    """Google Gemini provider over the REST API via httpx (no SDK dependency)."""

    def __init__(self, model: str, api_key: str) -> None:
        self._model = model
        self._api_key = api_key
        self._client = httpx.AsyncClient(timeout=120.0)

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model

    def _to_payload(
        self, messages: list[LLMMessage], temperature: float, max_tokens: int
    ) -> dict:
        system_parts = [m.content for m in messages if m.role == "system"]
        contents = [
            {
                "role": "model" if m.role == "assistant" else "user",
                "parts": [{"text": m.content}],
            }
            for m in messages
            if m.role != "system"
        ]
        payload: dict = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_parts:
            payload["systemInstruction"] = {"parts": [{"text": "\n".join(system_parts)}]}
        return payload

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> LLMResponse:
        start = time.perf_counter()
        resp = await _request_with_retry(
            self._client, "POST",
            f"{_BASE_URL}/models/{self._model}:generateContent",
            params={"key": self._api_key},
            json=self._to_payload(messages, temperature, max_tokens),
        )
        resp.raise_for_status()
        data = resp.json()
        elapsed = int((time.perf_counter() - start) * 1000)

        candidates = data.get("candidates") or []
        content = ""
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            content = "".join(p.get("text", "") for p in parts)

        usage = data.get("usageMetadata", {})
        return LLMResponse(
            content=content,
            model=self._model,
            provider="gemini",
            input_tokens=usage.get("promptTokenCount", 0),
            output_tokens=usage.get("candidatesTokenCount", 0),
            latency_ms=elapsed,
        )

    async def stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AsyncIterator[str]:
        payload = self._to_payload(messages, temperature, max_tokens)
        url = f"{_BASE_URL}/models/{self._model}:streamGenerateContent"

        # Retry the initial connection on rate-limit / transient errors.
        for attempt in range(_MAX_RETRIES + 1):
            async with self._client.stream(
                "POST", url,
                params={"key": self._api_key, "alt": "sse"},
                json=payload,
            ) as resp:
                if resp.status_code in _RETRY_STATUS and attempt < _MAX_RETRIES:
                    body = (await resp.aread()).decode("utf-8", "replace")
                    wait = _backoff(attempt, body)
                    logger.warning("gemini_stream_retry", status=resp.status_code,
                                   attempt=attempt + 1, wait=round(wait, 1))
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    chunk = line[len("data: "):].strip()
                    if not chunk or chunk == "[DONE]":
                        continue
                    try:
                        data = json.loads(chunk)
                    except json.JSONDecodeError:
                        continue
                    candidates = data.get("candidates") or []
                    if not candidates:
                        continue
                    parts = candidates[0].get("content", {}).get("parts", [])
                    for p in parts:
                        text = p.get("text", "")
                        if text:
                            yield text
                return
