from __future__ import annotations

from typing import Any


# role -> (default_provider, default_model)
ROLE_PROVIDER_MAP: dict[str, tuple[str, str]] = {
    "judge":          ("anthropic", "claude-sonnet-4-6"),
    "prosecutor":     ("openai",    "gpt-4o"),
    "defense":        ("openai",    "gpt-4o"),
    "plaintiff":      ("anthropic", "claude-haiku-4-5-20251001"),
    "accused":        ("anthropic", "claude-haiku-4-5-20251001"),
    "witness":        ("openai",    "gpt-4o-mini"),
    "investigator":   ("openai",    "gpt-4o"),
    "expert_witness": ("anthropic", "claude-sonnet-4-6"),
    "custom":         ("openai",    "gpt-4o"),
}

PROVIDER_REGISTRY: dict[str, type] = {}


def register_provider(name: str, cls: type) -> None:
    PROVIDER_REGISTRY[name] = cls


def _lazy_register() -> None:
    """Register built-in providers on first access."""
    if PROVIDER_REGISTRY:
        return
    from app.llm.openai import OpenAIProvider
    from app.llm.anthropic import AnthropicProvider
    register_provider("openai", OpenAIProvider)
    register_provider("anthropic", AnthropicProvider)


def list_providers() -> list[str]:
    _lazy_register()
    return list(PROVIDER_REGISTRY.keys())


def list_role_defaults() -> dict[str, dict[str, str]]:
    return {
        role: {"provider": prov, "model": model}
        for role, (prov, model) in ROLE_PROVIDER_MAP.items()
    }
