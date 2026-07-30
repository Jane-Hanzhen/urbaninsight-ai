from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.ai.providers.mock_provider import MOCK_INSIGHTS, MOCK_INSIGHTS_ZH_CN
from app.main import app


def report_context() -> dict[str, object]:
    return {
        "borough": {"id": "E09000007", "name": "Camden", "region": "London"},
        "scores": {
            "overall": 72.4,
            "regional_rank": 4,
            "economic": 68.2,
            "social": 79.5,
            "ecological": 61.1,
        },
        "indicators": {
            "gdhi_per_head_gbp": 58440,
            "business_density_per_1000": 179.79,
            "ndvi_mean": 0.245,
            "household_waste_recycling_rate_pct": 28.0,
        },
        "analysis_engine": {
            "method": "PCA-weighted TOPSIS",
            "dimension_contributions": {
                "Economic": 31.0,
                "Social": 44.0,
                "Ecological": 25.0,
            },
            "indicator_contributions": {},
            "pca_weights": {},
            "pca": {"components": 4},
            "topsis": {"overall_score": 72.4, "regional_rank": 4},
        },
    }


def report_payload(*, locale: str = "en", ai_applied: bool = False) -> dict[str, object]:
    insights = MOCK_INSIGHTS_ZH_CN if locale == "zh-CN" else MOCK_INSIGHTS
    return {
        "borough_id": "E09000007",
        "locale": locale,
        "analysis_mode": "ai" if ai_applied else "basic",
        "ai_insights_requested": ai_applied,
        "ai_insights_applied": ai_applied,
        "ai_provider": "deepseek" if ai_applied else None,
        "ai_model": "deepseek-test" if ai_applied else None,
        "ai_error": None,
        "insights": insights.model_dump(),
    }


class PDFReportEndpointTests(unittest.TestCase):
    def test_basic_pdf_uses_completed_payload_without_ai_call(self) -> None:
        client = TestClient(app)
        with (
            patch("app.main._context_or_404", return_value=report_context()),
            patch(
                "app.main.generate_insights",
                side_effect=AssertionError("PDF export called the AI provider"),
            ),
            patch(
                "app.main.generate_text",
                side_effect=AssertionError("PDF export called the AI provider"),
            ),
        ):
            response = client.post("/reports/pdf", json=report_payload())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/pdf")
        self.assertIn("Camden_basic_report.pdf", response.headers["content-disposition"])
        self.assertTrue(response.content.startswith(b"%PDF-"))
        self.assertGreater(len(response.content), 5_000)

    def test_chinese_ai_pdf_is_embedded_and_uses_completed_metadata(self) -> None:
        client = TestClient(app)
        with (
            patch("app.main._context_or_404", return_value=report_context()),
            patch(
                "app.main.generate_insights",
                side_effect=AssertionError("PDF export called the AI provider"),
            ),
            patch(
                "app.main.generate_text",
                side_effect=AssertionError("PDF export called the AI provider"),
            ),
        ):
            response = client.post(
                "/reports/pdf",
                json=report_payload(locale="zh-CN", ai_applied=True),
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Camden_ai_report.pdf", response.headers["content-disposition"])
        self.assertTrue(response.content.startswith(b"%PDF-"))
        self.assertGreater(len(response.content), 10_000)


if __name__ == "__main__":
    unittest.main()
