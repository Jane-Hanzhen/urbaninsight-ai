from __future__ import annotations

from .base import OpenAICompatibleProvider


class DeepSeekProvider(OpenAICompatibleProvider):
    def __init__(self, *, api_key: str | None, model: str, base_url: str) -> None:
        super().__init__(
            provider_name="deepseek",
            api_key=api_key,
            model=model,
            base_url=base_url,
        )
