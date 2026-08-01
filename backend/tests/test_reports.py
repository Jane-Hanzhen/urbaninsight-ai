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


def markdown_payload(*, locale: str = "en", ai_applied: bool = False) -> dict[str, object]:
    payload = report_payload(locale=locale, ai_applied=ai_applied)
    payload["include_ai_insights"] = ai_applied
    payload["previous_context"] = []
    payload["analysis_result"] = {
        "borough_id": "E09000007",
        "overall_score": 72.4,
        "regional_rank": 4,
        "economic_score": 68.2,
        "social_score": 79.5,
        "ecological_score": 61.1,
        "contribution_json": {
            "dimensions": {"Economic": 31.0, "Social": 44.0, "Ecological": 25.0}
        },
    }
    return payload


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


class MarkdownReportEndpointTests(unittest.TestCase):
    def test_mock_analysis_snapshot_exports_without_provider_call(self) -> None:
        client = TestClient(app)
        with (
            patch("app.main._context_or_404", return_value=report_context()),
            patch(
                "app.main.generate_text",
                side_effect=AssertionError("Markdown export called the mock provider"),
            ),
            patch(
                "app.main.generate_live_text",
                side_effect=AssertionError("Markdown export called a live provider"),
            ),
        ):
            response = client.post("/ai/report", json=markdown_payload())

        self.assertEqual(response.status_code, 200)
        content = response.json()["content"]
        self.assertTrue(content.startswith("# UrbanInsight Basic Analysis Report"))
        self.assertIn("**Overall score:** 72.4", content)
        self.assertIn("## Recommendations", content)

    def test_live_ai_snapshot_exports_without_second_provider_call(self) -> None:
        client = TestClient(app)
        with (
            patch("app.main._context_or_404", return_value=report_context()),
            patch(
                "app.main.generate_text",
                side_effect=AssertionError("Markdown export called the configured provider"),
            ),
            patch(
                "app.main.generate_live_text",
                side_effect=AssertionError("Markdown export called the completed provider"),
            ),
        ):
            response = client.post(
                "/ai/report",
                json=markdown_payload(locale="zh-CN", ai_applied=True),
            )

        self.assertEqual(response.status_code, 200)
        content = response.json()["content"]
        self.assertTrue(content.startswith("# UrbanInsight AI 深度分析报告"))
        self.assertIn("**AI Provider:** deepseek", content)
        self.assertIn("Markdown 导出不会重新计算统计结果或再次调用模型", content)


if __name__ == "__main__":
    unittest.main()
