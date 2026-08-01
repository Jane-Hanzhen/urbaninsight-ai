from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


@dataclass(frozen=True)
class IndicatorMetadata:
    english_name: str
    chinese_name: str


INDICATOR_METADATA: dict[str, IndicatorMetadata] = {
    "gdhi_per_head_gbp": IndicatorMetadata("GDHI per head", "人均可支配收入"),
    "business_density_per_1000": IndicatorMetadata("Business density", "商业密度"),
    "house_price_earnings_ratio_reverse": IndicatorMetadata(
        "Housing affordability", "住房负担能力"
    ),
    "police_mean": IndicatorMetadata("Police provision", "警务资源"),
    "convenient_service_mean": IndicatorMetadata(
        "Convenient services", "便民服务可达性"
    ),
    "cultural_mean": IndicatorMetadata("Cultural amenities", "文化设施可达性"),
    "medical_mean": IndicatorMetadata("Medical resources", "医疗资源可达性"),
    "bus_mean": IndicatorMetadata("Bus accessibility", "公交可达性"),
    "ndvi_mean": IndicatorMetadata("NDVI", "植被指数"),
    "wet_mean": IndicatorMetadata("Wetness index", "湿度指数"),
    "landscape_index": IndicatorMetadata("Landscape index", "景观指数"),
    "household_waste_recycling_rate_pct": IndicatorMetadata(
        "Household waste recycling rate", "生活垃圾回收率"
    ),
}


def indicator_name(key: str, locale: str) -> str:
    metadata = INDICATOR_METADATA.get(key)
    if metadata is None:
        return key.replace("_", " ").strip().capitalize()
    return metadata.chinese_name if locale == "zh-CN" else metadata.english_name


def indicator_labels(locale: str) -> dict[str, str]:
    return {key: indicator_name(key, locale) for key in INDICATOR_METADATA}


def format_indicator_value(key: str, value: Any) -> str:
    numeric = float(value)
    if key == "gdhi_per_head_gbp":
        return f"GBP {numeric:,.0f}"
    if key == "household_waste_recycling_rate_pct":
        return f"{numeric:.1f}%"
    return f"{numeric:,.3f}".rstrip("0").rstrip(".")


def replace_internal_indicator_names(text: str, locale: str) -> str:
    result = text
    for key in sorted(INDICATOR_METADATA, key=len, reverse=True):
        result = re.sub(
            rf"(?<![A-Za-z0-9_]){re.escape(key)}(?![A-Za-z0-9_])",
            indicator_name(key, locale),
            result,
        )
    return re.sub(
        r"(?<![A-Za-z0-9_])[a-z][a-z0-9]*(?:_[a-z0-9]+)+(?![A-Za-z0-9_])",
        lambda match: match.group(0).replace("_", " "),
        result,
    )
