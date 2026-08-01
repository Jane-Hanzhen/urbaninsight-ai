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


def conversation_payload(*, locale: str = "en") -> dict[str, object]:
    chinese = locale == "zh-CN"
    return {
        "borough_id": "E09000007",
        "locale": locale,
        "messages": [
            {
                "role": "user",
                "content": "这里哪方面表现特别好？" if chinese else "What stands out here?",
            },
            {
                "role": "assistant",
                "content": "服务可达性较强。" if chinese else "Service access stands out.",
                "answer": {
                    "response_type": "insight",
                    "headline": "核心发现" if chinese else "Core finding",
                    "summary": "服务与交通条件形成支持。" if chinese else "Services and transport provide support.",
                    "key_points": [{
                        "title": "公共服务" if chinese else "Public services",
                        "detail": "当前指标体现出相对优势。" if chinese else "Current indicators show a relative advantage.",
                        "tone": "positive",
                    }],
                    "bottom_line": "这是当前评价体系下的观察。" if chinese else "This is an observation under the current framework.",
                    "limitations": None,
                },
            },
            {
                "role": "user",
                "content": "比较 Camden" if chinese else "Compare Camden",
            },
            {
                "role": "assistant",
                "content": "两个区域优势不同。" if chinese else "The areas have different strengths.",
                "answer": {
                    "response_type": "comparison",
                    "headline": "比较结论" if chinese else "Comparison finding",
                    "summary": "两地呈现不同特征。" if chinese else "The two areas show different profiles.",
                    "primary_advantages": [{"dimension": "公共服务" if chinese else "Public services", "explanation": "服务条件更突出。" if chinese else "Service conditions stand out."}],
                    "comparison_advantages": [{"dimension": "生态环境" if chinese else "Environment", "explanation": "绿色环境指标更突出。" if chinese else "Green indicators stand out."}],
                    "primary_positioning": {"borough_name": "City of London", "label": "服务驱动型" if chinese else "Service-led", "description": "服务基础较强。" if chinese else "A stronger service base."},
                    "comparison_positioning": {"borough_name": "Camden", "label": "环境均衡型" if chinese else "Environmentally balanced", "description": "环境表现更均衡。" if chinese else "A more balanced environment."},
                    "decision_note": "应结合实际目标判断。" if chinese else "Interpret the result against the user's priorities.",
                    "evidence": [{"label": "综合得分" if chinese else "Overall score", "primary_value": "80", "comparison_value": "33.9"}],
                },
            },
        ],
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


class ConversationPDFEndpointTests(unittest.TestCase):
    def test_conversation_pdf_preserves_order_without_ai_call(self) -> None:
        client = TestClient(app)
        with (
            patch("app.main._context_or_404", return_value=report_context()),
            patch("app.main.generate_text", side_effect=AssertionError("Conversation export called AI")),
            patch("app.main.generate_live_text", side_effect=AssertionError("Conversation export called AI")),
        ):
            response = client.post("/conversations/pdf", json=conversation_payload())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/pdf")
        self.assertIn("Camden_Conversation.pdf", response.headers["content-disposition"])
        self.assertTrue(response.content.startswith(b"%PDF-"))
        self.assertGreater(len(response.content), 3_000)

    def test_chinese_conversation_pdf_embeds_structured_content(self) -> None:
        client = TestClient(app)
        with patch("app.main._context_or_404", return_value=report_context()):
            response = client.post(
                "/conversations/pdf", json=conversation_payload(locale="zh-CN")
            )

        self.assertEqual(response.status_code, 200)
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
        self.assertIn("**GDHI per head:** GBP 58,440", content)
        self.assertNotIn("gdhi_per_head_gbp", content)
        self.assertNotIn("business_density_per_1000", content)
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
        self.assertIn("**人均可支配收入:** GBP 58,440", content)
        self.assertIn("**商业密度:** 179.79", content)
        self.assertNotIn("gdhi_per_head_gbp", content)
        self.assertNotIn("business_density_per_1000", content)
        self.assertIn("Markdown 导出不会重新计算统计结果或再次调用模型", content)


if __name__ == "__main__":
    unittest.main()
