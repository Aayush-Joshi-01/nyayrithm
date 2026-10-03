from __future__ import annotations

import pytest

import tests.conftest
from app.db.stores import open_stores
from app.llm.base import LLMMessage, LLMResponse
from app.llm.metering import (
    MeteredEmbedder,
    MeteredLLM,
    estimate_tokens,
    set_agent_role,
    usage_context,
)
from app.llm.pricing import PriceBook, price_book
from app.models.documents import LlmPrice
from app.services.entitlements import EntitlementService, current_period

MSGS = [LLMMessage("system", "You are a judge."), LLMMessage("user", "Proceed with the hearing.")]


class FakeLLM:
    provider_name = "gemini"
    model_name = "gemini-flash-lite-latest"

    def __init__(self, *, usage=None, reply="Order in court.", fail: Exception | None = None,
                 reported=True):
        self.last_usage = usage
        self.reply, self.fail, self.reported = reply, fail, reported

    async def complete(self, messages, temperature=0.7, max_tokens=2048, **kw):
        if self.fail:
            raise self.fail
        return LLMResponse(self.reply, self.model_name, "gemini",
                           input_tokens=120 if self.reported else 0,
                           output_tokens=30 if self.reported else 0, latency_ms=7)

    async def stream(self, messages, temperature=0.7, max_tokens=2048, **kw):
        for part in self.reply.split(" "):
            yield part + " "
        if self.fail:
            raise self.fail


def usage_docs(**query):
    return list(tests.conftest._SYNC_MONGO["llm_usage"].find(query))


@pytest.fixture(autouse=True)
def fresh_prices():
    price_book.set_overrides([])
    yield
    price_book.set_overrides([])


# ── pricing ───────────────────────────────────────────────────────────────────
def test_longest_prefix_wins_and_cost_is_per_million_tokens():
    book = PriceBook()
    book.set_overrides([])
    cost, priced = book.cost("openai", "gpt-4o-mini-2024-07-18", 1_000_000, 1_000_000)
    assert priced and cost == pytest.approx(0.15 + 0.60)  # not the dearer gpt-4o price
    cost, _ = book.cost("openai", "gpt-4o", 2_000_000, 0)
    assert cost == pytest.approx(5.0)


def test_unknown_models_are_unpriced_not_free():
    cost, priced = PriceBook().cost("mystery", "model-x", 1000, 1000)
    assert (cost, priced) == (0.0, False)


def test_local_models_cost_nothing_but_are_priced():
    assert PriceBook().cost("ollama", "llama3.1:8b", 10**6, 10**6) == (0.0, True)


def test_admin_overrides_beat_defaults():
    book = PriceBook()
    book.set_overrides([LlmPrice("gemini", "gemini-flash-lite-latest", 1.0, 2.0)])
    assert book.cost("gemini", "gemini-flash-lite-latest", 1_000_000, 1_000_000)[0] == pytest.approx(3.0)
    assert book.price("gemini", "gemini-flash-lite-latest").source == "override"


def test_token_estimate():
    assert estimate_tokens("") == 0 and estimate_tokens("abcd") == 1 and estimate_tokens("a" * 41) == 11


# ── MeteredLLM ────────────────────────────────────────────────────────────────
async def test_complete_records_reported_usage_and_cost(db_path):
    llm = MeteredLLM(FakeLLM())
    out = await llm.complete(MSGS)
    assert out.content == "Order in court."
    (doc,) = usage_docs()
    assert (doc["kind"], doc["provider"], doc["model"]) == ("chat", "gemini", "gemini-flash-lite-latest")
    assert (doc["input_tokens"], doc["output_tokens"], doc["estimated"]) == (120, 30, False)
    assert doc["cost_usd"] == pytest.approx((120 * 0.10 + 30 * 0.40) / 1e6)
    assert doc["priced"] is True and doc["status"] == "ok" and doc["latency_ms"] == 7


async def test_the_wrapper_is_transparent():
    llm = MeteredLLM(FakeLLM())
    assert (llm.provider_name, llm.model_name) == ("gemini", "gemini-flash-lite-latest")


async def test_unreported_tokens_are_estimated_and_flagged(db_path):
    await MeteredLLM(FakeLLM(reported=False)).complete(MSGS)
    (doc,) = usage_docs()
    assert doc["estimated"] is True and doc["input_tokens"] > 0 and doc["output_tokens"] > 0


async def test_stream_uses_provider_usage_when_available(db_path):
    llm = MeteredLLM(FakeLLM(usage={"input_tokens": 200, "output_tokens": 40}))
    text = "".join([t async for t in llm.stream(MSGS)])
    assert text.strip() == "Order in court."
    (doc,) = usage_docs()
    assert (doc["input_tokens"], doc["output_tokens"], doc["estimated"]) == (200, 40, False)
    assert doc["ttft_ms"] is not None and doc["ttft_ms"] <= doc["latency_ms"]


async def test_stream_without_provider_usage_is_estimated(db_path):
    _ = [t async for t in MeteredLLM(FakeLLM(usage=None)).stream(MSGS)]
    (doc,) = usage_docs()
    assert doc["estimated"] is True and doc["output_tokens"] >= 1


async def test_failures_are_recorded_and_still_raised(db_path):
    with pytest.raises(TimeoutError):
        await MeteredLLM(FakeLLM(fail=TimeoutError("slow"))).complete(MSGS)
    (doc,) = usage_docs()
    assert doc["status"] == "error" and doc["error_code"] == "TimeoutError"


async def test_stream_failure_after_partial_output_is_recorded(db_path):
    llm = MeteredLLM(FakeLLM(fail=ConnectionError("dropped")))
    with pytest.raises(ConnectionError):
        _ = [t async for t in llm.stream(MSGS)]
    (doc,) = usage_docs()
    assert doc["status"] == "error" and doc["output_tokens"] >= 1 and doc["ttft_ms"] is not None


async def test_metering_failure_never_breaks_the_call(db_path, monkeypatch):
    def boom():
        raise ConnectionError("mongo down")

    monkeypatch.setattr("app.db.mongo.get_mongo_db", boom)
    out = await MeteredLLM(FakeLLM()).complete(MSGS)
    assert out.content == "Order in court."


# ── attribution and quota counters ────────────────────────────────────────────
async def test_calls_are_attributed_to_firm_user_simulation_and_role(db_path, seed):
    org = seed.org("Meter LLP")
    llm = MeteredLLM(FakeLLM())
    with usage_context(org_id=org, user_id="amy", simulation_id="sim-1"):
        set_agent_role("judge")
        await llm.complete(MSGS)
        set_agent_role("witness")
        await llm.complete(MSGS)
    await llm.complete(MSGS)  # outside any context: recorded, unattributed

    docs = usage_docs()
    attributed = [d for d in docs if d["org_id"] == org]
    assert [d["agent_role"] for d in attributed] == ["judge", "witness"]
    assert all(d["user_id"] == "amy" and d["simulation_id"] == "sim-1" for d in attributed)
    assert [d for d in docs if d["org_id"] is None]


async def test_firm_counters_include_every_call_so_quota_checks_are_current(db_path, seed):
    org = seed.org("Counter LLP", plan="tiny", plan_limits={"monthly_tokens": 400})
    llm = MeteredLLM(FakeLLM())
    with usage_context(org_id=org):
        await llm.complete(MSGS)  # 150 tokens
        await llm.complete(MSGS)  # 300
    async with open_stores() as stores:
        ent = EntitlementService(stores)
        usage = await ent.usage(org)
        assert usage["tokens"] == 300 and usage["cost_usd"] > 0
        assert not await ent.tokens_exhausted(org)
    with usage_context(org_id=org):
        await llm.complete(MSGS)  # 450 > 400
    async with open_stores() as stores:
        assert await EntitlementService(stores).tokens_exhausted(org)
        assert (await EntitlementService(stores).usage(org))["period"] == current_period()


async def test_failed_calls_do_not_burn_the_firms_allowance(db_path, seed):
    org = seed.org("Err LLP")
    with usage_context(org_id=org), pytest.raises(TimeoutError):
        await MeteredLLM(FakeLLM(fail=TimeoutError())).complete(MSGS)
    async with open_stores() as stores:
        assert (await EntitlementService(stores).usage(org))["tokens"] == 0
    assert len(usage_docs(org_id=org)) == 1  # still visible in LLMOps


async def test_admin_price_overrides_are_applied_to_new_records(db_path):
    tests.conftest._SYNC_MONGO["llm_prices"].insert_one({
        "id": "p1", "provider": "gemini", "model": "gemini-flash-lite-latest",
        "input_per_mtok": 10.0, "output_per_mtok": 20.0,
    })
    price_book.invalidate()
    await MeteredLLM(FakeLLM()).complete(MSGS)
    (doc,) = usage_docs()
    assert doc["cost_usd"] == pytest.approx((120 * 10 + 30 * 20) / 1e6)


# ── embeddings ────────────────────────────────────────────────────────────────
class FakeEmbedder:
    provider_name, model_name, dimension, modalities = "openai", "text-embedding-3-small", 3, ["text"]

    async def embed_text(self, text):
        return [0.1, 0.2, 0.3]


async def test_embeddings_are_metered_and_the_wrapper_is_transparent(db_path):
    emb = MeteredEmbedder(FakeEmbedder())
    assert emb.dimension == 3 and emb.modalities == ["text"]
    assert await emb.embed_text("a" * 400) == [0.1, 0.2, 0.3]
    (doc,) = usage_docs()
    assert (doc["kind"], doc["provider"], doc["input_tokens"], doc["output_tokens"]) == (
        "embedding", "openai", 100, 0)
    assert doc["cost_usd"] == pytest.approx(100 * 0.02 / 1e6)


# ── through the real engine ───────────────────────────────────────────────────
async def test_a_simulation_run_meters_every_agent_call_per_role(
    seed, queued, db_path, monkeypatch
):
    from app.config import get_settings
    from app.simulation.engine import SimulationEngine

    monkeypatch.setenv("SIMULATION_TURN_DELAY_SECONDS", "0")
    get_settings.cache_clear()
    monkeypatch.setattr("app.simulation.engine.get_vector_store", lambda: None)
    monkeypatch.setattr(
        "app.agents.graph.agent_graph.build_llm_provider",
        lambda role, override_provider=None, override_model=None: MeteredLLM(
            FakeLLM(usage={"input_tokens": 500, "output_tokens": 50})),
    )

    org = seed.org("Run LLP", plan="m", plan_limits={"monthly_tokens": 10_000_000})
    seed.member(org, "owner", "owner")
    sim = seed.simulation(seed.case("owner", org=org), "owner", status="running", max_turns=4,
                          config='{"enforce_procedure": false}')
    seed.agent(sim, "judge", name="Judge")
    seed.agent(sim, "prosecutor", name="Prosecutor")

    await SimulationEngine().run_simulation(sim)

    docs = usage_docs(org_id=org, simulation_id=sim)
    assert len(docs) == 4 and {d["agent_role"] for d in docs} == {"judge", "prosecutor"}
    assert all(d["user_id"] == "owner" and d["input_tokens"] == 500 for d in docs)
    async with open_stores() as stores:
        usage = await EntitlementService(stores).usage(org)
    assert usage["tokens"] == 4 * 550 and usage["turns"] == 4
