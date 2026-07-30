from __future__ import annotations

from typing import Any

from ..repository import get_analysis_result, get_borough, get_indicators


class AnalysisContextError(ValueError):
    pass


def build_analysis_context(borough_id: str) -> dict[str, Any]:
    borough = get_borough(borough_id)
    indicators = get_indicators(borough_id)
    analysis = get_analysis_result(borough_id)
    if borough is None:
        raise AnalysisContextError("Borough not found")
    if indicators is None:
        raise AnalysisContextError("Indicators not found")
    if analysis is None:
        raise AnalysisContextError("Analysis results not found")

    contribution = analysis["contribution_json"]
    return {
        "borough": {"id": borough["id"], "name": borough["name"], "region": borough["region"]},
        "scores": {
            "overall": analysis["overall_score"],
            "regional_rank": analysis["regional_rank"],
            "economic": analysis["economic_score"],
            "social": analysis["social_score"],
            "ecological": analysis["ecological_score"],
        },
        "indicators": {
            key: value
            for key, value in indicators.items()
            if key not in {"borough_id", "updated_at"}
        },
        "analysis_engine": {
            "method": "PCA-weighted TOPSIS",
            "dimension_contributions": contribution.get("dimensions", {}),
            "indicator_contributions": contribution.get("indicators", {}),
            "pca_weights": contribution.get("weights", {}),
            "pca": contribution.get("pca", {}),
            "topsis": {
                "overall_score": analysis["overall_score"],
                "regional_rank": analysis["regional_rank"],
            },
        },
    }
