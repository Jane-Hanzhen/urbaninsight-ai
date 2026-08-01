from __future__ import annotations

import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.ai.prompt_builder import (
    SYSTEM_INSTRUCTIONS,
    analysis_prompt,
    chat_prompt,
    comparison_prompt,
    report_prompt,
)
from app.ai.output_formatter import sanitize_ai_text, sanitize_analysis_insights
from app.ai.providers.base import ProviderConfigurationError, ProviderResponseError
from app.ai.providers.deepseek_provider import DeepSeekProvider
from app.ai.providers.factory import (
    configured_mode,
    configured_model,
    configured_provider,
    create_provider,
    is_configured,
)
from app.ai.providers.mock_provider import (
    MOCK_CHAT_RESPONSE,
    MOCK_CHAT_RESPONSE_ZH_CN,
    MOCK_COMPARISON_RESPONSE,
    MOCK_COMPARISON_RESPONSE_ZH_CN,
    MOCK_INSIGHTS,
    MOCK_INSIGHTS_ZH_CN,
    MOCK_REPORT_RESPONSE,
    MOCK_REPORT_RESPONSE_ZH_CN,
    MockProvider,
)
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.providers.qwen_provider import QwenProvider
from app.main import _format_provider_error, _redact_openai_error
from app.main import app


def sample_context(name: str, score: float, rank: int) -> dict[str, object]:
    return {
        "borough": {"id": name.lower(), "name": name, "region": "London"},
        "scores": {
            "overall": score,
            "regional_rank": rank,
            "economic": 71.2,
            "social": 68.4,
            "ecological": 55.1,
        },
        "indicators": {"gdhi_per_head_gbp": 32100.0, "ndvi_mean": 0.42},
        "analysis_engine": {
            "method": "PCA-weighted TOPSIS",
            "dimension_contributions": {"Economic": 41.2},
            "indicator_contributions": {"gdhi_per_head_gbp": 8.4},
            "pca_weights": {"gdhi_per_head_gbp": 0.12},
            "pca": {"components": 4},
            "topsis": {"overall_score": score, "regional_rank": rank},
        },
    }


def valid_insights_payload() -> dict[str, object]:
    insight = {"title": "Evidence", "detail": "Grounded interpretation."}
    return {
        "executive_summary": "A concise summary.",
        "ranking_explanation": "The stored rank reflects the supplied results.",
        "main_drivers": [insight, insight],
        "strengths": [insight, insight],
        "weaknesses": [insight, insight],
        "indicator_interpretation": "Indicators are interpreted without recalculation.",
        "recommendations": [
            {**insight, "priority": "High"},
            {**insight, "priority": "Medium"},
        ],
    }


def valid_chat_payload() -> dict[str, object]:
    return {
        "response_type": "insight",
        "headline": "A clear finding",
        "summary": "A concise answer grounded in the supplied context.",
        "key_points": [
            {"title": "Evidence", "detail": "A supported point.", "tone": "positive"}
        ],
        "bottom_line": "A practical takeaway.",
        "limitations": None,
    }


def valid_compare_payload() -> dict[str, object]:
    positioning = {
        "borough_name": "Camden",
        "label": "Balanced urban area",
        "description": "An interpretive positioning statement.",
    }
    return {
        "response_type": "comparison",
        "headline": "The boroughs have different strengths",
        "summary": "A concise comparison.",
        "primary_advantages": [{"dimension": "Social", "explanation": "Stronger access."}],
        "comparison_advantages": [{"dimension": "Ecological", "explanation": "Stronger environment."}],
        "primary_positioning": positioning,
        "comparison_positioning": {**positioning, "borough_name": "Westminster"},
        "decision_note": "Choose based on the decision priority.",
        "evidence": [],
    }


def completion(content: str) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


class PromptBuilderTests(unittest.TestCase):
    def test_analysis_prompt_includes_authoritative_engine_results(self) -> None:
        prompt = analysis_prompt(sample_context("Camden", 78.6, 3), [])

        self.assertIn('"name": "Camden"', prompt)
        self.assertIn('"overall": 78.6', prompt)
        self.assertIn('"regional_rank": 3', prompt)
        self.assertIn('"topsis"', prompt)
        self.assertIn('"name": "GDHI per head"', prompt)
        self.assertIn('"major_indicator_drivers"', prompt)
        self.assertNotIn("gdhi_per_head_gbp", prompt)
        self.assertNotIn('"indicator_contributions"', prompt)
        self.assertNotIn('"dimension_contributions"', prompt)
        self.assertNotIn('"pca_summary"', prompt)
        self.assertIn("Do not perform new calculations", prompt)

    def test_chinese_prompt_uses_centralized_human_readable_names(self) -> None:
        prompt = analysis_prompt(sample_context("Camden", 78.6, 3), [], "zh-CN")

        self.assertIn('"name": "人均可支配收入"', prompt)
        self.assertIn('"name": "植被指数"', prompt)
        self.assertNotIn("gdhi_per_head_gbp", prompt)
        self.assertNotIn("ndvi_mean", prompt)

    def test_comparison_prompt_contains_both_boroughs(self) -> None:
        prompt = comparison_prompt(
            sample_context("Camden", 78.6, 3),
            sample_context("Westminster", 82.4, 1),
            [],
        )

        self.assertIn('"selected_borough"', prompt)
        self.assertIn('"comparison_borough"', prompt)
        self.assertIn('"name": "Camden"', prompt)
        self.assertIn('"name": "Westminster"', prompt)
        self.assertIn("Do not derive a new score or ranking", prompt)
        self.assertIn("Do not use\nMarkdown", prompt)
        self.assertIn("under the current evaluation framework", prompt)
        self.assertIn("Never state that one borough is simply better", prompt)
        self.assertIn("no more than one decimal place", prompt)

    def test_chat_prompt_uses_evidence_bounded_language(self) -> None:
        prompt = chat_prompt(sample_context("Camden", 78.6, 3), "What stands out?", [])

        self.assertIn("Do not predict future industries", prompt)
        self.assertIn("claim absolute\ncausation", prompt)
        self.assertIn("Round overall and dimension\nscores to one decimal place", prompt)
        self.assertIn("provides underlying conditions for", prompt)

    def test_all_prompts_include_requested_output_language(self) -> None:
        context = sample_context("Camden", 78.6, 3)

        prompts = (
            analysis_prompt(context, [], "zh-CN"),
            chat_prompt(context, "请解释排名。", [], locale="zh-CN"),
            comparison_prompt(context, sample_context("Westminster", 82.4, 1), [], "zh-CN"),
            report_prompt(context, [], "zh-CN"),
        )

        for prompt in prompts:
            self.assertIn("OUTPUT LANGUAGE: Simplified Chinese (zh-CN).", prompt)

    def test_prompt_defaults_to_english_for_backward_compatibility(self) -> None:
        prompt = analysis_prompt(sample_context("Camden", 78.6, 3), [])

        self.assertIn("OUTPUT LANGUAGE: English (en).", prompt)

    def test_system_instructions_preserve_statistical_boundary(self) -> None:
        self.assertIn("Never calculate, recalculate", SYSTEM_INSTRUCTIONS)
        self.assertIn("immutable facts", SYSTEM_INSTRUCTIONS)
        self.assertIn("Never reveal database field names", SYSTEM_INSTRUCTIONS)
        self.assertIn("Do not list PCA weights", SYSTEM_INSTRUCTIONS)

    def test_output_formatter_replaces_provider_leaks_in_text_and_insights(self) -> None:
        text = "business_density_per_1000, wet_mean, and future_metric_key are drivers."
        insights = MOCK_INSIGHTS.model_copy(
            update={"executive_summary": "gdhi_per_head_gbp is important."}
        )

        self.assertEqual(
            sanitize_ai_text(text, "zh-CN"),
            "商业密度, 湿度指数, and future metric key are drivers.",
        )
        sanitized = sanitize_analysis_insights(insights, "en")
        self.assertEqual(
            sanitized.executive_summary, "GDHI per head is important."
        )

    def test_openai_error_logging_redacts_api_keys(self) -> None:
        message = "Authentication failed for sk-example_secret_123456"
        redacted = _redact_openai_error(message)

        self.assertNotIn("sk-example_secret_123456", redacted)
        self.assertIn("[REDACTED_API_KEY]", redacted)

    def test_provider_error_logging_includes_sanitized_cause(self) -> None:
        try:
            try:
                raise ValueError("bad URL with sk-example_secret_123456")
            except ValueError as cause:
                raise RuntimeError("connection failed") from cause
        except RuntimeError as error:
            formatted = _format_provider_error(error)

        self.assertIn("caused_by=ValueError", formatted)
        self.assertNotIn("sk-example_secret_123456", formatted)


class ProviderConfigurationTests(unittest.TestCase):
    def test_mock_mode_ignores_live_provider_configuration(self) -> None:
        with patch.dict(
            os.environ,
            {"AI_MODE": "mock", "AI_PROVIDER": "unsupported"},
            clear=True,
        ):
            provider = create_provider()
            self.assertIsInstance(provider, MockProvider)
            self.assertEqual(configured_mode(), "mock")
            self.assertEqual(configured_provider(), "mock")
            self.assertEqual(configured_model(), "urbaninsight-mock")
            self.assertTrue(is_configured())

    def test_openai_provider_configuration(self) -> None:
        environment = {
            "AI_PROVIDER": "openai",
            "OPENAI_API_KEY": "test-openai-key",
            "OPENAI_MODEL": "test-openai-model",
        }
        with patch.dict(os.environ, environment, clear=True):
            provider = create_provider()
            self.assertIsInstance(provider, OpenAIProvider)
            self.assertEqual(configured_provider(), "openai")
            self.assertEqual(configured_model(), "test-openai-model")
            self.assertTrue(is_configured())

    def test_qwen_provider_configuration(self) -> None:
        environment = {
            "AI_PROVIDER": "qwen",
            "DASHSCOPE_API_KEY": "test-qwen-key",
            "QWEN_MODEL": "test-qwen-model",
            "QWEN_BASE_URL": "https://qwen.example/v1",
        }
        with patch.dict(os.environ, environment, clear=True):
            provider = create_provider()
            self.assertIsInstance(provider, QwenProvider)
            self.assertEqual(provider.model, "test-qwen-model")
            self.assertEqual(provider._base_url, "https://qwen.example/v1")
            self.assertTrue(provider.is_configured())

    def test_deepseek_provider_configuration(self) -> None:
        environment = {
            "AI_PROVIDER": "deepseek",
            "DEEPSEEK_API_KEY": "test-deepseek-key",
            "DEEPSEEK_MODEL": "test-deepseek-model",
            "DEEPSEEK_BASE_URL": "https://deepseek.example/v1",
        }
        with patch.dict(os.environ, environment, clear=True):
            provider = create_provider()
            self.assertIsInstance(provider, DeepSeekProvider)
            self.assertEqual(configured_provider(), "deepseek")
            self.assertEqual(provider.model, "test-deepseek-model")
            self.assertEqual(provider._base_url, "https://deepseek.example/v1")

    def test_provider_switching_uses_only_ai_provider(self) -> None:
        for name, expected_type in (
            ("openai", OpenAIProvider),
            ("qwen", QwenProvider),
            ("deepseek", DeepSeekProvider),
        ):
            with self.subTest(provider=name):
                with patch.dict(os.environ, {"AI_PROVIDER": name}, clear=True):
                    self.assertIsInstance(create_provider(), expected_type)

    def test_missing_active_provider_key(self) -> None:
        with patch.dict(os.environ, {"AI_PROVIDER": "deepseek"}, clear=True):
            provider = create_provider()
            self.assertFalse(provider.is_configured())
            with self.assertRaisesRegex(ProviderConfigurationError, "AI_PROVIDER=deepseek"):
                provider.generate_text("hello")

    def test_unsupported_provider(self) -> None:
        with patch.dict(os.environ, {"AI_PROVIDER": "unknown"}, clear=True):
            with self.assertRaisesRegex(ProviderConfigurationError, "Unsupported AI provider"):
                create_provider()

    def test_unsupported_mode(self) -> None:
        with patch.dict(os.environ, {"AI_MODE": "offline"}, clear=True):
            with self.assertRaisesRegex(ProviderConfigurationError, "Unsupported AI_MODE"):
                create_provider()

    def test_status_reflects_active_provider(self) -> None:
        environment = {
            "AI_PROVIDER": "deepseek",
            "DEEPSEEK_API_KEY": "test-deepseek-key",
            "DEEPSEEK_MODEL": "deepseek-test",
        }
        with patch.dict(os.environ, environment, clear=True):
            response = TestClient(app).get("/ai/status")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["enabled"])
        self.assertEqual(response.json()["mode"], "live")
        self.assertEqual(response.json()["provider"], "deepseek")
        self.assertEqual(response.json()["model"], "deepseek-test")
        self.assertEqual(response.json()["default_provider"], "deepseek")
        self.assertEqual(response.json()["available_providers"], ["deepseek", "qwen"])


class ProviderGenerationTests(unittest.TestCase):
    def test_mock_provider_never_creates_external_client(self) -> None:
        delays: list[float] = []
        provider = MockProvider(delay=delays.append)

        with patch("app.ai.providers.base.OpenAI", side_effect=AssertionError("SDK used")):
            insights = provider.generate_insights("analysis")
            chat = provider.generate_text("question")

        self.assertEqual(insights, MOCK_INSIGHTS)
        self.assertEqual(chat, MOCK_CHAT_RESPONSE)
        self.assertEqual(len(delays), 2)
        self.assertTrue(all(0.3 <= delay <= 0.8 for delay in delays))

    def test_mock_provider_routes_text_response_types(self) -> None:
        provider = MockProvider(delay=lambda _: None)

        self.assertEqual(provider.generate_text("ordinary question"), MOCK_CHAT_RESPONSE)
        self.assertEqual(
            provider.generate_text(
                "Answer the user's question\nCompare the selected borough with the comparison borough"
            ),
            MOCK_COMPARISON_RESPONSE,
        )
        self.assertEqual(
            provider.generate_text("Write a polished Markdown report from context"),
            MOCK_REPORT_RESPONSE,
        )

    def test_mock_provider_returns_simplified_chinese(self) -> None:
        provider = MockProvider(delay=lambda _: None)
        instruction = "\nOUTPUT LANGUAGE: Simplified Chinese (zh-CN)."

        self.assertEqual(provider.generate_insights(instruction), MOCK_INSIGHTS_ZH_CN)
        self.assertEqual(
            provider.generate_text(f"ordinary question{instruction}"),
            MOCK_CHAT_RESPONSE_ZH_CN,
        )
        self.assertEqual(
            provider.generate_text(
                "Answer the user's question\nCompare the selected borough with the comparison borough"
                f"{instruction}"
            ),
            MOCK_COMPARISON_RESPONSE_ZH_CN,
        )
        self.assertEqual(
            provider.generate_text(
                f"Write a polished Markdown report from context{instruction}"
            ),
            MOCK_REPORT_RESPONSE_ZH_CN,
        )

    def test_mock_mode_endpoints_keep_existing_contracts(self) -> None:
        with patch.dict(os.environ, {"AI_MODE": "mock"}, clear=False):
            with patch("app.ai.providers.mock_provider.time.sleep"):
                client = TestClient(app)
                status = client.get("/ai/status")
                analyze = client.post(
                    "/ai/analyze",
                    json={
                        "borough_id": "E09000007",
                        "include_ai_insights": False,
                        "previous_context": [],
                    },
                )
                chat = client.post(
                    "/ai/chat",
                    json={
                        "borough_id": "E09000007",
                        "previous_context": [],
                        "question": "What stands out?",
                    },
                )
                comparison = client.post(
                    "/ai/compare",
                    json={
                        "borough_id": "E09000007",
                        "compare_borough_id": "E09000033",
                        "previous_context": [],
                    },
                )
                report = client.post(
                    "/ai/report",
                    json={"borough_id": "E09000007", "previous_context": []},
                )

        self.assertEqual(status.json()["provider"], "mock")
        self.assertTrue(status.json()["enabled"])
        self.assertEqual(status.json()["mode"], "mock")
        self.assertEqual(status.json()["model"], "urbaninsight-mock")
        self.assertEqual(status.json()["available_providers"], ["deepseek", "qwen"])
        self.assertEqual(analyze.status_code, 200)
        self.assertEqual(analyze.json()["analysis_mode"], "basic")
        self.assertFalse(analyze.json()["ai_insights_applied"])
        self.assertIn("executive_summary", analyze.json()["insights"])
        self.assertEqual(chat.json()["content"], MOCK_CHAT_RESPONSE)
        self.assertEqual(chat.json()["answer"]["response_type"], "insight")
        self.assertEqual(comparison.json()["content"], MOCK_COMPARISON_RESPONSE)
        self.assertEqual(comparison.json()["answer"]["response_type"], "comparison")
        self.assertTrue(
            report.json()["content"].startswith(
                "# UrbanInsight AI In-depth Analysis Report"
            )
        )

    def test_mock_mode_endpoints_return_requested_simplified_chinese(self) -> None:
        with patch.dict(os.environ, {"AI_MODE": "mock"}, clear=False):
            with patch("app.ai.providers.mock_provider.time.sleep"):
                client = TestClient(app)
                base = {
                    "borough_id": "E09000007",
                    "include_ai_insights": False,
                    "previous_context": [],
                    "locale": "zh-CN",
                }
                analyze = client.post("/ai/analyze", json=base)
                chat = client.post(
                    "/ai/chat", json={**base, "question": "最值得关注的是什么？"}
                )
                comparison = client.post(
                    "/ai/compare",
                    json={**base, "compare_borough_id": "E09000033"},
                )
                report = client.post("/ai/report", json=base)

        self.assertEqual(analyze.status_code, 200)
        self.assertEqual(
            analyze.json()["insights"]["executive_summary"],
            MOCK_INSIGHTS_ZH_CN.executive_summary,
        )
        self.assertEqual(chat.json()["content"], MOCK_CHAT_RESPONSE_ZH_CN)
        self.assertEqual(chat.json()["answer"]["response_type"], "insight")
        self.assertEqual(comparison.json()["content"], MOCK_COMPARISON_RESPONSE_ZH_CN)
        self.assertEqual(comparison.json()["answer"]["response_type"], "comparison")
        self.assertTrue(
            report.json()["content"].startswith(
                "# UrbanInsight 基础分析报告"
            )
        )

    def test_disabled_ai_returns_basic_analysis_without_provider_call(self) -> None:
        with patch("app.main.generate_live_insights") as generate_live_insights:
            response = TestClient(app).post(
                "/ai/analyze",
                json={
                    "borough_id": "E09000007",
                    "include_ai_insights": False,
                },
            )

        payload = response.json()
        self.assertEqual(payload["analysis_mode"], "basic")
        self.assertFalse(payload["ai_insights_requested"])
        self.assertFalse(payload["ai_insights_applied"])
        self.assertIsNone(payload["ai_provider"])
        self.assertIsNone(payload["ai_model"])
        self.assertIn("executive_summary", payload["insights"])
        generate_live_insights.assert_not_called()

    def test_unavailable_ai_preserves_successful_analysis_response(self) -> None:
        with patch.dict(os.environ, {"AI_MODE": "live"}, clear=False):
            with patch(
                "app.main.generate_live_insights",
                side_effect=ProviderConfigurationError("missing key"),
            ):
                response = TestClient(app).post(
                    "/ai/analyze",
                    json={
                        "borough_id": "E09000007",
                        "include_ai_insights": True,
                        "ai_provider": "deepseek",
                    },
                )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["analysis_mode"], "basic")
        self.assertTrue(payload["ai_insights_requested"])
        self.assertFalse(payload["ai_insights_applied"])
        self.assertEqual(payload["ai_provider"], "deepseek")
        self.assertEqual(payload["ai_error"], "unavailable")
        self.assertIn("executive_summary", payload["insights"])

    def test_qwen_failure_does_not_fall_back_to_another_live_provider(self) -> None:
        with patch.dict(os.environ, {"AI_MODE": "live"}, clear=False):
            with patch(
                "app.main.generate_live_insights",
                side_effect=ProviderConfigurationError("missing qwen key"),
            ) as generate_live:
                response = TestClient(app).post(
                    "/ai/analyze",
                    json={
                        "borough_id": "E09000007",
                        "include_ai_insights": True,
                        "ai_provider": "qwen",
                    },
                )

        self.assertEqual(generate_live.call_args.args[1], "qwen")
        payload = response.json()
        self.assertEqual(payload["analysis_mode"], "basic")
        self.assertFalse(payload["ai_insights_applied"])
        self.assertEqual(payload["ai_provider"], "qwen")
        self.assertEqual(payload["ai_error"], "unavailable")

    def test_explicit_deepseek_request_uses_mock_route_in_mock_mode(self) -> None:
        with patch.dict(
            os.environ,
            {"AI_MODE": "mock", "DEEPSEEK_MODEL": "deepseek-request-model"},
            clear=False,
        ):
            with patch("app.main.generate_live_insights") as generate_live:
                with patch("app.ai.providers.mock_provider.time.sleep"):
                    response = TestClient(app).post(
                        "/ai/analyze",
                        json={
                            "borough_id": "E09000007",
                            "include_ai_insights": True,
                            "ai_provider": "deepseek",
                        },
                    )

        generate_live.assert_not_called()
        self.assertEqual(response.json()["analysis_mode"], "ai")
        self.assertTrue(response.json()["ai_insights_applied"])
        self.assertEqual(response.json()["ai_provider"], "deepseek")
        self.assertEqual(response.json()["ai_model"], "urbaninsight-mock")
        self.assertIsNone(response.json()["ai_error"])

    def test_explicit_qwen_request_uses_qwen_live_route(self) -> None:
        with patch.dict(
            os.environ,
            {"AI_MODE": "live", "QWEN_MODEL": "qwen-request-model"},
            clear=False,
        ):
            with patch(
                "app.main.generate_live_insights",
                return_value=(MOCK_INSIGHTS, "qwen", "qwen-request-model"),
            ) as generate_live:
                response = TestClient(app).post(
                    "/ai/analyze",
                    json={
                        "borough_id": "E09000007",
                        "include_ai_insights": True,
                        "ai_provider": "qwen",
                    },
                )

        generate_live.assert_called_once()
        self.assertEqual(generate_live.call_args.args[1], "qwen")
        self.assertEqual(response.json()["analysis_mode"], "ai")
        self.assertEqual(response.json()["ai_provider"], "qwen")

    def test_missing_request_provider_uses_environment_default(self) -> None:
        with patch.dict(
            os.environ,
            {"AI_MODE": "mock", "AI_PROVIDER": "qwen", "QWEN_MODEL": "qwen-default"},
            clear=False,
        ):
            with patch("app.main.generate_live_insights") as generate_live:
                with patch("app.ai.providers.mock_provider.time.sleep"):
                    response = TestClient(app).post(
                        "/ai/analyze",
                        json={
                            "borough_id": "E09000007",
                            "include_ai_insights": True,
                        },
                    )

        generate_live.assert_not_called()
        self.assertEqual(response.json()["ai_provider"], "qwen")
        self.assertEqual(response.json()["ai_model"], "urbaninsight-mock")

    def test_explicit_provider_text_requests_use_mock_mode(self) -> None:
        with patch.dict(os.environ, {"AI_MODE": "mock"}, clear=False):
            with patch("app.main.generate_live_text") as generate_live_text:
                with patch("app.ai.providers.mock_provider.time.sleep"):
                    chat = TestClient(app).post(
                        "/ai/chat",
                        json={
                            "borough_id": "E09000007",
                            "question": "What stands out?",
                            "previous_context": [],
                            "ai_provider": "deepseek",
                        },
                    )
                    report = TestClient(app).post(
                        "/ai/report",
                        json={
                            "borough_id": "E09000007",
                            "include_ai_insights": True,
                            "previous_context": [],
                            "ai_provider": "qwen",
                        },
                    )

        generate_live_text.assert_not_called()
        self.assertEqual(chat.json()["content"], MOCK_CHAT_RESPONSE)
        self.assertEqual(chat.json()["answer"]["response_type"], "insight")
        self.assertTrue(
            report.json()["content"].startswith(
                "# UrbanInsight AI In-depth Analysis Report"
            )
        )

    def test_unsupported_request_provider_is_rejected(self) -> None:
        response = TestClient(app).post(
            "/ai/analyze",
            json={
                "borough_id": "E09000007",
                "include_ai_insights": True,
                "ai_provider": "unknown",
            },
        )

        self.assertEqual(response.status_code, 422)

    def test_basic_report_is_deterministic_and_has_basic_title(self) -> None:
        with patch("app.main.generate_live_text") as generate_live_text:
            response = TestClient(app).post(
                "/ai/report",
                json={
                    "borough_id": "E09000007",
                    "include_ai_insights": False,
                    "locale": "zh-CN",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response.json()["content"].startswith(
                "# UrbanInsight 基础分析报告"
            )
        )
        generate_live_text.assert_not_called()

    def test_ai_report_uses_completed_provider_route_and_ai_title(self) -> None:
        with patch.dict(os.environ, {"AI_MODE": "live"}, clear=False):
            with patch(
                "app.main.generate_live_text",
                return_value="# Provider title\n\nReport content",
            ) as generate_live_text:
                response = TestClient(app).post(
                    "/ai/report",
                    json={
                        "borough_id": "E09000007",
                        "include_ai_insights": True,
                        "ai_provider": "qwen",
                        "locale": "zh-CN",
                    },
                )

        self.assertEqual(generate_live_text.call_args.args[1], "qwen")
        self.assertTrue(
            response.json()["content"].startswith(
                "# UrbanInsight AI 深度分析报告"
            )
        )

    def test_invalid_locale_is_rejected(self) -> None:
        response = TestClient(app).post(
            "/ai/analyze",
            json={
                "borough_id": "E09000007",
                "previous_context": [],
                "locale": "fr",
            },
        )

        self.assertEqual(response.status_code, 422)

    def test_structured_insights_are_parsed_and_validated(self) -> None:
        provider = DeepSeekProvider(
            api_key="test-key", model="test-model", base_url="https://example.test"
        )
        client = MagicMock()
        client.chat.completions.create.return_value = completion(
            json.dumps(valid_insights_payload())
        )
        provider._client = client

        insights = provider.generate_insights("analyze")

        self.assertEqual(insights.executive_summary, "A concise summary.")
        call = client.chat.completions.create.call_args.kwargs
        self.assertEqual(call["response_format"], {"type": "json_object"})
        self.assertFalse(call["stream"])

    def test_deepseek_chat_is_parsed_and_validated(self) -> None:
        provider = DeepSeekProvider(
            api_key="test-key", model="test-model", base_url="https://example.test"
        )
        client = MagicMock()
        client.chat.completions.create.return_value = completion(json.dumps(valid_chat_payload()))
        provider._client = client

        answer = provider.generate_chat("question")

        self.assertEqual(answer.response_type, "insight")
        self.assertEqual(answer.headline, "A clear finding")
        self.assertEqual(
            client.chat.completions.create.call_args.kwargs["response_format"],
            {"type": "json_object"},
        )

    def test_qwen_comparison_is_parsed_and_validated(self) -> None:
        provider = QwenProvider(
            api_key="test-key", model="test-model", base_url="https://example.test"
        )
        client = MagicMock()
        client.chat.completions.create.return_value = completion(json.dumps(valid_compare_payload()))
        provider._client = client

        answer = provider.generate_comparison("compare")

        self.assertEqual(answer.response_type, "comparison")
        call = client.chat.completions.create.call_args.kwargs
        self.assertEqual(call["response_format"], {"type": "json_object"})
        self.assertEqual(call["extra_body"], {"enable_thinking": False})

    def test_invalid_structured_json_raises_clear_error(self) -> None:
        provider = QwenProvider(
            api_key="test-key", model="test-model", base_url="https://example.test"
        )
        client = MagicMock()
        client.chat.completions.create.return_value = completion("not-json")
        provider._client = client

        with self.assertRaisesRegex(ProviderResponseError, "invalid JSON"):
            provider.generate_insights("analyze")

    def test_qwen_disables_thinking(self) -> None:
        provider = QwenProvider(
            api_key="test-key", model="test-model", base_url="https://example.test"
        )
        client = MagicMock()
        client.chat.completions.create.return_value = completion(
            json.dumps(valid_insights_payload())
        )
        provider._client = client

        provider.generate_insights("analyze")

        call = client.chat.completions.create.call_args.kwargs
        self.assertEqual(call["extra_body"], {"enable_thinking": False})

    def test_normal_text_generation_returns_assistant_content(self) -> None:
        provider = OpenAIProvider(api_key="test-key", model="test-model")
        client = MagicMock()
        client.chat.completions.create.return_value = completion("Grounded answer")
        provider._client = client

        self.assertEqual(provider.generate_text("question"), "Grounded answer")
        call = client.chat.completions.create.call_args.kwargs
        self.assertNotIn("response_format", call)
        self.assertFalse(call["stream"])


if __name__ == "__main__":
    unittest.main()
