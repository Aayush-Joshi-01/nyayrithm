from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator

import httpx

from app.config import get_settings
from app.llm.base import LLMMessage, LLMResponse


class OllamaProvider:
    """Local models served by Ollama (https://ollama.com), over its HTTP API.

    No API key; the server address comes from ``OLLAMA_BASE_URL``. Local models can take a
    long time to load and generate, hence the generous timeout.
    """

    def __init__(self, model: str, api_key: str | None = None, base_url: str | None = None) -> None:
        self._model = model
        self._base_url = (base_url or get_settings().OLLAMA_BASE_URL).rstrip("/")
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=10.0))
        self.last_usage: dict[str, int] | None = None  # set after each stream() for metering

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._model

    def _payload(
        self, messages: list[LLMMessage], temperature: float, max_tokens: int, stream: bool
    ) -> dict:
        return {
            "model": self._model,
            "stream": stream,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> LLMResponse:
        start = time.perf_counter()
        resp = await self._client.post(
            f"{self._base_url}/api/chat",
            json=self._payload(messages, temperature, max_tokens, stream=False),
        )
        resp.raise_for_status()
        data = resp.json()
        return LLMResponse(
            content=data.get("message", {}).get("content", ""),
            model=self._model,
            provider="ollama",
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
            latency_ms=int((time.perf_counter() - start) * 1000),
        )

    async def stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AsyncIterator[str]:
        async with self._client.stream(
            "POST",
            f"{self._base_url}/api/chat",
            json=self._payload(messages, temperature, max_tokens, stream=True),
        ) as resp:
            resp.raise_for_status()
            self.last_usage = None
            async for line in resp.aiter_lines():
                if not line.strip():
                    continue
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if chunk.get("error"):
                    raise RuntimeError(f"Ollama error: {chunk['error']}")
                text = chunk.get("message", {}).get("content", "")
                if text:
                    yield text
                if chunk.get("done"):
                    self.last_usage = {"input_tokens": chunk.get("prompt_eval_count", 0),
                                       "output_tokens": chunk.get("eval_count", 0)}
                    return
