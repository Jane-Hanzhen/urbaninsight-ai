from __future__ import annotations

import json
from typing import Any, Literal

from .schemas import ChatAnswer, CompareAnswer, SupportedLocale


DimensionKey = Literal["economic", "social", "ecological"]
DIMENSIONS: tuple[DimensionKey, ...] = ("economic", "social", "ecological")


def build_mock_chat_response(prompt: str) -> ChatAnswer | None:
    parsed = _parse_prompt(prompt)
    if parsed is None:
        return None
    payload, question, locale = parsed
    primary = payload.get("selected_borough")
    if not isinstance(primary, dict):
        return None

    intent = _question_intent(question)
    if intent == "weakness":
        return _weakness_answer(primary, locale)
    if intent == "ranking":
        return _ranking_answer(primary, locale)
    if intent == "development":
        return _development_answer(primary, locale)
    if intent == "strength":
        return _strength_answer(primary, locale)
    return _overview_answer(primary, locale)


def build_mock_compare_response(prompt: str) -> CompareAnswer | None:
    parsed = _parse_prompt(prompt)
    if parsed is None:
        return None
    payload, _, locale = parsed
    primary = payload.get("selected_borough")
    comparison = payload.get("comparison_borough")
    if not isinstance(primary, dict) or not isinstance(comparison, dict):
        return None

    primary_name = _borough_name(primary)
    comparison_name = _borough_name(comparison)
    primary_scores = _scores(primary)
    comparison_scores = _scores(comparison)
    primary_better = sorted(
        DIMENSIONS,
        key=lambda key: primary_scores[key] - comparison_scores[key],
        reverse=True,
    )
    comparison_better = sorted(
        DIMENSIONS,
        key=lambda key: comparison_scores[key] - primary_scores[key],
        reverse=True,
    )
    primary_advantages = [
        _comparison_advantage(key, primary_name, comparison_name, locale)
        for key in primary_better
        if primary_scores[key] > comparison_scores[key]
    ][:3]
    comparison_advantages = [
        _comparison_advantage(key, comparison_name, primary_name, locale)
        for key in comparison_better
        if comparison_scores[key] > primary_scores[key]
    ][:3]
    if not primary_advantages:
        primary_advantages = [
            _profile_advantage(_strongest_dimension(primary), primary_name, locale)
        ]
    if not comparison_advantages:
        comparison_advantages = [
            _profile_advantage(_strongest_dimension(comparison), comparison_name, locale)
        ]

    primary_overall = float(primary_scores["overall"])
    comparison_overall = float(comparison_scores["overall"])
    if locale == "zh-CN":
        summary = (
            f"在当前评价体系下，{primary_name}与{comparison_name}呈现出不同的优势结构；"
            "差异应结合具体决策重点理解，而不是作为区域价值的绝对判断。"
        )
        headline = f"{primary_name}与{comparison_name}各有侧重"
        decision_note = "选择应取决于更重视经济活力、公共服务还是生态环境。"
    else:
        summary = (
            f"Under the current evaluation framework, {primary_name} and {comparison_name} "
            "show different strength profiles; these differences are decision context, not an "
            "absolute judgement of borough value."
        )
        headline = f"{primary_name} and {comparison_name} have different strengths"
        decision_note = (
            "The more relevant choice depends on whether economic activity, public services, "
            "or ecological conditions matter most."
        )

    evidence_keys = sorted(
        DIMENSIONS,
        key=lambda key: abs(primary_scores[key] - comparison_scores[key]),
        reverse=True,
    )[:2]
    evidence = [
        {
            "label": _dimension_name(key, locale),
            "primary_value": _format_score(primary_scores[key]),
            "comparison_value": _format_score(comparison_scores[key]),
        }
        for key in evidence_keys
    ]
    evidence.insert(
        0,
        {
            "label": _text(locale, "Overall score", "综合得分"),
            "primary_value": _format_score(primary_overall),
            "comparison_value": _format_score(comparison_overall),
        },
    )
    return CompareAnswer(
        headline=headline,
        summary=summary,
        primary_advantages=primary_advantages,
        comparison_advantages=comparison_advantages,
        primary_positioning=_positioning(primary, locale),
        comparison_positioning=_positioning(comparison, locale),
        decision_note=decision_note,
        evidence=evidence,
    )


def _strength_answer(context: dict[str, Any], locale: SupportedLocale) -> ChatAnswer:
    name = _borough_name(context)
    strongest = _strongest_dimension(context)
    drivers = _drivers(context)[:3]
    dimension = _dimension_name(strongest, locale)
    if locale == "zh-CN":
        return ChatAnswer(
            headline=f"{dimension}是{name}当前最突出的维度",
            summary=f"在当前评价体系下，{name}的主要优势来自{dimension}，相关指标为这一表现提供了数据支撑。",
            key_points=[
                {"title": driver, "detail": "该指标是当前分析结果中的主要驱动因素之一。", "tone": "positive"}
                for driver in drivers
            ],
            bottom_line=f"简单来说，{name}在{dimension}方面表现更突出。",
        )
    return ChatAnswer(
        headline=f"{dimension} is {name}'s clearest strength",
        summary=f"Under the current evaluation framework, {name}'s main advantage comes from {dimension.lower()}, supported by the current indicator profile.",
        key_points=[
            {"title": driver, "detail": "This is one of the main drivers in the stored analysis result.", "tone": "positive"}
            for driver in drivers
        ],
        bottom_line=f"In short, {name} performs most strongly in {dimension.lower()}.",
    )


def _weakness_answer(context: dict[str, Any], locale: SupportedLocale) -> ChatAnswer:
    name = _borough_name(context)
    weakest = _weakest_dimension(context)
    dimension = _dimension_name(weakest, locale)
    score = _format_score(_scores(context)[weakest])
    if locale == "zh-CN":
        return ChatAnswer(
            headline=f"{dimension}是{name}相对需要关注的方向",
            summary=f"在当前评价体系下，{dimension}是该区域三个维度中得分相对较低的一项。",
            key_points=[
                {"title": f"{dimension}表现", "detail": f"当前维度得分为 {score}，应结合具体指标继续观察。", "tone": "attention"},
                {"title": "谨慎解读", "detail": "相对短板不等于区域缺乏价值，也不代表单一因素造成了当前结果。", "tone": "neutral"},
            ],
            bottom_line=f"后续可以优先关注如何改善{dimension}相关条件。",
        )
    return ChatAnswer(
        headline=f"{dimension} is the main area to watch in {name}",
        summary=f"Under the current evaluation framework, {dimension.lower()} is the lowest-scoring of the borough's three dimensions.",
        key_points=[
            {"title": f"{dimension} performance", "detail": f"The current dimension score is {score} and should be read alongside its indicators.", "tone": "attention"},
            {"title": "Interpret with care", "detail": "A relative weakness is not an absolute judgement and does not establish a single cause.", "tone": "neutral"},
        ],
        bottom_line=f"Future attention can focus on improving the conditions represented by {dimension.lower()}.",
    )


def _ranking_answer(context: dict[str, Any], locale: SupportedLocale) -> ChatAnswer:
    name = _borough_name(context)
    scores = _scores(context)
    rank = int(scores["regional_rank"])
    strongest = _strongest_dimension(context)
    dimension = _dimension_name(strongest, locale)
    drivers = _drivers(context)[:3]
    if locale == "zh-CN":
        return ChatAnswer(
            headline=f"{name}的排名由整体维度表现共同支撑",
            summary=f"该区域综合得分为 {_format_score(scores['overall'])}、排名第 {rank}；在当前评价体系下，{_rank_statement(rank, locale)}",
            key_points=[
                {"title": f"{dimension}较突出", "detail": "这是当前三个维度中表现最高的一项。", "tone": "positive"},
                {"title": "主要驱动因素", "detail": "、".join(drivers), "tone": "neutral"},
            ],
            bottom_line="这里解释的是已存储分析结果，不会重新计算 PCA-TOPSIS。",
        )
    return ChatAnswer(
        headline=f"{name}'s rank is supported by its combined dimension profile",
        summary=f"The borough has an overall score of {_format_score(scores['overall'])} and rank {rank}; under the current evaluation framework, {_rank_statement(rank, locale)}",
        key_points=[
            {"title": f"Stronger {dimension.lower()}", "detail": "This is the highest of the three current dimension scores.", "tone": "positive"},
            {"title": "Main drivers", "detail": ", ".join(drivers), "tone": "neutral"},
        ],
        bottom_line="This explains the stored result without recalculating PCA-TOPSIS.",
    )


def _development_answer(context: dict[str, Any], locale: SupportedLocale) -> ChatAnswer:
    name = _borough_name(context)
    strongest = _strongest_dimension(context)
    dimension = _dimension_name(strongest, locale)
    directions = {
        "economic": _text(locale, "commercial activity and professional-service-related urban functions", "商业活动、专业服务及相关城市功能"),
        "social": _text(locale, "public services, accessibility, and everyday service functions", "公共服务、交通可达性和生活服务相关方向"),
        "ecological": _text(locale, "green space, recreation, and liveability-related improvements", "绿色空间、休闲和宜居环境相关方向"),
    }
    if locale == "zh-CN":
        return ChatAnswer(
            response_type="recommendation",
            headline=f"可以从{name}现有的{dimension}基础出发",
            summary=f"基于当前指标表现，该区域更具备支持{directions[strongest]}的基础条件，但这不是产业预测。",
            key_points=[
                {"title": "现有基础", "detail": f"{dimension}是当前得分最高的维度。", "tone": "positive"},
                {"title": "关注方向", "detail": f"可以关注{directions[strongest]}，并结合更具体的数据进一步判断。", "tone": "neutral"},
            ],
            bottom_line="建议把这些方向视为探索线索，而不是确定的发展结论。",
            limitations="当前数据用于区域表现评价，不能直接证明具体产业的未来发展结果。",
        )
    return ChatAnswer(
        response_type="recommendation",
        headline=f"Build from {name}'s existing {dimension.lower()} base",
        summary=f"Based on the current indicators, the borough has underlying conditions that can support {directions[strongest]}; this is not an industry forecast.",
        key_points=[
            {"title": "Existing base", "detail": f"{dimension} is the highest current dimension score.", "tone": "positive"},
            {"title": "Direction to explore", "detail": f"Consider {directions[strongest]} and validate the direction with more specific evidence.", "tone": "neutral"},
        ],
        bottom_line="Treat these as exploration directions rather than certain development outcomes.",
        limitations="The current data evaluates borough performance and cannot establish future results for a specific industry.",
    )


def _overview_answer(context: dict[str, Any], locale: SupportedLocale) -> ChatAnswer:
    strength = _strongest_dimension(context)
    weakness = _weakest_dimension(context)
    name = _borough_name(context)
    if locale == "zh-CN":
        return ChatAnswer(
            headline=f"{name}呈现出清晰的优势与改进方向",
            summary=f"在当前评价体系下，{_dimension_name(strength, locale)}表现最突出，{_dimension_name(weakness, locale)}相对需要关注。",
            key_points=[
                {"title": "主要优势", "detail": f"{_dimension_name(strength, locale)}是当前最高维度。", "tone": "positive"},
                {"title": "重点关注", "detail": f"{_dimension_name(weakness, locale)}是当前最低维度。", "tone": "attention"},
            ],
            bottom_line="可以继续追问优势、短板、排名原因或值得关注的发展方向。",
        )
    return ChatAnswer(
        headline=f"{name} has a clear strength and an area to watch",
        summary=f"Under the current evaluation framework, {_dimension_name(strength, locale).lower()} is strongest while {_dimension_name(weakness, locale).lower()} needs relatively more attention.",
        key_points=[
            {"title": "Main strength", "detail": f"{_dimension_name(strength, locale)} is the highest current dimension.", "tone": "positive"},
            {"title": "Area to watch", "detail": f"{_dimension_name(weakness, locale)} is the lowest current dimension.", "tone": "attention"},
        ],
        bottom_line="You can ask about strengths, weaknesses, ranking, or directions worth exploring.",
    )


def _parse_prompt(
    prompt: str,
) -> tuple[dict[str, Any], str, SupportedLocale] | None:
    marker = "AUTHORITATIVE CONTEXT\n"
    start = prompt.find(marker)
    if start < 0:
        return None
    raw = prompt[start + len(marker):].lstrip()
    try:
        payload, end = json.JSONDecoder().raw_decode(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    question_marker = "USER QUESTION\n"
    question_start = raw.find(question_marker, end)
    question = raw[question_start + len(question_marker):].strip() if question_start >= 0 else ""
    locale: SupportedLocale = (
        "zh-CN" if "OUTPUT LANGUAGE: Simplified Chinese (zh-CN)." in prompt else "en"
    )
    return payload, question, locale


def _question_intent(question: str) -> str:
    normalized = question.lower()
    groups = (
        ("weakness", ("短板", "不足", "弱项", "问题", "weakness", "weakest", "shortcoming", "improve")),
        ("ranking", ("排名", "第几", "rank", "ranking", "why so high", "why first")),
        ("development", ("发展什么", "发展方向", "未来", "适合", "关注什么方向", "develop", "future", "direction", "suitable")),
        ("strength", ("优势", "最好", "突出", "特别好", "擅长", "strength", "strongest", "stand out", "best")),
    )
    for intent, terms in groups:
        if any(term in normalized for term in terms):
            return intent
    return "overview"


def _scores(context: dict[str, Any]) -> dict[str, float]:
    raw = context.get("scores", {})
    return {
        "overall": float(raw.get("overall", 0)),
        "regional_rank": float(raw.get("regional_rank", 0)),
        **{key: float(raw.get(key, 0)) for key in DIMENSIONS},
    }


def _strongest_dimension(context: dict[str, Any]) -> DimensionKey:
    scores = _scores(context)
    return max(DIMENSIONS, key=lambda key: scores[key])


def _weakest_dimension(context: dict[str, Any]) -> DimensionKey:
    scores = _scores(context)
    return min(DIMENSIONS, key=lambda key: scores[key])


def _drivers(context: dict[str, Any]) -> list[str]:
    engine = context.get("analysis_engine", {})
    values = engine.get("major_indicator_drivers", []) if isinstance(engine, dict) else []
    drivers = [str(value) for value in values if str(value).strip()]
    return drivers or ["Current dimension scores"]


def _borough_name(context: dict[str, Any]) -> str:
    borough = context.get("borough", {})
    return str(borough.get("name", "Selected borough"))


def _dimension_name(key: DimensionKey, locale: SupportedLocale) -> str:
    labels = {
        "economic": _text(locale, "Economic vitality", "经济活力"),
        "social": _text(locale, "Public services", "公共服务"),
        "ecological": _text(locale, "Ecological environment", "生态环境"),
    }
    return labels[key]


def _positioning(context: dict[str, Any], locale: SupportedLocale) -> dict[str, str]:
    scores = _scores(context)
    ordered = sorted(DIMENSIONS, key=lambda key: scores[key], reverse=True)
    strongest, second = ordered[:2]
    balanced = scores[strongest] - scores[second] <= 8
    if balanced:
        label = _text(locale, "Balanced urban profile", "均衡型城市区域")
        description = _text(
            locale,
            f"Its {_dimension_name(strongest, locale).lower()} and {_dimension_name(second, locale).lower()} scores are relatively close.",
            f"其{_dimension_name(strongest, locale)}与{_dimension_name(second, locale)}表现相对接近。",
        )
    else:
        label = {
            "economic": _text(locale, "Economic-activity-led area", "经济活力支撑型区域"),
            "social": _text(locale, "Service-connected urban area", "公共服务支撑型区域"),
            "ecological": _text(locale, "Environment-led urban area", "生态环境支撑型区域"),
        }[strongest]
        description = _text(
            locale,
            f"Its current profile is led by {_dimension_name(strongest, locale).lower()}.",
            f"其当前特征主要由{_dimension_name(strongest, locale)}表现支撑。",
        )
    return {"borough_name": _borough_name(context), "label": label, "description": description}


def _comparison_advantage(
    key: DimensionKey, name: str, other_name: str, locale: SupportedLocale
) -> dict[str, str]:
    dimension = _dimension_name(key, locale)
    explanation = _text(
        locale,
        f"{name} has the higher supplied {dimension.lower()} score than {other_name}.",
        f"{name}的{dimension}得分高于{other_name}。",
    )
    return {"dimension": dimension, "explanation": explanation}


def _profile_advantage(
    key: DimensionKey, name: str, locale: SupportedLocale
) -> dict[str, str]:
    dimension = _dimension_name(key, locale)
    return {
        "dimension": dimension,
        "explanation": _text(
            locale,
            f"{dimension} is the strongest dimension within {name}'s current profile.",
            f"{dimension}是{name}自身表现最突出的维度。",
        ),
    }


def _rank_statement(rank: int, locale: SupportedLocale) -> str:
    if rank <= 3:
        return _text(locale, "the borough performs near the top of the ranking.", "该区域综合表现位于前列。")
    if rank <= 10:
        return _text(locale, "the borough performs around the middle of the ranking.", "该区域表现处于中等水平。")
    return _text(locale, "the borough has further room to improve.", "该区域仍存在进一步提升空间。")


def _format_score(value: float) -> str:
    return f"{float(value):.1f}"


def _text(locale: SupportedLocale, english: str, chinese: str) -> str:
    return chinese if locale == "zh-CN" else english
