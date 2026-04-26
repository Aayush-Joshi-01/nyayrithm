from __future__ import annotations

import time
from typing import AsyncIterator

import anthropic as anthropic_sdk

from app.llm.base import LLMMessage, LLMResponse


class AnthropicProvider:
    def __init__(self, model: str, api_key: str) -> None:
        self._model = model
        self._client = anthropic_sdk.AsyncAnthropic(api_key=api_key)

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def model_name(self) -> str:
        return self._model

    def _split_messages(self, messages: list[LLMMessage]) -> tuple[str, list[dict]]:
        system = ""
        conv: list[dict] = []
        for m in messages:
            if m.role == "system":
                system = m.content
            else:
                conv.append({"role": m.role, "content": m.content})
        return system, conv

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> LLMResponse:
        system, conv = self._split_messages(messages)
        start = time.perf_counter()
        response = await self._client.messages.create(
            model=self._model,
            system=system,
            messages=conv,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        elapsed = int((time.perf_counter() - start) * 1000)
        return LLMResponse(
            content=response.content[0].text if response.content else "",
            model=self._model,
            provider="anthropic",
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            latency_ms=elapsed,
        )

    async def stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AsyncIterator[str]:
        system, conv = self._split_messages(messages)
        async with self._client.messages.stream(
            model=self._model,
            system=system,
            messages=conv,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        ) as stream:
            async for text in stream.text_stream:
                yield text
