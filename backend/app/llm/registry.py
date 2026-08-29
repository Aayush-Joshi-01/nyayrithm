from __future__ import annotations

from typing import Any


# role -> (default_provider, default_model)
# Alias that always resolves to Google's newest flash-lite model.
_DEFAULT_MODEL = "gemini-flash-lite-latest"
ROLE_PROVIDER_MAP: dict[str, tuple[str, str]] = {
    role: ("gemini", _DEFAULT_MODEL)
    for role in (
        "judge", "prosecutor", "defense", "plaintiff", "accused",
        "witness", "investigator", "expert_witness", "custom",
    )
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
    from app.llm.gemini import GeminiProvider
    register_provider("openai", OpenAIProvider)
    register_provider("anthropic", AnthropicProvider)
    register_provider("gemini", GeminiProvider)


def list_providers() -> list[str]:
    _lazy_register()
    return list(PROVIDER_REGISTRY.keys())


def list_role_defaults() -> dict[str, dict[str, str]]:
    return {
        role: {"provider": prov, "model": model}
        for role, (prov, model) in ROLE_PROVIDER_MAP.items()
    }
