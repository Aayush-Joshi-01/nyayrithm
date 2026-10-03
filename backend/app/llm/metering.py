from __future__ import annotations

"""LLMOps: record every model call (chat, embedding, vision) with who, what and how much.

``MeteredLLM`` wraps any ``LLMProvider``. Context (which firm, user, simulation and agent
role the call is for) travels in a ``ContextVar`` set by the engine, so providers and agents
need no changes. Recording is best-effort: a metering failure is logged and never fails a
turn. Each record is a MongoDB document (``llm_usage``) and also bumps the firm's monthly
counters in Postgres, which the quota checks read.
"""

import contextlib
import time
from collections.abc import AsyncIterator
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any

import structlog

from app.llm.base import LLMMessage, LLMProvider, LLMResponse
from app.llm.pricing import price_book
from app.models.documents import LlmUsage

logger = structlog.get_logger()


@dataclass
class UsageContext:
    org_id: str | None = None
    user_id: str | None = None
    simulation_id: str | None = None
    agent_role: str | None = None


_ctx: ContextVar[UsageContext | None] = ContextVar("usage_context", default=None)


@contextlib.contextmanager
def usage_context(**fields: Any):
    """Attribute every model call made inside the block to a firm / user / simulation."""
    token = _ctx.set(UsageContext(**fields))
    try:
        yield _ctx.get()
    finally:
        _ctx.reset(token)


def set_agent_role(role: str | None) -> None:
    ctx = _ctx.get()
    if ctx is not None:
        ctx.agent_role = role


def estimate_tokens(text: str) -> int:
    """Rough token count (about four characters each) for providers that report none."""
    return max(1, (len(text) + 3) // 4) if text else 0


async def _refresh_prices() -> None:
    if not price_book.stale:
        return
    from app.db import mongo
    from app.models.documents import LlmPrice

    try:
        docs = await mongo.get_mongo_db()["llm_prices"].find({}).to_list(length=500)
        rows = []
        for d in docs:
            d.pop("_id", None)
            rows.append(LlmPrice(**{k: v for k, v in d.items()
                                    if k in LlmPrice.__dataclass_fields__}))
        price_book.set_overrides(rows)
    except Exception as exc:  # noqa: BLE001 - fall back to defaults
        price_book.set_overrides([])
        logger.warning("price_overrides_unavailable", error=str(exc))


async def record_usage(
    *, kind: str, provider: str, model: str, input_tokens: int, output_tokens: int,
    estimated: bool, latency_ms: int, ttft_ms: int | None = None, status: str = "ok",
    error_code: str | None = None,
) -> None:
    """Persist one usage record and add it to the firm's monthly counters."""
    ctx = _ctx.get() or UsageContext()
    try:
        await _refresh_prices()
        cost, priced = price_book.cost(provider, model, input_tokens, output_tokens)
        from app.db.factory import get_repository
        from app.db.stores import open_stores
        from app.services.entitlements import EntitlementService

        usage = LlmUsage(
            kind=kind, provider=provider, model=model, org_id=ctx.org_id, user_id=ctx.user_id,
            simulation_id=ctx.simulation_id, agent_role=ctx.agent_role,
            input_tokens=input_tokens, output_tokens=output_tokens, estimated=estimated,
            cost_usd=cost, priced=priced, latency_ms=latency_ms, ttft_ms=ttft_ms,
            status=status, error_code=error_code,
        )
        async with open_stores() as stores:
            await get_repository("llm_usage", stores).create(usage)
            if ctx.org_id and status == "ok":
                await EntitlementService(stores).add_usage(
                    ctx.org_id, tokens=input_tokens + output_tokens, cost_usd=cost
                )
    except Exception as exc:  # noqa: BLE001
        logger.warning("usage_record_failed", error=str(exc))


class MeteredEmbedder:
    """Wraps an ``Embedder`` so every embedding call is recorded (tokens are estimated)."""

    def __init__(self, inner: Any) -> None:
        self._inner = inner

    def __getattr__(self, name: str) -> Any:  # modalities, dimension, provider/model names
        return getattr(self._inner, name)

    async def embed_text(self, text: str) -> list[float]:
        started = time.perf_counter()
        provider = getattr(self._inner, "provider_name", "unknown")
        model = getattr(self._inner, "model_name", "unknown")
        try:
            vector = await self._inner.embed_text(text)
        except Exception as exc:
            await record_usage(
                kind="embedding", provider=provider, model=model,
                input_tokens=estimate_tokens(text), output_tokens=0, estimated=True,
                latency_ms=int((time.perf_counter() - started) * 1000),
                status="error", error_code=type(exc).__name__,
            )
            raise
        await record_usage(
            kind="embedding", provider=provider, model=model,
            input_tokens=estimate_tokens(text), output_tokens=0, estimated=True,
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
        return vector

    async def embed_image(self, image_bytes: bytes) -> list[float]:
        return await self._inner.embed_image(image_bytes)

    async def embed_audio(self, audio_bytes: bytes) -> list[float]:
        return await self._inner.embed_audio(audio_bytes)

    async def embed_multimodal(self, inputs: dict) -> list[float]:
        return await self._inner.embed_multimodal(inputs)


class MeteredLLM:
    """An ``LLMProvider`` that records what it is asked to do. Behaves exactly like the inner one."""

    def __init__(self, inner: LLMProvider) -> None:
        self._inner = inner

    @property
    def provider_name(self) -> str:
        return self._inner.provider_name

    @property
    def model_name(self) -> str:
        return self._inner.model_name

    async def complete(self, messages: list[LLMMessage], temperature: float = 0.7,
                       max_tokens: int = 2048, **kwargs: Any) -> LLMResponse:
        started = time.perf_counter()
        try:
            response = await self._inner.complete(
                messages, temperature=temperature, max_tokens=max_tokens, **kwargs
            )
        except Exception as exc:
            await record_usage(
                kind="chat", provider=self.provider_name, model=self.model_name,
                input_tokens=sum(estimate_tokens(m.content) for m in messages), output_tokens=0,
                estimated=True, latency_ms=int((time.perf_counter() - started) * 1000),
                status="error", error_code=type(exc).__name__,
            )
            raise
        reported = bool(response.input_tokens or response.output_tokens)
        await record_usage(
            kind="chat", provider=self.provider_name, model=self.model_name,
            input_tokens=response.input_tokens or sum(estimate_tokens(m.content) for m in messages),
            output_tokens=response.output_tokens or estimate_tokens(response.content),
            estimated=not reported,
            latency_ms=response.latency_ms or int((time.perf_counter() - started) * 1000),
        )
        return response

    async def stream(self, messages: list[LLMMessage], temperature: float = 0.7,
                     max_tokens: int = 2048, **kwargs: Any) -> AsyncIterator[str]:
        started = time.perf_counter()
        first_token_at: float | None = None
        produced: list[str] = []
        try:
            async for token in self._inner.stream(
                messages, temperature=temperature, max_tokens=max_tokens, **kwargs
            ):
                if first_token_at is None:
                    first_token_at = time.perf_counter()
                produced.append(token)
                yield token
        except BaseException as exc:
            # Includes cancellation: the call still cost something and is worth recording.
            await record_usage(
                kind="chat", provider=self.provider_name, model=self.model_name,
                input_tokens=sum(estimate_tokens(m.content) for m in messages),
                output_tokens=estimate_tokens("".join(produced)), estimated=True,
                latency_ms=int((time.perf_counter() - started) * 1000),
                ttft_ms=int((first_token_at - started) * 1000) if first_token_at else None,
                status="error", error_code=type(exc).__name__,
            )
            raise
        usage = getattr(self._inner, "last_usage", None)
        reported = bool(usage and (usage.get("input_tokens") or usage.get("output_tokens")))
        await record_usage(
            kind="chat", provider=self.provider_name, model=self.model_name,
            input_tokens=(usage or {}).get("input_tokens")
            or sum(estimate_tokens(m.content) for m in messages),
            output_tokens=(usage or {}).get("output_tokens") or estimate_tokens("".join(produced)),
            estimated=not reported,
            latency_ms=int((time.perf_counter() - started) * 1000),
            ttft_ms=int((first_token_at - started) * 1000) if first_token_at else None,
        )
