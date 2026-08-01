from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

from openai import OpenAI
from pydantic import ValidationError

from ..prompt_builder import SYSTEM_INSTRUCTIONS
from ..schemas import AnalysisInsights, ChatAnswer, CompareAnswer


class ProviderConfigurationError(RuntimeError):
    pass


class ProviderResponseError(RuntimeError):
    def __init__(self, provider_name: str, message: str) -> None:
        self.provider_name = provider_name
        super().__init__(message)


class AIProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def model(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def is_configured(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def generate_insights(self, prompt: str) -> AnalysisInsights:
        raise NotImplementedError

    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate_chat(self, prompt: str) -> ChatAnswer:
        raise NotImplementedError

    @abstractmethod
    def generate_comparison(self, prompt: str) -> CompareAnswer:
        raise NotImplementedError


class OpenAICompatibleProvider(AIProvider):
    def __init__(
        self,
        *,
        provider_name: str,
        api_key: str | None,
        model: str,
        base_url: str | None = None,
    ) -> None:
        self._provider_name = provider_name
        self._api_key = api_key
        self._model = model
        self._base_url = base_url
        self._client: OpenAI | None = None

    @property
    def name(self) -> str:
        return self._provider_name

    @property
    def model(self) -> str:
        return self._model

    def is_configured(self) -> bool:
        return bool(self._api_key and self._model)

    def generate_insights(self, prompt: str) -> AnalysisInsights:
        schema = json.dumps(AnalysisInsights.model_json_schema(), separators=(",", ":"))
        response = self._get_client().chat.completions.create(
            model=self.model,
            messages=self._messages(
                prompt,
                "Return one valid JSON object only. Do not use Markdown or code fences. "
                f"The JSON must conform exactly to this schema: {schema}",
            ),
            response_format={"type": "json_object"},
            stream=False,
            **self._completion_options(),
        )
        return parse_analysis_insights(self._message_content(response), self.name)

    def generate_text(self, prompt: str) -> str:
        response = self._get_client().chat.completions.create(
            model=self.model,
            messages=self._messages(prompt),
            stream=False,
            **self._completion_options(),
        )
        content = self._message_content(response)
        if not content.strip():
            raise ProviderResponseError(self.name, f"{self.name} returned an empty response")
        return content

    def generate_chat(self, prompt: str) -> ChatAnswer:
        return self._generate_structured(prompt, ChatAnswer)

    def generate_comparison(self, prompt: str) -> CompareAnswer:
        return self._generate_structured(prompt, CompareAnswer)

    def _generate_structured(self, prompt: str, schema_type: Any) -> Any:
        schema = json.dumps(schema_type.model_json_schema(), separators=(",", ":"))
        response = self._get_client().chat.completions.create(
            model=self.model,
            messages=self._messages(
                prompt,
                "Return one valid JSON object only. Do not use Markdown or code fences. "
                f"The JSON must conform exactly to this schema: {schema}",
            ),
            response_format={"type": "json_object"},
            stream=False,
            **self._completion_options(),
        )
        return parse_structured_response(self._message_content(response), self.name, schema_type)

    def _get_client(self) -> OpenAI:
        if not self.is_configured():
            raise ProviderConfigurationError(
                f"The API key for AI_PROVIDER={self.name} is not configured"
            )
        if self._client is None:
            options: dict[str, str] = {"api_key": self._api_key or ""}
            if self._base_url:
                options["base_url"] = self._base_url
            self._client = OpenAI(**options)
        return self._client

    def _messages(self, prompt: str, suffix: str | None = None) -> list[dict[str, str]]:
        system = SYSTEM_INSTRUCTIONS if suffix is None else f"{SYSTEM_INSTRUCTIONS}\n{suffix}"
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]

    def _completion_options(self) -> dict[str, Any]:
        return {}

    def _message_content(self, response: Any) -> str:
        try:
            content = response.choices[0].message.content
        except (AttributeError, IndexError, TypeError) as error:
            raise ProviderResponseError(
                self.name, f"{self.name} returned an invalid completion response"
            ) from error
        if not isinstance(content, str):
            raise ProviderResponseError(self.name, f"{self.name} returned no message content")
        return content


def parse_analysis_insights(content: str, provider_name: str) -> AnalysisInsights:
    return parse_structured_response(content, provider_name, AnalysisInsights)


def parse_structured_response(content: str, provider_name: str, schema_type: Any) -> Any:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].strip().lower() in {"```", "```json"}:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as error:
        raise ProviderResponseError(
            provider_name,
            f"{provider_name} returned invalid JSON for {schema_type.__name__}",
        ) from error

    try:
        return schema_type.model_validate(payload)
    except ValidationError as error:
        raise ProviderResponseError(
            provider_name,
            f"{provider_name} returned JSON that failed {schema_type.__name__} validation: {error}",
        ) from error
