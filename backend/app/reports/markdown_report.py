from __future__ import annotations

from typing import Any

from ..indicators import format_indicator_value, indicator_name
from ..ai.report_builder import report_title
from ..ai.schemas import AnalysisInsights, ReportRequest


def build_markdown_report(context: dict[str, Any], request: ReportRequest) -> str:
    insights = request.insights
    if insights is None or request.ai_insights_applied is None:
        raise ValueError("Completed report data is required")

    locale = request.locale
    scores = context["scores"]
    engine = context["analysis_engine"]
    title = report_title(locale, request.ai_insights_applied)
    mode = _label(locale, "AI in-depth analysis", "AI 深度分析") if request.ai_insights_applied else _label(locale, "Basic analysis", "基础分析")

    sections = [
        f"# {title}",
        "",
        f"**{_label(locale, 'Borough', '行政区')}:** {_text(context['borough']['name'])}",
        f"**{_label(locale, 'Analysis mode', '分析模式')}:** {mode}",
    ]
    if request.ai_insights_applied and request.ai_provider:
        sections.append(f"**AI Provider:** {_text(request.ai_provider)}")
        if request.ai_model:
            sections.append(f"**{_label(locale, 'Model', '模型')}:** {_text(request.ai_model)}")

    sections.extend(
        [
            "",
            f"## {_label(locale, 'Executive Summary', '执行摘要')}",
            "",
            _text(insights.executive_summary),
            "",
            f"- **{_label(locale, 'Overall score', '综合得分')}:** {float(scores['overall']):.1f}",
            f"- **{_label(locale, 'London rank', '伦敦排名')}:** #{int(scores['regional_rank'])}",
            f"- **{_label(locale, 'Method', '评价方法')}:** PCA-weighted TOPSIS",
            "",
            f"## {_label(locale, 'Regional Evaluation', '区域评价')}",
            "",
            _text(insights.ranking_explanation),
            "",
            f"### {_label(locale, 'Dimension Scores', '维度得分')}",
            "",
            f"- {_label(locale, 'Economic', '经济')}: {float(scores['economic']):.1f}",
            f"- {_label(locale, 'Social', '社会')}: {float(scores['social']):.1f}",
            f"- {_label(locale, 'Ecological', '生态')}: {float(scores['ecological']):.1f}",
            "",
            f"### {_label(locale, 'PCA Contributions', 'PCA 贡献度')}",
            "",
            *_contribution_lines(engine.get("dimension_contributions", {}), locale),
            "",
            f"## {_label(locale, 'Key Indicators', '关键指标')}",
            "",
            *_indicator_lines(context["indicators"], locale),
            "",
            f"## {_label(locale, 'Main Drivers', '主要驱动因素')}",
            "",
            *_insight_lines(insights.main_drivers),
            "",
            _text(insights.indicator_interpretation),
            "",
            f"## {_label(locale, 'Strengths', '优势')}",
            "",
            *_insight_lines(insights.strengths),
            "",
            f"## {_label(locale, 'Weaknesses', '短板')}",
            "",
            *_insight_lines(insights.weaknesses),
            "",
            f"## {_label(locale, 'Recommendations', '建议')}",
            "",
            *_recommendation_lines(insights),
            "",
            f"## {_label(locale, 'Method and Disclaimer', '方法与免责声明')}",
            "",
            _method_note(locale, request),
        ]
    )
    return "\n".join(sections).strip() + "\n"


def _contribution_lines(values: dict[str, Any], locale: str) -> list[str]:
    labels = {"Economic": "经济", "Social": "社会", "Ecological": "生态"}
    return [
        f"- {labels.get(name, name) if locale == 'zh-CN' else name}: {float(value):.1f}%"
        for name, value in values.items()
    ]


def _indicator_lines(indicators: dict[str, Any], locale: str) -> list[str]:
    return [f"- **{_text(indicator_name(key, locale))}:** {format_indicator_value(key, value)}" for key, value in indicators.items()]


def _insight_lines(items: list[Any]) -> list[str]:
    return [f"- **{_text(item.title)}:** {_text(item.detail)}" for item in items]


def _recommendation_lines(insights: AnalysisInsights) -> list[str]:
    return [f"- **{item.priority} — {_text(item.title)}:** {_text(item.detail)}" for item in insights.recommendations]


def _method_note(locale: str, request: ReportRequest) -> str:
    if locale == "zh-CN":
        mode = "本报告包含本次分析已完成的 AI 深度解读。" if request.ai_insights_applied else "本报告使用本次已完成的基础分析解读。"
        fallback = " 本次请求的 AI 深度解读未成功应用。" if request.ai_insights_requested and not request.ai_insights_applied else ""
        return f"PCA 与 TOPSIS 结果来自分析引擎已存储的权威结果，Markdown 导出不会重新计算统计结果或再次调用模型。{mode}{fallback} 本报告仅用于辅助研究与决策。"
    mode = "This report includes the AI interpretation completed for this analysis." if request.ai_insights_applied else "This report uses the completed basic-analysis interpretation."
    fallback = " The requested AI interpretation was not successfully applied." if request.ai_insights_requested and not request.ai_insights_applied else ""
    return f"PCA and TOPSIS values are authoritative stored Analysis Engine results. Markdown export neither recalculates statistics nor calls a model again. {mode}{fallback} This report supports research and decision-making."


def _text(value: Any) -> str:
    return " ".join(str(value).split()).replace("|", "\\|")


def _label(locale: str, english: str, chinese: str) -> str:
    return chinese if locale == "zh-CN" else english
