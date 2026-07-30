from __future__ import annotations

import os

from .base import AIProvider, ProviderConfigurationError
from .deepseek_provider import DeepSeekProvider
from .mock_provider import MockProvider
from .openai_provider import OpenAIProvider
from .qwen_provider import QwenProvider

SUPPORTED_PROVIDERS = {"openai", "qwen", "deepseek"}
SUPPORTED_MODES = {"mock", "live"}


def configured_mode() -> str:
    mode = os.getenv("AI_MODE", "live").strip().lower()
    if mode not in SUPPORTED_MODES:
        raise ProviderConfigurationError(
            f"Unsupported AI_MODE '{mode}'. Expected one of: {', '.join(sorted(SUPPORTED_MODES))}"
        )
    return mode


def configured_provider() -> str:
    if configured_mode() == "mock":
        return "mock"
    provider = os.getenv("AI_PROVIDER", "openai").strip().lower()
    if provider not in SUPPORTED_PROVIDERS:
        raise ProviderConfigurationError(
            f"Unsupported AI_PROVIDER '{provider}'. Expected one of: {', '.join(sorted(SUPPORTED_PROVIDERS))}"
        )
    return provider


def configured_live_provider(provider_name: str | None = None) -> str:
    provider = (
        provider_name.strip().lower()
        if provider_name
        else os.getenv("AI_PROVIDER", "openai").strip().lower()
    )
    if provider not in SUPPORTED_PROVIDERS:
        raise ProviderConfigurationError(
            f"Unsupported AI provider '{provider}'. Expected one of: "
            f"{', '.join(sorted(SUPPORTED_PROVIDERS))}"
        )
    return provider


def configured_model(provider_name: str | None = None) -> str:
    provider = (
        configured_live_provider(provider_name)
        if provider_name is not None
        else configured_provider()
    )
    if provider == "mock":
        return "urbaninsight-mock"
    environment_name = {
        "openai": "OPENAI_MODEL",
        "qwen": "QWEN_MODEL",
        "deepseek": "DEEPSEEK_MODEL",
    }[provider]
    defaults = {
        "openai": "gpt-4o-mini",
        "qwen": "qwen3.7-plus",
        "deepseek": "deepseek-v4-flash",
    }
    return os.getenv(environment_name, defaults[provider]).strip()


def create_provider() -> AIProvider:
    if configured_mode() == "mock":
        return MockProvider()
    return create_live_provider()


def create_live_provider(provider_name: str | None = None) -> AIProvider:
    provider = configured_live_provider(provider_name)
    model = configured_model(provider)
    if provider == "openai":
        return OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"), model=model)
    if provider == "qwen":
        return QwenProvider(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            model=model,
            base_url=os.getenv(
                "QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
            ),
        )
    return DeepSeekProvider(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        model=model,
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    )


def create_basic_provider() -> MockProvider:
    return MockProvider(delay=lambda _: None)


def is_configured() -> bool:
    return create_provider().is_configured()
