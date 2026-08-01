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
