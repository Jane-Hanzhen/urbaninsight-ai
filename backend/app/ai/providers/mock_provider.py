from __future__ import annotations

import random
import time
from collections.abc import Callable

from ..schemas import AnalysisInsights
from .base import AIProvider


MOCK_INSIGHTS = AnalysisInsights.model_validate(
    {
        "executive_summary": "This borough combines strong access to urban services with several practical opportunities for more balanced development.",
        "ranking_explanation": "Its regional position comes directly from the supplied Analysis Engine scores and contributions; no independent ranking was calculated during interpretation.",
        "main_drivers": [
            {
                "title": "Service accessibility",
                "detail": "The supplied service and mobility indicators are important factors in the borough's evaluated performance.",
            },
            {
                "title": "Environmental quality",
                "detail": "Vegetation, landscape, and recycling indicators shape the ecological dimension.",
            },
        ],
        "strengths": [
            {
                "title": "Connected urban services",
                "detail": "Residents benefit from a broad mix of services and transport connections.",
            },
            {
                "title": "Diverse local activity",
                "detail": "The indicator profile suggests a varied and active urban environment.",
            },
        ],
        "weaknesses": [
            {
                "title": "Uneven environmental performance",
                "detail": "Some ecological indicators leave room for more consistent neighbourhood quality.",
            },
            {
                "title": "Affordability pressure",
                "detail": "Economic strengths should be considered alongside the supplied housing affordability indicator.",
            },
        ],
        "indicator_interpretation": "The stored indicators show a mixed profile: access and activity support urban potential, while affordability and environmental outcomes deserve continued attention.",
        "recommendations": [
            {
                "title": "Improve green connections",
                "detail": "Connect existing green assets through street planting and accessible walking routes.",
                "priority": "High",
            },
            {
                "title": "Protect inclusive access",
                "detail": "Target investment so strong services remain accessible across neighbourhoods.",
                "priority": "Medium",
            },
        ],
    }
)

MOCK_INSIGHTS_ZH_CN = AnalysisInsights.model_validate(
    {
        "executive_summary": "该行政区拥有良好的城市服务可达性，同时也存在促进均衡发展的实际机会。",
        "ranking_explanation": "其区域排名直接来自分析引擎提供的得分与贡献结果；解读过程没有独立重新计算排名。",
        "main_drivers": [
            {
                "title": "服务可达性",
                "detail": "现有服务与交通指标是该行政区评估表现的重要影响因素。",
            },
            {
                "title": "环境质量",
                "detail": "植被、景观和回收指标共同影响生态维度表现。",
            },
        ],
        "strengths": [
            {
                "title": "城市服务连接良好",
                "detail": "居民能够使用多样化的服务和交通连接。",
            },
            {
                "title": "区域活动多元",
                "detail": "指标组合显示该地区具有多样且活跃的城市环境。",
            },
        ],
        "weaknesses": [
            {
                "title": "环境表现不均衡",
                "detail": "部分生态指标显示街区环境质量仍有提升空间。",
            },
            {
                "title": "住房负担压力",
                "detail": "在评估经济优势时，也应关注现有住房负担能力指标。",
            },
        ],
        "indicator_interpretation": "现有指标呈现混合特征：服务与活动水平支撑城市潜力，而住房负担和环境表现仍需持续关注。",
        "recommendations": [
            {
                "title": "改善绿色连接",
                "detail": "通过街道绿化和便捷步行路线连接现有绿色资源。",
                "priority": "High",
            },
            {
                "title": "保障包容性服务",
                "detail": "有针对性地投入资源，确保各街区都能使用优质服务与交通。",
                "priority": "Medium",
            },
        ],
    }
)

MOCK_CHAT_RESPONSE = (
    "Based on the current borough context, the strongest opportunities come from building on "
    "existing service access while addressing the weaker affordability and environmental signals."
)
MOCK_COMPARISON_RESPONSE = (
    "The selected borough and comparison borough differ across their stored dimension scores, "
    "indicator values, and contribution profiles. The selected borough's advantage is stronger "
    "urban access, while the comparison highlights different environmental and economic trade-offs."
)
MOCK_REPORT_RESPONSE = """# UrbanInsight AI In-depth Analysis Report

## Executive Summary

The borough shows a balanced urban profile with strong service access and identifiable opportunities.

## Regional Evaluation

Scores and ranking are taken directly from the stored Analysis Engine context.

## Key Indicators

Service, mobility, affordability, vegetation, and recycling indicators shape the evaluation.

## Strengths and Weaknesses

Connected services are a strength; affordability and uneven environmental quality require attention.

## Recommendations

- Improve green connections between neighbourhood assets.
- Protect inclusive access to services and transport.
"""

MOCK_CHAT_RESPONSE_ZH_CN = "根据当前行政区背景，最值得关注的机会是发挥现有服务可达性优势，同时改善住房负担与环境方面的较弱信号。"
MOCK_COMPARISON_RESPONSE_ZH_CN = (
    "所选行政区与对比行政区在现有维度得分、指标值和贡献结构上存在差异。"
    "所选行政区的优势是城市服务可达性较强，而对比地区呈现出不同的环境与经济权衡。"
)
MOCK_REPORT_RESPONSE_ZH_CN = """# UrbanInsight AI 深度分析报告

## 执行摘要

该行政区拥有较为均衡的城市特征，服务可达性良好，并存在明确的提升机会。

## 区域评估

得分与排名直接取自分析引擎存储的结果。

## 关键指标

服务、交通、住房负担、植被和回收指标共同影响评估结果。

## 优势与短板

服务连接是主要优势；住房负担和环境质量不均衡值得关注。

## 建议

- 改善街区绿色资源之间的连接。
- 保障居民公平使用服务与交通。
"""


class MockProvider(AIProvider):
    def __init__(self, delay: Callable[[float], None] | None = None) -> None:
        self._delay = delay or time.sleep

    @property
    def name(self) -> str:
        return "mock"

    @property
    def model(self) -> str:
        return "urbaninsight-mock"

    def is_configured(self) -> bool:
        return True

    def generate_insights(self, prompt: str) -> AnalysisInsights:
        self._simulate_latency()
        insights = MOCK_INSIGHTS_ZH_CN if _requests_simplified_chinese(prompt) else MOCK_INSIGHTS
        return insights.model_copy(deep=True)

    def generate_text(self, prompt: str) -> str:
        self._simulate_latency()
        is_chinese = _requests_simplified_chinese(prompt)
        if prompt.startswith("Write a polished Markdown report"):
            return MOCK_REPORT_RESPONSE_ZH_CN if is_chinese else MOCK_REPORT_RESPONSE
        if "Compare the selected borough with the comparison borough" in prompt:
            return MOCK_COMPARISON_RESPONSE_ZH_CN if is_chinese else MOCK_COMPARISON_RESPONSE
        return MOCK_CHAT_RESPONSE_ZH_CN if is_chinese else MOCK_CHAT_RESPONSE

    def _simulate_latency(self) -> None:
        self._delay(random.uniform(0.3, 0.8))


def _requests_simplified_chinese(prompt: str) -> bool:
    return "OUTPUT LANGUAGE: Simplified Chinese (zh-CN)." in prompt
