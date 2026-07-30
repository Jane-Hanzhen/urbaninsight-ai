from __future__ import annotations

from typing import Any

from .base import OpenAICompatibleProvider


class QwenProvider(OpenAICompatibleProvider):
    def __init__(self, *, api_key: str | None, model: str, base_url: str) -> None:
        super().__init__(
            provider_name="qwen",
            api_key=api_key,
            model=model,
            base_url=base_url,
        )

    def _completion_options(self) -> dict[str, Any]:
        return {"extra_body": {"enable_thinking": False}}
