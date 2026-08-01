from __future__ import annotations

from typing import Any

from ..indicators import replace_internal_indicator_names
from .schemas import AnalysisInsights, ChatAnswer, CompareAnswer, SupportedLocale


def sanitize_ai_text(text: str, locale: SupportedLocale) -> str:
    return replace_internal_indicator_names(text, locale)


def sanitize_analysis_insights(
    insights: AnalysisInsights, locale: SupportedLocale
) -> AnalysisInsights:
    payload = _sanitize_value(insights.model_dump(), locale)
    return AnalysisInsights.model_validate(payload)


def sanitize_chat_answer(answer: ChatAnswer, locale: SupportedLocale) -> ChatAnswer:
    return ChatAnswer.model_validate(_sanitize_value(answer.model_dump(), locale))


def sanitize_compare_answer(answer: CompareAnswer, locale: SupportedLocale) -> CompareAnswer:
    return CompareAnswer.model_validate(_sanitize_value(answer.model_dump(), locale))


def _sanitize_value(value: Any, locale: SupportedLocale) -> Any:
    if isinstance(value, str):
        return sanitize_ai_text(value, locale)
    if isinstance(value, list):
        return [_sanitize_value(item, locale) for item in value]
    if isinstance(value, dict):
        return {key: _sanitize_value(item, locale) for key, item in value.items()}
    return value
