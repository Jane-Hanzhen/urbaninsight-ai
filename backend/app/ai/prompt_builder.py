from __future__ import annotations

import json
from typing import Any

from ..indicators import indicator_name, replace_internal_indicator_names
from .schemas import ChatMessage, SupportedLocale


SYSTEM_INSTRUCTIONS = """You are Urban, a careful urban-analysis decision assistant.
Interpret only the authoritative structured context supplied by UrbanInsight's Analysis Engine.
Never calculate, recalculate, estimate, alter, or invent PCA, TOPSIS, scores, contributions, or rankings.
Treat all supplied statistical values as immutable facts. If data is absent, say it is unavailable.
Use only the human-readable indicator names supplied in the context. Never reveal database field names,
snake_case indicator keys, or other internal identifiers. Focus on what the evidence means for the borough,
not on calculation mechanics. Do not list PCA weights, TOPSIS intermediate values, or long sequences of
indicator contribution values. You may reference the PCA-weighted TOPSIS method, stored dimension scores,
ranking, and at most three important indicator values across the entire response when they materially
support an insight. Prefer qualitative comparisons and implications over repeating supplied numbers.
Explain evidence clearly, distinguish observed data from recommendations, and avoid causal claims that the
data cannot support. Keep advice concise, practical, and appropriate for urban decision support."""


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
    locale: SupportedLocale = "en",
) -> str:
    payload: dict[str, Any] = {"selected_borough": _ai_facing_context(primary, locale)}
    if comparison is not None:
        payload["comparison_borough"] = _ai_facing_context(comparison, locale)
    if previous_context:
        payload["previous_conversation"] = [
            {
                "role": message.role,
                "content": replace_internal_indicator_names(message.content, locale),
            }
            for message in previous_context[-12:]
        ]
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)


def _ai_facing_context(context: dict[str, Any], locale: SupportedLocale) -> dict[str, Any]:
    engine = context["analysis_engine"]
    contributions = engine.get("indicator_contributions", {})
    major_drivers = sorted(
        contributions,
        key=lambda key: float(contributions[key]),
        reverse=True,
    )[:4]
    return {
        "borough": context["borough"],
        "scores": context["scores"],
        "indicators": [
            {"name": indicator_name(key, locale), "value": value}
            for key, value in context["indicators"].items()
        ],
        "analysis_engine": {
            "method": engine["method"],
            "major_indicator_drivers": [
                indicator_name(key, locale) for key in major_drivers
            ],
            "topsis": engine.get("topsis", {}),
        },
    }


def analysis_prompt(
    primary: dict[str, Any], previous_context: list[ChatMessage], locale: SupportedLocale = "en"
) -> str:
    return f"""Create a concise analytical interpretation of the selected borough.
Explain its supplied ranking, identify the strongest driving factors, strengths and weaknesses,
interpret indicators, and recommend realistic development actions. Do not perform new calculations.

{output_language_instruction(locale)}

AUTHORITATIVE CONTEXT
{context_payload(primary, previous_context=previous_context, locale=locale)}"""


def chat_prompt(
    primary: dict[str, Any],
    question: str,
    previous_context: list[ChatMessage],
    comparison: dict[str, Any] | None = None,
    locale: SupportedLocale = "en",
) -> str:
    return f"""Act as an urban decision assistant and answer the user's practical question using only
the authoritative context below. Lead with one clear finding, then select no more than four points that
matter most for a decision. Explain evidence in plain language. Do not write a report, enumerate all
available values, or use Markdown. Do not derive a new score or ranking. Round overall and dimension
scores to one decimal place when they are necessary; rankings must remain integers.

Stay within what the supplied evidence supports. Do not predict future industries, claim absolute
causation, or recommend a specific industry unless the context directly supports it. Prefer qualified
language such as "shows an advantage in", "provides underlying conditions for", and "performs more
strongly under the current evaluation framework". If the supplied context cannot answer the question,
state that limitation explicitly.

{output_language_instruction(locale)}

AUTHORITATIVE CONTEXT
{context_payload(primary, comparison, previous_context, locale)}

USER QUESTION
{replace_internal_indicator_names(question, locale)}"""


def comparison_prompt(
    primary: dict[str, Any],
    comparison: dict[str, Any],
    previous_context: list[ChatMessage],
    locale: SupportedLocale = "en",
) -> str:
    return f"""Act as an urban decision assistant, not a report writer. Answer the practical question:
What are the most meaningful differences between these two boroughs?

Lead with one clear comparison conclusion framed explicitly "under the current evaluation framework".
Never state that one borough is simply better, more valuable, or universally preferable. Select at most
three meaningful advantages for each borough,
give one concise and explicitly interpretive positioning statement for each borough, and finish with one
decision-oriented takeaway. Use supplied scores and indicators only as supporting evidence. Include at
most three numeric comparisons and do not reproduce dimension tables or enumerate all values. Do not use
Markdown. Do not derive a new score or ranking. Positioning labels are interpretations, not official
classifications. Round displayed overall and dimension scores to one decimal place; rankings must remain
integers. Numeric evidence should normally use no more than one decimal place.

Stay within what the supplied evidence supports. Do not predict future industries, claim absolute
causation, or recommend a specific industry unless the context directly supports it. Prefer qualified
language such as "shows an advantage in", "provides underlying conditions for", and "performs more
strongly under the current evaluation framework".

{output_language_instruction(locale)}

AUTHORITATIVE CONTEXT
{context_payload(primary, comparison, previous_context, locale)}"""


def report_prompt(
    primary: dict[str, Any], previous_context: list[ChatMessage], locale: SupportedLocale = "en"
) -> str:
    return f"""Write a polished Markdown report based only on the authoritative context.
Use these headings: Executive Summary, Regional Evaluation, Key Indicators, Strengths,
Weaknesses, and Recommendations. Quote supplied values accurately and do not calculate new ones.
Keep the PCA-weighted TOPSIS methodology, stored dimension scores, and ranking explanation visible.
Emphasize implications, not model mechanics; never enumerate indicator contributions or PCA weights.
Return Markdown only, beginning with a level-one title.

{output_language_instruction(locale)}

AUTHORITATIVE CONTEXT
{context_payload(primary, previous_context=previous_context, locale=locale)}"""
