from __future__ import annotations

import json
from typing import Any

from .schemas import ChatMessage, SupportedLocale


SYSTEM_INSTRUCTIONS = """You are Urban, a careful urban-analysis decision assistant.
Interpret only the authoritative structured context supplied by UrbanInsight's Analysis Engine.
Never calculate, recalculate, estimate, alter, or invent PCA, TOPSIS, scores, contributions, or rankings.
Treat all supplied statistical values as immutable facts. If data is absent, say it is unavailable.
Explain evidence in plain English, distinguish observed data from recommendations, and avoid causal claims
that the data cannot support. Keep advice concise, practical, and appropriate for urban decision support."""


def output_language_instruction(locale: SupportedLocale) -> str:
    if locale == "zh-CN":
        return (
            "OUTPUT LANGUAGE: Simplified Chinese (zh-CN). 请使用清晰、专业的简体中文回答。"
            "Keep JSON property names, numeric values, borough names, and the "
            "recommendation priority values High or Medium unchanged."
        )
    return "OUTPUT LANGUAGE: English (en). Respond in clear, professional English."


def context_payload(
    primary: dict[str, Any],
    comparison: dict[str, Any] | None = None,
    previous_context: list[ChatMessage] | None = None,
) -> str:
    payload: dict[str, Any] = {"selected_borough": primary}
    if comparison is not None:
        payload["comparison_borough"] = comparison
    if previous_context:
        payload["previous_conversation"] = [message.model_dump() for message in previous_context[-12:]]
    return json.dumps(payload, indent=2, sort_keys=True)


def analysis_prompt(
    primary: dict[str, Any], previous_context: list[ChatMessage], locale: SupportedLocale = "en"
) -> str:
    return f"""Create a concise analytical interpretation of the selected borough.
Explain its supplied ranking, identify the strongest driving factors, strengths and weaknesses,
interpret indicators, and recommend realistic development actions. Do not perform new calculations.

{output_language_instruction(locale)}

AUTHORITATIVE CONTEXT
{context_payload(primary, previous_context=previous_context)}"""


def chat_prompt(
    primary: dict[str, Any],
    question: str,
    previous_context: list[ChatMessage],
    comparison: dict[str, Any] | None = None,
    locale: SupportedLocale = "en",
) -> str:
    return f"""Answer the user's question using only the authoritative context below.
When comparing boroughs, explain supplied score, indicator, contribution, and development differences;
do not derive a new score or ranking. Keep the response focused and use Markdown when useful.

{output_language_instruction(locale)}

AUTHORITATIVE CONTEXT
{context_payload(primary, comparison, previous_context)}

USER QUESTION
{question}"""


def comparison_prompt(
    primary: dict[str, Any],
    comparison: dict[str, Any],
    previous_context: list[ChatMessage],
    locale: SupportedLocale = "en",
) -> str:
    return chat_prompt(
        primary,
        "Compare the selected borough with the comparison borough. Explain score and indicator differences, competitive advantages, and development gaps.",
        previous_context,
        comparison,
        locale,
    )


def report_prompt(
    primary: dict[str, Any], previous_context: list[ChatMessage], locale: SupportedLocale = "en"
) -> str:
    return f"""Write a polished Markdown report based only on the authoritative context.
Use these headings: Executive Summary, Regional Evaluation, Key Indicators, Strengths,
Weaknesses, and Recommendations. Quote supplied values accurately and do not calculate new ones.
Return Markdown only, beginning with a level-one title.

{output_language_instruction(locale)}

AUTHORITATIVE CONTEXT
{context_payload(primary, previous_context=previous_context)}"""
