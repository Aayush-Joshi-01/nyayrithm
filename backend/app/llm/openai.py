from __future__ import annotations

import time
from typing import AsyncIterator

from openai import AsyncOpenAI

from app.llm.base import LLMMessage, LLMResponse


class OpenAIProvider:
    def __init__(self, model: str, api_key: str) -> None:
        self._model = model
        self._client = AsyncOpenAI(api_key=api_key)

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model

    def _to_messages(self, messages: list[LLMMessage]) -> list[dict]:
        return [{"role": m.role, "content": m.content} for m in messages]

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> LLMResponse:
        start = time.perf_counter()
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=self._to_messages(messages),
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        elapsed = int((time.perf_counter() - start) * 1000)
        return LLMResponse(
            content=response.choices[0].message.content or "",
            model=self._model,
            provider="openai",
            input_tokens=response.usage.prompt_tokens if response.usage else 0,
            output_tokens=response.usage.completion_tokens if response.usage else 0,
            latency_ms=elapsed,
        )

    async def stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AsyncIterator[str]:
        async with await self._client.chat.completions.create(
            model=self._model,
            messages=self._to_messages(messages),
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs,
        ) as stream:
            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
