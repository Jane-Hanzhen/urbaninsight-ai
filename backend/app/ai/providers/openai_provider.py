from __future__ import annotations

from .base import OpenAICompatibleProvider


class OpenAIProvider(OpenAICompatibleProvider):
    def __init__(self, *, api_key: str | None, model: str) -> None:
        super().__init__(
            provider_name="openai",
            api_key=api_key,
            model=model,
        )
