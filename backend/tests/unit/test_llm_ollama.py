from __future__ import annotations

import json

import httpx
import pytest

from app.llm.base import LLMMessage
from app.llm.factory import build_llm_provider
from app.llm.ollama import OllamaProvider
from app.llm.registry import PROVIDER_REGISTRY, _lazy_register

MESSAGES = [LLMMessage("system", "You are a judge."), LLMMessage("user", "Proceed.")]


def provider_with(handler) -> OllamaProvider:
    p = OllamaProvider("llama3.1:8b", base_url="http://ollama.test:11434/")
    p._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return p


async def test_complete_maps_request_and_response():
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"], seen["body"] = str(request.url), json.loads(request.content)
        return httpx.Response(200, json={
            "message": {"role": "assistant", "content": "Order in court."},
            "prompt_eval_count": 12, "eval_count": 4,
        })

    out = await provider_with(handler).complete(MESSAGES, temperature=0.2, max_tokens=64)
    assert seen["url"] == "http://ollama.test:11434/api/chat"
    assert seen["body"]["model"] == "llama3.1:8b" and seen["body"]["stream"] is False
    assert seen["body"]["options"] == {"temperature": 0.2, "num_predict": 64}
    assert seen["body"]["messages"][0] == {"role": "system", "content": "You are a judge."}
    assert (out.content, out.provider, out.input_tokens, out.output_tokens) == (
        "Order in court.", "ollama", 12, 4)


async def test_stream_yields_tokens_until_done():
    lines = [
        {"message": {"content": "Order"}, "done": False},
        {"message": {"content": " in"}, "done": False},
        {"message": {"content": " court."}, "done": False},
        {"message": {"content": ""}, "done": True},
    ]
    body = "\n".join(json.dumps(line) for line in lines) + "\n"
    p = provider_with(lambda r: httpx.Response(200, text=body))
    assert [t async for t in p.stream(MESSAGES)] == ["Order", " in", " court."]


async def test_stream_surfaces_server_errors():
    p = provider_with(lambda r: httpx.Response(200, text='{"error": "model not found"}\n'))
    with pytest.raises(RuntimeError, match="model not found"):
        [t async for t in p.stream(MESSAGES)]


async def test_http_errors_propagate():
    p = provider_with(lambda r: httpx.Response(404, json={"error": "nope"}))
    with pytest.raises(httpx.HTTPStatusError):
        await p.complete(MESSAGES)


def test_ollama_is_registered_and_needs_no_api_key(monkeypatch):
    _lazy_register()
    assert PROVIDER_REGISTRY["ollama"] is OllamaProvider
    llm = build_llm_provider("judge", override_provider="ollama", override_model="mistral-nemo")
    assert (llm.provider_name, llm.model_name) == ("ollama", "mistral-nemo")
