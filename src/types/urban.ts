export type BoroughSummary = {
  id: string;
  name: string;
  status: "ready" | "coming-soon";
};

export type AnalysisPhase =
  | "idle"
  | "hover"
  | "selected"
  | "analyzing"
  | "completed";

export type DimensionScore = {
  label: string;
  score: number;
  description: string;
};

export type DimensionContribution = {
  dimension: string;
  contribution: number;
};

export type IndicatorDimension = "Economic" | "Social" | "Ecological";

export type IndicatorTooltipContent = {
  title: string;
  description: string;
  interpretation: string;
};

export type KeyIndicator = {
  id: string;
  dimension: IndicatorDimension;
  label: string;
  value: string;
  context: string;
  tooltip: IndicatorTooltipContent;
  status: "positive" | "neutral" | "attention";
};

export type AnalysisInsight = {
  title: string;
  detail: string;
};

export type AnalysisRecommendation = AnalysisInsight & {
  priority: "High" | "Medium";
};

export type AIAnalysisInsights = {
  executive_summary: string;
  ranking_explanation: string;
  main_drivers: AnalysisInsight[];
  strengths: AnalysisInsight[];
  weaknesses: AnalysisInsight[];
  indicator_interpretation: string;
  recommendations: AnalysisRecommendation[];
};

export type AIAnalysisResponse = {
  analysis_mode: "basic" | "ai";
  ai_insights_requested: boolean;
  ai_insights_applied: boolean;
  ai_provider: AIProvider | "openai" | null;
  ai_model: string | null;
  ai_error: "unavailable" | null;
  insights: AIAnalysisInsights;
};

export type AIProvider = "deepseek" | "qwen";

export type AIChatKeyPoint = { title: string; detail: string; tone: "positive" | "neutral" | "attention" };
export type AIChatAnswer = {
  response_type: "insight" | "recommendation" | "clarification";
  headline: string;
  summary: string;
  key_points: AIChatKeyPoint[];
  bottom_line: string | null;
  limitations: string | null;
};
export type AIComparisonAdvantage = { dimension: string; explanation: string };
export type AIBoroughPositioning = { borough_name: string; label: string; description: string };
export type AIComparisonEvidence = { label: string; primary_value: string; comparison_value: string };
export type AICompareAnswer = {
  response_type: "comparison";
  headline: string;
  summary: string;
  primary_advantages: AIComparisonAdvantage[];
  comparison_advantages: AIComparisonAdvantage[];
  primary_positioning: AIBoroughPositioning;
  comparison_positioning: AIBoroughPositioning;
  decision_note: string;
  evidence: AIComparisonEvidence[];
};
export type AIStructuredAnswer = AIChatAnswer | AICompareAnswer;

export type CompletedAnalysisMetadata = Pick<
  AIAnalysisResponse,
  | "analysis_mode"
  | "ai_insights_requested"
  | "ai_insights_applied"
  | "ai_provider"
  | "ai_model"
  | "ai_error"
>;

export type AIMessage = {
  role: "user" | "assistant";
  content: string;
  answer?: AIStructuredAnswer;
};

export type MockAnalysis = {
  boroughName: string;
  overallScore: number;
  rank: number;
  summary: string;
  dimensions: DimensionScore[];
  contributions: DimensionContribution[];
  indicators: KeyIndicator[];
  strengths: AnalysisInsight[];
  weaknesses: AnalysisInsight[];
  recommendations: AnalysisRecommendation[];
};
