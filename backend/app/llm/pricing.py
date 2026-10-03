"""Reference prices for estimating what a model call cost (USD per million tokens).

These are *reference* figures to give the operator a sense of spend, not an invoice: vendors
change prices, add tiers and discount cached input. Anything here can be overridden per
model from the admin portal (stored in MongoDB), and a model with no entry is reported as
unpriced rather than as free. Local models (Ollama, sentence-transformers) are zero.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

# (provider, model-name prefix) -> (input $/Mtok, output $/Mtok). Longest prefix wins.
DEFAULT_PRICES: dict[tuple[str, str], tuple[float, float]] = {
    ("gemini", "gemini-flash-lite"): (0.10, 0.40),
    ("gemini", "gemini-2.5-flash-lite"): (0.10, 0.40),
    ("gemini", "gemini-2.5-flash"): (0.30, 2.50),
    ("gemini", "gemini-2.5-pro"): (1.25, 10.00),
    ("gemini", "gemini-embedding"): (0.15, 0.0),
    ("openai", "gpt-4o-mini"): (0.15, 0.60),
    ("openai", "gpt-4o"): (2.50, 10.00),
    ("openai", "text-embedding-3-small"): (0.02, 0.0),
    ("openai", "text-embedding-3-large"): (0.13, 0.0),
    ("anthropic", "claude-haiku-4-5"): (1.00, 5.00),
    ("ollama", ""): (0.0, 0.0),
    ("local", ""): (0.0, 0.0),
}


@dataclass(frozen=True)
class Price:
    input_per_mtok: float
    output_per_mtok: float
    source: str  # default | override


def _default_price(provider: str, model: str) -> Price | None:
    best: tuple[int, tuple[float, float]] | None = None
    for (prov, prefix), price in DEFAULT_PRICES.items():
        if prov == provider and model.startswith(prefix) and (best is None or len(prefix) > best[0]):
            best = (len(prefix), price)
    return Price(*best[1], source="default") if best else None


class PriceBook:
    """Defaults plus admin overrides. Overrides are cached briefly so metering stays cheap."""

    def __init__(self, ttl_seconds: float = 60.0) -> None:
        self._ttl = ttl_seconds
        self._overrides: dict[tuple[str, str], Price] = {}
        self._loaded_at = 0.0

    def set_overrides(self, rows: list[Any]) -> None:
        self._overrides = {
            (r.provider, r.model): Price(r.input_per_mtok, r.output_per_mtok, "override")
            for r in rows
        }
        self._loaded_at = time.monotonic()

    def invalidate(self) -> None:
        self._loaded_at = 0.0

    @property
    def stale(self) -> bool:
        return time.monotonic() - self._loaded_at > self._ttl

    def price(self, provider: str, model: str) -> Price | None:
        return self._overrides.get((provider, model)) or _default_price(provider, model)

    def cost(self, provider: str, model: str, input_tokens: int, output_tokens: int
             ) -> tuple[float, bool]:
        """(estimated USD, priced?). Unknown models cost 0.0 and are flagged unpriced."""
        price = self.price(provider, model)
        if price is None:
            return 0.0, False
        usd = (input_tokens * price.input_per_mtok + output_tokens * price.output_per_mtok) / 1e6
        return round(usd, 8), True


price_book = PriceBook()


def default_price_table() -> list[dict[str, Any]]:
    return [{"provider": p, "model": m or "*", "input_per_mtok": i, "output_per_mtok": o,
             "source": "default"} for (p, m), (i, o) in sorted(DEFAULT_PRICES.items())]
