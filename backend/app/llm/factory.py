from __future__ import annotations

from app.config import get_settings
from app.llm.base import LLMProvider
from app.llm.registry import ROLE_PROVIDER_MAP, PROVIDER_REGISTRY, _lazy_register


def build_llm_provider(
    role: str,
    override_provider: str | None = None,
    override_model: str | None = None,
) -> LLMProvider:
    """
    Build and return an LLMProvider for the given role.
    Override provider/model to bypass the role default map.
    """
    _lazy_register()
    settings = get_settings()

    default_provider, default_model = ROLE_PROVIDER_MAP.get(role, ("openai", "gpt-4o"))
    provider_name = override_provider or default_provider
    model_name = override_model or default_model

    api_key = settings.get_api_key(provider_name)
    if api_key is None and provider_name not in ("ollama",):
        raise ValueError(
            f"API key for provider '{provider_name}' is not configured. "
            f"Set the corresponding env var (e.g. OPENAI_API_KEY)."
        )

    cls = PROVIDER_REGISTRY.get(provider_name)
    if cls is None:
        raise NotImplementedError(
            f"LLM provider '{provider_name}' is not registered. "
            f"Add it to app/llm/ and call registry.register_provider()."
        )

    return cls(model=model_name, api_key=api_key)
