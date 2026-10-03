from __future__ import annotations

"""LLMOps queries for the admin portal: consumption, cost, latency, errors, quotas, prices.

Everything is read from the ``llm_usage`` collection (one document per model call) and the
per-firm monthly counters. Costs are *estimates* from the price table; each response says so.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import text

from app.db.factory import get_repository
from app.db.stores import Stores
from app.llm.pricing import default_price_table, price_book
from app.models.documents import LlmPrice
from app.services.entitlements import current_period

GROUP_FIELDS = {
    "provider": "$provider",
    "model": {"provider": "$provider", "model": "$model"},
    "role": "$agent_role",
    "firm": "$org_id",
    "kind": "$kind",
}
_MAX_LATENCY_SAMPLE = 100_000

NOTE = ("Costs are estimates from a reference price table (editable under Prices). Calls whose "
        "provider reports no usage are counted from text length and marked estimated.")


def _percentile(sorted_values: list[int], q: float) -> int | None:
    if not sorted_values:
        return None
    idx = min(len(sorted_values) - 1, max(0, round(q * (len(sorted_values) - 1))))
    return int(sorted_values[idx])


def _flag(field: str, value: Any) -> dict[str, Any]:
    return {"$cond": [{"$eq": [field, value]}, 1, 0]}


class LlmOpsService:
    def __init__(self, stores: Stores) -> None:
        self.stores = stores
        self.db = stores.mongo

    def _match(self, days: int, org_id: str | None = None, **extra: Any) -> dict[str, Any]:
        match: dict[str, Any] = {
            "created_at": {"$gte": datetime.now(timezone.utc) - timedelta(days=days)}, **extra}
        if org_id:
            match["org_id"] = org_id
        return match

    async def _firm_names(self, ids: set[str | None]) -> dict[str, str]:
        names: dict[str, str] = {}
        orgs = get_repository("organization", self.stores)
        for oid in ids:
            if oid:
                org = await orgs.get(oid)
                names[oid] = org.name if org else "(deleted firm)"
        return names

    # ── totals ────────────────────────────────────────────────────────────────
    async def summary(self, days: int, org_id: str | None) -> dict[str, Any]:
        match = self._match(days, org_id)
        rows = await self.db["llm_usage"].aggregate([
            {"$match": match},
            {"$group": {
                "_id": None,
                "requests": {"$sum": 1},
                "errors": {"$sum": _flag("$status", "error")},
                "input_tokens": {"$sum": "$input_tokens"},
                "output_tokens": {"$sum": "$output_tokens"},
                "cost_usd": {"$sum": "$cost_usd"},
                "avg_latency_ms": {"$avg": "$latency_ms"},
                "avg_ttft_ms": {"$avg": "$ttft_ms"},
                "estimated": {"$sum": {"$cond": ["$estimated", 1, 0]}},
                "unpriced": {"$sum": _flag("$priced", False)},
            }},
        ]).to_list(length=1)
        g = rows[0] if rows else {}
        requests = int(g.get("requests", 0))
        latencies = sorted(
            int(d["latency_ms"]) for d in await self.db["llm_usage"].find(
                {**match, "status": "ok", "kind": "chat"}, {"latency_ms": 1, "_id": 0}
            ).limit(_MAX_LATENCY_SAMPLE).to_list(length=_MAX_LATENCY_SAMPLE)
        )
        return {
            "days": days, "org_id": org_id, "requests": requests,
            "errors": int(g.get("errors", 0)),
            "error_rate": round(g.get("errors", 0) / requests, 4) if requests else 0.0,
            "input_tokens": int(g.get("input_tokens", 0)),
            "output_tokens": int(g.get("output_tokens", 0)),
            "tokens": int(g.get("input_tokens", 0)) + int(g.get("output_tokens", 0)),
            "cost_usd": round(float(g.get("cost_usd", 0.0)), 6),
            "latency_ms": {"avg": round(g["avg_latency_ms"]) if g.get("avg_latency_ms") else None,
                           "p50": _percentile(latencies, 0.50), "p95": _percentile(latencies, 0.95)},
            "avg_ttft_ms": round(g["avg_ttft_ms"]) if g.get("avg_ttft_ms") else None,
            "estimated_share": round(g.get("estimated", 0) / requests, 4) if requests else 0.0,
            "unpriced_requests": int(g.get("unpriced", 0)),
            "note": NOTE,
        }

    async def timeseries(self, days: int, bucket: str, org_id: str | None) -> list[dict[str, Any]]:
        fmt = "%Y-%m-%dT%H:00" if bucket == "hour" else "%Y-%m-%d"
        rows = await self.db["llm_usage"].aggregate([
            {"$match": self._match(days, org_id)},
            {"$group": {
                "_id": {"$dateToString": {"format": fmt, "date": "$created_at"}},
                "requests": {"$sum": 1},
                "errors": {"$sum": _flag("$status", "error")},
                "input_tokens": {"$sum": "$input_tokens"},
                "output_tokens": {"$sum": "$output_tokens"},
                "cost_usd": {"$sum": "$cost_usd"},
                "avg_latency_ms": {"$avg": "$latency_ms"},
            }},
            {"$sort": {"_id": 1}},
        ]).to_list(length=5000)
        return [{
            "t": r["_id"], "requests": int(r["requests"]), "errors": int(r["errors"]),
            "tokens": int(r["input_tokens"]) + int(r["output_tokens"]),
            "cost_usd": round(float(r["cost_usd"]), 6),
            "avg_latency_ms": round(r["avg_latency_ms"]) if r["avg_latency_ms"] else None,
        } for r in rows]

    async def breakdown(self, by: str, days: int, org_id: str | None, limit: int = 50
                        ) -> list[dict[str, Any]]:
        rows = await self.db["llm_usage"].aggregate([
            {"$match": self._match(days, org_id)},
            {"$group": {
                "_id": GROUP_FIELDS[by],
                "requests": {"$sum": 1},
                "errors": {"$sum": _flag("$status", "error")},
                "input_tokens": {"$sum": "$input_tokens"},
                "output_tokens": {"$sum": "$output_tokens"},
                "cost_usd": {"$sum": "$cost_usd"},
                "avg_latency_ms": {"$avg": "$latency_ms"},
            }},
            {"$sort": {"cost_usd": -1, "requests": -1}},
            {"$limit": limit},
        ]).to_list(length=limit)
        firms = await self._firm_names({r["_id"] for r in rows}) if by == "firm" else {}
        out = []
        for r in rows:
            key = r["_id"]
            if by == "model":
                label, extra = f"{key.get('provider')}/{key.get('model')}", dict(key)
            elif by == "firm":
                label, extra = (firms.get(key, "(unattributed)") if key else "(unattributed)"), \
                    {"org_id": key}
            else:
                label, extra = (key or "(none)"), {}
            out.append({
                "key": label, **extra, "requests": int(r["requests"]), "errors": int(r["errors"]),
                "error_rate": round(r["errors"] / r["requests"], 4) if r["requests"] else 0.0,
                "tokens": int(r["input_tokens"]) + int(r["output_tokens"]),
                "input_tokens": int(r["input_tokens"]), "output_tokens": int(r["output_tokens"]),
                "cost_usd": round(float(r["cost_usd"]), 6),
                "avg_latency_ms": round(r["avg_latency_ms"]) if r["avg_latency_ms"] else None,
            })
        return out

    async def failures(self, days: int, limit: int) -> list[dict[str, Any]]:
        docs = await self.db["llm_usage"].find(
            self._match(days, status="error"), {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(length=limit)
        firms = await self._firm_names({d.get("org_id") for d in docs})
        return [{
            "created_at": d["created_at"], "kind": d.get("kind"), "provider": d.get("provider"),
            "model": d.get("model"), "error_code": d.get("error_code"),
            "firm": firms.get(d.get("org_id") or "", None), "agent_role": d.get("agent_role"),
            "simulation_id": d.get("simulation_id"), "latency_ms": d.get("latency_ms"),
        } for d in docs]

    # ── quota utilisation (Postgres counters vs plan limits) ──────────────────
    async def quota(self) -> list[dict[str, Any]]:
        rows = (await self.stores.pg.execute(text(
            "SELECT o.id AS org_id, o.name, o.status AS org_status, s.status AS sub_status, "
            "p.code AS plan, p.monthly_tokens, p.monthly_simulations, "
            "COALESCE(u.tokens, 0) AS tokens, COALESCE(u.simulations, 0) AS simulations, "
            "COALESCE(u.cost_usd, 0) AS cost_usd "
            "FROM organizations o "
            "LEFT JOIN subscriptions s ON s.org_id = o.id "
            "LEFT JOIN plans p ON p.code = s.plan_code "
            "LEFT JOIN usage_counters u ON u.org_id = o.id AND u.period = :period"
        ), {"period": current_period()})).all()
        out = []
        for r in rows:
            limit = int(r.monthly_tokens or 0)
            sims = int(r.monthly_simulations or 0)
            out.append({
                "org_id": str(r.org_id), "name": r.name, "plan": r.plan,
                "status": r.org_status, "subscription_status": r.sub_status,
                "tokens": int(r.tokens), "token_limit": limit,
                "token_utilisation": round(int(r.tokens) / limit, 4) if limit else None,
                "simulations": int(r.simulations), "simulation_limit": sims,
                "simulation_utilisation": round(int(r.simulations) / sims, 4) if sims else None,
                "cost_usd": round(float(r.cost_usd), 6),
            })
        out.sort(key=lambda x: -(x["token_utilisation"] or 0))
        return out

    # ── prices ────────────────────────────────────────────────────────────────
    async def prices(self) -> dict[str, Any]:
        repo = get_repository("llm_price", self.stores)
        overrides, _ = await repo.list(size=500)
        return {
            "defaults": default_price_table(),
            "overrides": [{"provider": o.provider, "model": o.model,
                           "input_per_mtok": o.input_per_mtok,
                           "output_per_mtok": o.output_per_mtok, "updated_by": o.updated_by}
                          for o in overrides],
            "note": "USD per million tokens. Defaults are reference figures; override a model to "
                    "match your actual contract.",
        }

    async def set_price(self, provider: str, model: str, input_per_mtok: float,
                        output_per_mtok: float, actor: str) -> None:
        repo = get_repository("llm_price", self.stores)
        existing = await self.db["llm_prices"].find_one({"provider": provider, "model": model})
        if existing:
            await repo.update(existing["id"], {"input_per_mtok": input_per_mtok,
                                               "output_per_mtok": output_per_mtok,
                                               "updated_by": actor})
        else:
            await repo.create(LlmPrice(provider=provider, model=model,
                                       input_per_mtok=input_per_mtok,
                                       output_per_mtok=output_per_mtok, updated_by=actor))
        price_book.invalidate()

    async def clear_price(self, provider: str, model: str) -> bool:
        res = await self.db["llm_prices"].delete_one({"provider": provider, "model": model})
        price_book.invalidate()
        return res.deleted_count > 0
