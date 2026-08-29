from __future__ import annotations

import structlog

from app.config import get_settings
from app.llm.base import LLMProvider
from app.llm.registry import ROLE_PROVIDER_MAP, PROVIDER_REGISTRY, _lazy_register

logger = structlog.get_logger()


def _usable(provider_name: str, settings) -> bool:
    if provider_name == "ollama":
        return provider_name in PROVIDER_REGISTRY
    return (
        provider_name in PROVIDER_REGISTRY
        and settings.get_api_key(provider_name) is not None
    )


def build_llm_provider(
    role: str,
    override_provider: str | None = None,
    override_model: str | None = None,
) -> LLMProvider:
    """
    Build an LLMProvider for the given role.

    If the requested provider isn't usable (no API key / not registered), fall
    back to LLM_DEFAULT_PROVIDER so a mis-configured agent never hard-stops a
    simulation. Only raises if nothing is usable.
    """
    _lazy_register()
    settings = get_settings()

    default_provider, default_model = ROLE_PROVIDER_MAP.get(
        role, ("gemini", "gemini-flash-lite-latest")
    )
    provider_name = override_provider or default_provider
    model_name = override_model or default_model

    if not _usable(provider_name, settings):
        fallback = settings.LLM_DEFAULT_PROVIDER
        if fallback != provider_name and _usable(fallback, settings):
            logger.warning(
                "llm_provider_fallback", requested=provider_name, using=fallback, role=role
            )
            fb_provider, fb_model = ROLE_PROVIDER_MAP.get(role, (fallback, model_name))
            provider_name = fallback
            model_name = fb_model if fb_provider == fallback else model_name
        else:
            raise ValueError(
                f"LLM provider '{provider_name}' is not usable and no fallback is "
                f"configured. Set its API key (e.g. GEMINI_API_KEY) in .env."
            )

    api_key = settings.get_api_key(provider_name)
    cls = PROVIDER_REGISTRY[provider_name]
    return cls(model=model_name, api_key=api_key)
