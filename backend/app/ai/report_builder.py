from __future__ import annotations

from .schemas import SupportedLocale


REPORT_TITLES: dict[SupportedLocale, dict[bool, str]] = {
    "en": {
        False: "UrbanInsight Basic Analysis Report",
        True: "UrbanInsight AI In-depth Analysis Report",
    },
    "zh-CN": {
        False: "UrbanInsight 基础分析报告",
        True: "UrbanInsight AI 深度分析报告",
    },
}


def report_title(locale: SupportedLocale, include_ai_insights: bool) -> str:
    return REPORT_TITLES[locale][include_ai_insights]


def normalize_report_title(
    content: str, locale: SupportedLocale, include_ai_insights: bool
) -> str:
    title = f"# {report_title(locale, include_ai_insights)}"
    lines = content.lstrip().splitlines()
    if lines and lines[0].startswith("# "):
        lines[0] = title
        return "\n".join(lines).strip()
    return f"{title}\n\n{content.strip()}"
