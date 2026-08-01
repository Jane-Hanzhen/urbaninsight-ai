from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


SupportedLocale = Literal["en", "zh-CN"]
SupportedProvider = Literal["openai", "qwen", "deepseek"]


class InsightItem(BaseModel):
    title: str
    detail: str


class RecommendationItem(InsightItem):
    priority: Literal["High", "Medium"]


class AnalysisInsights(BaseModel):
    executive_summary: str
    ranking_explanation: str
    main_drivers: list[InsightItem] = Field(min_length=2, max_length=4)
    strengths: list[InsightItem] = Field(min_length=2, max_length=4)
    weaknesses: list[InsightItem] = Field(min_length=2, max_length=4)
    indicator_interpretation: str
    recommendations: list[RecommendationItem] = Field(min_length=2, max_length=4)


class ChatKeyPoint(BaseModel):
    title: str
    detail: str
    tone: Literal["positive", "neutral", "attention"] = "neutral"


class ChatAnswer(BaseModel):
    response_type: Literal["insight", "recommendation", "clarification"] = "insight"
    headline: str
    summary: str
    key_points: list[ChatKeyPoint] = Field(default_factory=list, max_length=4)
    bottom_line: str | None = None
    limitations: str | None = None


class ComparisonAdvantage(BaseModel):
    dimension: str
    explanation: str


class BoroughPositioning(BaseModel):
    borough_name: str
    label: str
    description: str


class ComparisonEvidence(BaseModel):
    label: str
    primary_value: str
    comparison_value: str


class CompareAnswer(BaseModel):
    response_type: Literal["comparison"] = "comparison"
    headline: str
    summary: str
    primary_advantages: list[ComparisonAdvantage] = Field(default_factory=list, max_length=3)
    comparison_advantages: list[ComparisonAdvantage] = Field(default_factory=list, max_length=3)
    primary_positioning: BoroughPositioning
    comparison_positioning: BoroughPositioning
    decision_note: str
    evidence: list[ComparisonEvidence] = Field(default_factory=list, max_length=3)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class AnalyzeRequest(BaseModel):
    borough_id: str
    previous_context: list[ChatMessage] = Field(default_factory=list, max_length=12)
    locale: SupportedLocale = "en"
    include_ai_insights: bool = True
    ai_provider: SupportedProvider | None = None


class AnalyzeResponse(BaseModel):
    analysis_mode: Literal["basic", "ai"]
    ai_insights_requested: bool
    ai_insights_applied: bool
    ai_provider: SupportedProvider | None = None
    ai_model: str | None = None
    ai_error: Literal["unavailable"] | None = None
    insights: AnalysisInsights


class ChatRequest(AnalyzeRequest):
    question: str = Field(min_length=1, max_length=1000)
    compare_borough_id: str | None = None


class CompareRequest(AnalyzeRequest):
    compare_borough_id: str


class AnalysisResultSnapshot(BaseModel):
    borough_id: str
    overall_score: float
    regional_rank: int
    economic_score: float
    social_score: float
    ecological_score: float
    contribution_json: dict[str, object] = Field(default_factory=dict)
    updated_at: str | None = None


class ReportRequest(AnalyzeRequest):
    analysis_mode: Literal["basic", "ai"] | None = None
    ai_insights_requested: bool | None = None
    ai_insights_applied: bool | None = None
    ai_model: str | None = None
    ai_error: Literal["unavailable"] | None = None
    insights: AnalysisInsights | None = None
    analysis_result: AnalysisResultSnapshot | None = None


class TextResponse(BaseModel):
    content: str


class ChatResponse(TextResponse):
    answer: ChatAnswer


class CompareResponse(TextResponse):
    answer: CompareAnswer


class PDFReportRequest(BaseModel):
    borough_id: str
    locale: SupportedLocale = "en"
    analysis_mode: Literal["basic", "ai"]
    ai_insights_requested: bool
    ai_insights_applied: bool
    ai_provider: SupportedProvider | None = None
    ai_model: str | None = None
    ai_error: Literal["unavailable"] | None = None
    insights: AnalysisInsights


class ConversationExportMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)
    answer: ChatAnswer | CompareAnswer | None = None


class ConversationPDFRequest(BaseModel):
    borough_id: str
    locale: SupportedLocale = "en"
    messages: list[ConversationExportMessage] = Field(min_length=1, max_length=100)
