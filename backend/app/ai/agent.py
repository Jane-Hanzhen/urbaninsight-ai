from __future__ import annotations

from .providers import (
    ProviderConfigurationError,
    configured_live_provider,
    configured_mode,
    configured_model,
    configured_provider,
    create_provider,
    create_basic_provider,
    create_live_provider,
    is_configured,
)
from .schemas import AnalysisInsights, ChatAnswer, CompareAnswer

# Preserve the existing import contract used by the API layer.
AgentConfigurationError = ProviderConfigurationError


def generate_insights(prompt: str) -> AnalysisInsights:
    return create_provider().generate_insights(prompt)


def generate_text(prompt: str) -> str:
    return create_provider().generate_text(prompt)


def generate_chat(prompt: str) -> ChatAnswer:
    return create_provider().generate_chat(prompt)


def generate_comparison(prompt: str) -> CompareAnswer:
    return create_provider().generate_comparison(prompt)


def generate_basic_insights(prompt: str) -> AnalysisInsights:
    return create_basic_provider().generate_insights(prompt)


def generate_basic_text(prompt: str) -> str:
    return create_basic_provider().generate_text(prompt)


def generate_live_insights(
    prompt: str, provider_name: str | None = None
) -> tuple[AnalysisInsights, str, str]:
    provider = create_live_provider(provider_name)
    return provider.generate_insights(prompt), provider.name, provider.model


def generate_live_text(prompt: str, provider_name: str | None = None) -> str:
    return create_live_provider(provider_name).generate_text(prompt)


def generate_live_chat(prompt: str, provider_name: str | None = None) -> ChatAnswer:
    return create_live_provider(provider_name).generate_chat(prompt)


def generate_live_comparison(prompt: str, provider_name: str | None = None) -> CompareAnswer:
    return create_live_provider(provider_name).generate_comparison(prompt)


__all__ = [
    "AgentConfigurationError",
    "configured_mode",
    "configured_model",
    "configured_live_provider",
    "configured_provider",
    "create_provider",
    "generate_insights",
    "generate_chat",
    "generate_comparison",
    "generate_basic_insights",
    "generate_basic_text",
    "generate_live_insights",
    "generate_live_chat",
    "generate_live_comparison",
    "generate_live_text",
    "generate_text",
    "is_configured",
]
