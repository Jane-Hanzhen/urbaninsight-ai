import type {
  AIAnalysisInsights,
  AIAnalysisResponse,
  AIMessage,
  AIProvider,
  CompletedAnalysisMetadata
} from "@/types/urban";
import type { SupportedLocale } from "@/i18n";

export type ApiBorough = {
  id: string;
  name: string;
  region: string;
  geometry_reference: string | null;
  created_at: string;
};

export type ApiIndicators = {
  borough_id: string;
  gdhi_per_head_gbp: number;
  business_density_per_1000: number;
  house_price_earnings_ratio_reverse: number;
  police_mean: number;
  convenient_service_mean: number;
  cultural_mean: number;
  medical_mean: number;
  bus_mean: number;
  ndvi_mean: number;
  wet_mean: number;
  landscape_index: number;
  household_waste_recycling_rate_pct: number;
  updated_at: string;
};

export type ApiAnalysisResult = {
  borough_id: string;
  overall_score: number;
  regional_rank: number;
  economic_score: number;
  social_score: number;
  ecological_score: number;
  contribution_json: {
    dimensions: Record<"Economic" | "Social" | "Ecological", number>;
    indicators: Record<string, number>;
    weights: Record<string, number>;
    pca: {
      components: number;
      explained_variance_ratio: number[];
      cumulative_explained_variance: number;
    };
  };
  updated_at: string;
};

export type ApiAnalysisResponse = {
  borough_id: string;
  result: ApiAnalysisResult | null;
};

export type AIStatusResponse = {
  configured: boolean;
  enabled: boolean;
  mode: "mock" | "live";
  provider: string;
  model: string;
  default_provider: string;
  available_providers: string[];
};

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, { signal });
  if (!response.ok) {
    throw await toApiError(response);
  }
  return response.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal
  });
  if (!response.ok) {
    throw await toApiError(response);
  }
  return response.json() as Promise<T>;
}

async function postBlob(path: string, body: unknown): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!response.ok) {
    throw await toApiError(response);
  }
  return response.blob();
}

async function toApiError(response: Response) {
  const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
  return new Error(payload?.detail ?? `API request failed with status ${response.status}`);
}

export function fetchBoroughs(signal?: AbortSignal) {
  return request<ApiBorough[]>("/boroughs", signal);
}

export function fetchIndicators(boroughId: string, signal?: AbortSignal) {
  return request<ApiIndicators>(`/indicators/${encodeURIComponent(boroughId)}`, signal);
}

export function fetchAnalysis(boroughId: string, signal?: AbortSignal) {
  return request<ApiAnalysisResponse>(`/analysis/${encodeURIComponent(boroughId)}`, signal);
}

export function fetchAIStatus(signal?: AbortSignal) {
  return request<AIStatusResponse>("/ai/status", signal);
}

export function generateAIAnalysis(
  boroughId: string,
  includeAIInsights: boolean,
  aiProvider: AIProvider | undefined,
  previousContext: AIMessage[] = [],
  locale: SupportedLocale = "en",
  signal?: AbortSignal
) {
  return post<AIAnalysisResponse>(
    "/ai/analyze",
    {
      borough_id: boroughId,
      include_ai_insights: includeAIInsights,
      ai_provider: includeAIInsights ? aiProvider : undefined,
      previous_context: previousContext,
      locale
    },
    signal
  );
}

export function askAI(
  boroughId: string,
  question: string,
  previousContext: AIMessage[],
  locale: SupportedLocale = "en",
  compareBoroughId?: string,
  aiProvider?: AIProvider
) {
  return post<{ content: string }>("/ai/chat", {
    borough_id: boroughId,
    question,
    previous_context: previousContext,
    locale,
    ai_provider: aiProvider,
    compare_borough_id: compareBoroughId
  });
}

export function compareBoroughs(
  boroughId: string,
  compareBoroughId: string,
  previousContext: AIMessage[],
  locale: SupportedLocale = "en",
  aiProvider?: AIProvider
) {
  return post<{ content: string }>("/ai/compare", {
    borough_id: boroughId,
    compare_borough_id: compareBoroughId,
    previous_context: previousContext,
    locale,
    ai_provider: aiProvider
  });
}

export function generateAIReport(
  boroughId: string,
  metadata: CompletedAnalysisMetadata,
  insights: AIAnalysisInsights,
  analysisResult: ApiAnalysisResult,
  locale: SupportedLocale = "en"
) {
  return post<{ content: string }>("/ai/report", {
    borough_id: boroughId,
    include_ai_insights: metadata.ai_insights_applied,
    previous_context: [],
    locale,
    ...metadata,
    insights,
    analysis_result: analysisResult
  });
}

export function generatePDFReport(
  boroughId: string,
  locale: SupportedLocale,
  metadata: CompletedAnalysisMetadata,
  insights: AIAnalysisInsights
) {
  return postBlob("/reports/pdf", {
    borough_id: boroughId,
    locale,
    ...metadata,
    insights
  });
}
