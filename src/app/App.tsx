import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { TFunction } from "i18next";
import { useTranslation } from "react-i18next";
import { AIPanel } from "@/components/ai-panel/AIPanel";
import { AnalysisWorkspace } from "@/components/analysis/AnalysisWorkspace";
import { AppShell } from "@/components/layout/AppShell";
import { MapStage } from "@/components/map/MapStage";
import { mockAnalysis } from "@/data/mock/urbanInsight";
import {
  askAI,
  compareBoroughs,
  fetchAnalysis,
  fetchAIStatus,
  fetchBoroughs,
  fetchIndicators,
  generateAIAnalysis,
  generateAIReport,
  generatePDFReport,
  type ApiAnalysisResult,
  type ApiBorough,
  type ApiIndicators
} from "@/lib/api";
import type {
  AIAnalysisInsights,
  AIMessage,
  AIProvider,
  AnalysisPhase,
  CompletedAnalysisMetadata
} from "@/types/urban";
import { currentLocale, type SupportedLocale } from "@/i18n";

const AI_INSIGHTS_STORAGE_KEY = "urbaninsight-ai-insights-enabled";
const AI_PROVIDER_STORAGE_KEY = "urbaninsight-ai-provider";

export function App() {
  const { t } = useTranslation();
  const [hoveredBorough, setHoveredBorough] = useState<string | null>(null);
  const [selectedBorough, setSelectedBorough] = useState<string | null>(null);
  const [phase, setPhase] = useState<AnalysisPhase>("idle");
  const [boroughs, setBoroughs] = useState<ApiBorough[]>([]);
  const [indicators, setIndicators] = useState<ApiIndicators | null>(null);
  const [analysisResult, setAnalysisResult] = useState<ApiAnalysisResult | null>(null);
  const [aiInsights, setAIInsights] = useState<AIAnalysisInsights | null>(null);
  const [aiError, setAIError] = useState<string | null>(null);
  const [messages, setMessages] = useState<AIMessage[]>([]);
  const [isReplying, setIsReplying] = useState(false);
  const [reportFormat, setReportFormat] = useState<"pdf" | "markdown" | null>(null);
  const [reportError, setReportError] = useState<string | null>(null);
  const [aiInsightsEnabled, setAIInsightsEnabled] = useState(
    () => window.localStorage.getItem(AI_INSIGHTS_STORAGE_KEY) === "true"
  );
  const [analysisUsedAI, setAnalysisUsedAI] = useState(false);
  const [analysisRequestedAI, setAnalysisRequestedAI] = useState(false);
  const [aiProvider, setAIProvider] = useState<AIProvider>(() => {
    const saved = window.localStorage.getItem(AI_PROVIDER_STORAGE_KEY);
    return saved === "qwen" ? "qwen" : "deepseek";
  });
  const [completedMetadata, setCompletedMetadata] =
    useState<CompletedAnalysisMetadata | null>(null);
  const [progressStep, setProgressStep] = useState(0);
  const [showAISettingNotice, setShowAISettingNotice] = useState(false);
  const workspaceRef = useRef<HTMLDivElement | null>(null);
  const aiRequestControllerRef = useRef<AbortController | null>(null);
  const settingNoticeTimerRef = useRef<number | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetchBoroughs(controller.signal)
      .then((response) => {
        if (import.meta.env.DEV) {
          console.info(`[UrbanInsight] Boroughs loaded: ${response.length}`);
        }
        setBoroughs(response);
      })
      .catch((error: Error) => {
        if (error.name !== "AbortError" && import.meta.env.DEV) {
          console.error("[UrbanInsight] Borough loading failed", error);
        }
        setBoroughs([]);
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (window.localStorage.getItem(AI_PROVIDER_STORAGE_KEY)) return;
    const controller = new AbortController();
    fetchAIStatus(controller.signal)
      .then((status) => {
        if (status.default_provider === "qwen" || status.default_provider === "deepseek") {
          setAIProvider(status.default_provider);
        }
      })
      .catch(() => undefined);
    return () => controller.abort();
  }, []);

  const selectedBoroughRecord = useMemo(
    () => boroughs.find(
      (borough) => normalizeBoroughName(borough.name) === normalizeBoroughName(selectedBorough)
    ) ?? null,
    [boroughs, selectedBorough]
  );

  const runAnalysis = useCallback(async (
    borough: ApiBorough,
    includeAIInsights: boolean,
    requestedProvider: AIProvider
  ) => {
    aiRequestControllerRef.current?.abort();
    const controller = new AbortController();
    aiRequestControllerRef.current = controller;
    const locale = currentLocale();
    const payload = {
      borough_id: borough.id,
      include_ai_insights: includeAIInsights,
      ai_provider: includeAIInsights ? requestedProvider : undefined,
      previous_context: [],
      locale
    };

    if (import.meta.env.DEV) {
      console.info(`[UrbanInsight] Calling POST /ai/analyze ${JSON.stringify(payload)}`);
    }

    setPhase("analyzing");
    setProgressStep(0);
    try {
      const nextIndicators = await fetchIndicators(borough.id, controller.signal);
      setIndicators(nextIndicators);
      setProgressStep(1);

      const nextAnalysis = await fetchAnalysis(borough.id, controller.signal);
      setAnalysisResult(nextAnalysis.result);
      setProgressStep(2);

      const analysisRequest = generateAIAnalysis(
        borough.id,
        includeAIInsights,
        includeAIInsights ? requestedProvider : undefined,
        [],
        locale,
        controller.signal
      );
      setProgressStep(includeAIInsights ? 3 : 2);
      const recommendationTimer = includeAIInsights
        ? window.setTimeout(() => {
            if (!controller.signal.aborted) setProgressStep(4);
          }, 250)
        : null;
      const response = await analysisRequest;
      if (recommendationTimer) window.clearTimeout(recommendationTimer);
      setProgressStep(includeAIInsights ? 5 : 2);

      setAIInsights(response.insights);
      setAnalysisUsedAI(response.ai_insights_applied);
      setCompletedMetadata({
        analysis_mode: response.analysis_mode,
        ai_insights_requested: response.ai_insights_requested,
        ai_insights_applied: response.ai_insights_applied,
        ai_provider: response.ai_provider,
        ai_model: response.ai_model,
        ai_error: response.ai_error
      });
      setAIError(
        response.ai_error === "unavailable"
          ? t("errors.providerUnavailable", {
              provider: providerDisplayName(t, response.ai_provider)
            })
          : null
      );
      await waitForProgressCompletion(includeAIInsights ? 160 : 80);
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") return;
      setAIInsights(null);
      setAnalysisUsedAI(false);
      setCompletedMetadata(null);
      setAIError(t("errors.analysis"));
    } finally {
      if (!controller.signal.aborted) {
        setPhase("completed");
        window.setTimeout(
          () => workspaceRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }),
          180
        );
      }
    }
  }, [t]);

  useEffect(() => () => {
    aiRequestControllerRef.current?.abort();
    if (settingNoticeTimerRef.current) {
      window.clearTimeout(settingNoticeTimerRef.current);
    }
  }, []);

  const handleHoverBorough = useCallback(
    (boroughName: string | null) => {
      setHoveredBorough(boroughName);

      if (!selectedBorough && boroughName) {
        setPhase("hover");
      }

      if (!selectedBorough && !boroughName) {
        setPhase("idle");
      }
    },
    [selectedBorough]
  );

  const handleSelectBorough = useCallback((boroughName: string) => {
    const borough = boroughs.find(
      (candidate) => normalizeBoroughName(candidate.name) === normalizeBoroughName(boroughName)
    );

    if (import.meta.env.DEV) {
      console.info(`[UrbanInsight] Borough selected ${JSON.stringify({
        boroughName,
        boroughId: borough?.id ?? null
      })}`);
    }

    setSelectedBorough(boroughName);
    setPhase("selected");
    setAIInsights(null);
    setAIError(null);
    setMessages([]);
    setReportError(null);
    setIndicators(null);
    setAnalysisResult(null);
    setAnalysisUsedAI(false);
    setAnalysisRequestedAI(aiInsightsEnabled);
    setCompletedMetadata(null);

    if (!borough) {
      setAIError(t("errors.boroughId", { borough: boroughName }));
      if (import.meta.env.DEV) {
        console.warn("[UrbanInsight] AI analysis not started: borough ID unavailable");
      }
      return;
    }

    void runAnalysis(borough, aiInsightsEnabled, aiProvider);
  }, [aiInsightsEnabled, aiProvider, boroughs, runAnalysis, t]);

  const handleAIInsightsEnabledChange = useCallback((enabled: boolean) => {
    setAIInsightsEnabled(enabled);
    window.localStorage.setItem(AI_INSIGHTS_STORAGE_KEY, String(enabled));
    if (phase !== "completed") return;

    setShowAISettingNotice(true);
    if (settingNoticeTimerRef.current) {
      window.clearTimeout(settingNoticeTimerRef.current);
    }
    settingNoticeTimerRef.current = window.setTimeout(
      () => setShowAISettingNotice(false),
      2600
    );
  }, [phase]);

  const handleAIProviderChange = useCallback((provider: AIProvider) => {
    setAIProvider(provider);
    window.localStorage.setItem(AI_PROVIDER_STORAGE_KEY, provider);
    if (phase !== "completed") return;

    setShowAISettingNotice(true);
    if (settingNoticeTimerRef.current) {
      window.clearTimeout(settingNoticeTimerRef.current);
    }
    settingNoticeTimerRef.current = window.setTimeout(
      () => setShowAISettingNotice(false),
      2600
    );
  }, [phase]);

  const handleAsk = useCallback(async (question: string) => {
    if (!selectedBoroughRecord) return;
    const userMessage: AIMessage = { role: "user", content: question };
    const context = [...messages, userMessage];
    setMessages(context);
    setIsReplying(true);
    setAIError(null);
    try {
      const response = await askAI(
        selectedBoroughRecord.id,
        question,
        messages,
        currentLocale(),
        undefined,
        completedAIProvider(completedMetadata)
      );
      setMessages((current) => [...current, { role: "assistant", content: response.content }]);
    } catch (error) {
      setAIError(t("errors.ai"));
    } finally {
      setIsReplying(false);
    }
  }, [completedMetadata, messages, selectedBoroughRecord, t]);

  const handleCompare = useCallback(async (compareBoroughId: string) => {
    if (!selectedBoroughRecord) return;
    const comparison = boroughs.find((borough) => borough.id === compareBoroughId);
    if (!comparison) return;
    const userMessage: AIMessage = {
      role: "user",
      content: t("ai.compareQuestion", { borough: comparison.name })
    };
    setMessages((current) => [...current, userMessage]);
    setIsReplying(true);
    setAIError(null);
    try {
      const response = await compareBoroughs(
        selectedBoroughRecord.id,
        compareBoroughId,
        messages,
        currentLocale(),
        completedAIProvider(completedMetadata)
      );
      setMessages((current) => [...current, { role: "assistant", content: response.content }]);
    } catch (error) {
      setAIError(t("errors.comparison"));
    } finally {
      setIsReplying(false);
    }
  }, [boroughs, completedMetadata, messages, selectedBoroughRecord, t]);

  const handleGenerateMarkdown = useCallback(async () => {
    if (!selectedBoroughRecord || !completedMetadata || !aiInsights || !analysisResult) return;
    setReportFormat("markdown");
    setReportError(null);
    try {
      const locale = currentLocale();
      const response = await generateAIReport(
        selectedBoroughRecord.id,
        completedMetadata,
        aiInsights,
        analysisResult,
        locale
      );
      downloadMarkdown(response.content, selectedBoroughRecord.name, locale);
    } catch (error) {
      setReportError(t("errors.report"));
    } finally {
      setReportFormat(null);
    }
  }, [aiInsights, analysisResult, completedMetadata, selectedBoroughRecord, t]);

  const handleGeneratePDF = useCallback(async () => {
    if (!selectedBoroughRecord || !completedMetadata || !aiInsights) return;
    setReportFormat("pdf");
    setReportError(null);
    try {
      const locale = currentLocale();
      const blob = await generatePDFReport(
        selectedBoroughRecord.id,
        locale,
        completedMetadata,
        aiInsights
      );
      downloadPDF(
        blob,
        selectedBoroughRecord.name,
        locale,
        completedMetadata.ai_insights_applied
      );
    } catch (error) {
      setReportError(t("errors.pdfReport"));
    } finally {
      setReportFormat(null);
    }
  }, [aiInsights, completedMetadata, selectedBoroughRecord, t]);

  const selectedAnalysis = useMemo(() => {
    const boroughName = selectedBorough ?? "Camden";
    const analysis = {
      ...mockAnalysis,
      boroughName,
      summary: t("analysis.fallbackSummary"),
      dimensions: mockAnalysis.dimensions.map((dimension) => ({
        ...dimension,
        description: t(`analysis.${dimension.label.toLowerCase()}Description`)
      })),
      indicators: indicators ? toIndicatorCards(t, indicators) : [],
      strengths: [],
      weaknesses: [],
      recommendations: []
    };
    if (!analysisResult) {
      return analysis;
    }

    const dimensions = [
      {
        label: "Economic",
        score: roundScore(analysisResult.economic_score),
        description: t("analysis.economicDescription")
      },
      {
        label: "Social",
        score: roundScore(analysisResult.social_score),
        description: t("analysis.socialDescription")
      },
      {
        label: "Ecological",
        score: roundScore(analysisResult.ecological_score),
        description: t("analysis.ecologicalDescription")
      }
    ];
    const strongestDimension = dimensions.reduce((strongest, dimension) =>
      dimension.score > strongest.score ? dimension : strongest
    );

    const statisticalAnalysis = {
      ...analysis,
      overallScore: roundScore(analysisResult.overall_score),
      rank: analysisResult.regional_rank,
      summary: t("analysis.summary", { score: roundScore(analysisResult.overall_score), rank: analysisResult.regional_rank, dimension: t(`analysis.${strongestDimension.label.toLowerCase()}`) }),
      dimensions,
      contributions: Object.entries(analysisResult.contribution_json.dimensions).map(
        ([dimension, contribution]) => ({
          dimension,
          contribution: roundScore(contribution)
        })
      )
    };
    if (!aiInsights) return statisticalAnalysis;
    return {
      ...statisticalAnalysis,
      summary: `${aiInsights.executive_summary} ${aiInsights.ranking_explanation}`,
      strengths: aiInsights.strengths,
      weaknesses: aiInsights.weaknesses,
      recommendations: aiInsights.recommendations
    };
  }, [aiInsights, analysisResult, indicators, selectedBorough, t]);

  return (
    <AppShell
      boroughs={boroughs.map((borough) => borough.name)}
      selectedBorough={selectedBorough}
      onSelectBorough={handleSelectBorough}
      aiInsightsEnabled={aiInsightsEnabled}
      aiProvider={aiProvider}
      showAISettingNotice={showAISettingNotice}
      onAIInsightsEnabledChange={handleAIInsightsEnabledChange}
      onAIProviderChange={handleAIProviderChange}
      map={
        <MapStage
          hoveredBorough={hoveredBorough}
          selectedBorough={selectedBorough}
          onHoverBorough={handleHoverBorough}
          onSelectBorough={handleSelectBorough}
        />
      }
      aiPanel={
        <AIPanel
          phase={phase}
          hoveredBorough={hoveredBorough}
          selectedBorough={selectedBorough}
          selectedBoroughId={selectedBoroughRecord?.id ?? null}
          analysis={selectedAnalysis}
          boroughs={boroughs}
          messages={messages}
          aiError={aiError}
          includeAIInsights={analysisRequestedAI}
          analysisUsedAI={analysisUsedAI}
          progressStep={progressStep}
          isReplying={isReplying}
          onAsk={handleAsk}
          onCompare={handleCompare}
        />
      }
      analysis={
        phase === "completed" ? (
          <div ref={workspaceRef}>
            <AnalysisWorkspace
              analysis={selectedAnalysis}
              aiInsights={aiInsights}
              analysisRequestedAI={analysisRequestedAI}
              analysisUsedAI={analysisUsedAI}
              reportFormat={reportFormat}
              reportError={reportError}
              onGeneratePDF={handleGeneratePDF}
              onGenerateMarkdown={handleGenerateMarkdown}
            />
          </div>
        ) : null
      }
    />
  );
}

function toIndicatorCards(t: TFunction, indicators: ApiIndicators) {
  return [
    {
      id: "gdhi_per_head_gbp",
      dimension: "Economic" as const,
      label: t("indicators.gdhi_per_head_gbp", { defaultValue: "GDHI per head" }),
      value: formatCurrency(indicators.gdhi_per_head_gbp),
      context: t("indicatorContext.gdhi"),
      status: "neutral" as const
    },
    {
      id: "business_density_per_1000",
      dimension: "Economic" as const,
      label: t("indicators.business_density_per_1000", { defaultValue: "Business density" }),
      value: `${formatNumber(indicators.business_density_per_1000, 1)} / 1,000`,
      context: t("indicatorContext.business"),
      status: "neutral" as const
    },
    {
      id: "house_price_earnings_ratio_reverse",
      dimension: "Economic" as const,
      label: t("indicators.house_price_earnings_ratio_reverse", { defaultValue: "Housing affordability" }),
      value: formatNumber(indicators.house_price_earnings_ratio_reverse, 2, 2),
      context: t("indicatorContext.reversed"),
      status: "neutral" as const
    },
    {
      id: "police_mean",
      dimension: "Social" as const,
      label: t("indicators.police_mean", { defaultValue: "Police provision" }),
      value: formatNumber(indicators.police_mean, 1, 1),
      context: t("indicatorContext.police"),
      status: "neutral" as const
    },
    {
      id: "bus_mean",
      dimension: "Social" as const,
      label: t("indicators.bus_mean", { defaultValue: "Bus accessibility" }),
      value: formatNumber(indicators.bus_mean, 1, 1),
      context: t("indicatorContext.bus"),
      status: "neutral" as const
    },
    {
      id: "medical_mean",
      dimension: "Social" as const,
      label: t("indicators.medical_mean", { defaultValue: "Medical resources" }),
      value: formatNumber(indicators.medical_mean, 1, 1),
      context: t("indicatorContext.medical"),
      status: "neutral" as const
    },
    {
      id: "cultural_mean",
      dimension: "Social" as const,
      label: t("indicators.cultural_mean", { defaultValue: "Cultural amenities" }),
      value: formatNumber(indicators.cultural_mean, 1, 1),
      context: t("indicatorContext.cultural"),
      status: "neutral" as const
    },
    {
      id: "convenient_service_mean",
      dimension: "Social" as const,
      label: t("indicators.convenient_service_mean", { defaultValue: "Convenient services" }),
      value: formatNumber(indicators.convenient_service_mean, 1, 1),
      context: t("indicatorContext.convenient"),
      status: "neutral" as const
    },
    {
      id: "ndvi_mean",
      dimension: "Ecological" as const,
      label: t("indicators.ndvi_mean", { defaultValue: "NDVI" }),
      value: formatNumber(indicators.ndvi_mean, 3, 3),
      context: t("indicatorContext.ndvi"),
      status: "neutral" as const
    },
    {
      id: "wet_mean",
      dimension: "Ecological" as const,
      label: t("indicators.wet_mean", { defaultValue: "Wetness index" }),
      value: formatNumber(indicators.wet_mean, 3, 3),
      context: t("indicatorContext.wet"),
      status: "neutral" as const
    },
    {
      id: "landscape_index",
      dimension: "Ecological" as const,
      label: t("indicators.landscape_index", { defaultValue: "Landscape index" }),
      value: formatNumber(indicators.landscape_index, 3, 3),
      context: t("indicatorContext.landscape"),
      status: "neutral" as const
    },
    {
      id: "household_waste_recycling_rate_pct",
      dimension: "Ecological" as const,
      label: t("indicators.household_waste_recycling_rate_pct", { defaultValue: "Waste recycling" }),
      value: `${formatNumber(indicators.household_waste_recycling_rate_pct, 1, 1)}%`,
      context: t("indicatorContext.recycling"),
      status: "neutral" as const
    }
  ];
}

function formatNumber(
  value: number,
  maximumFractionDigits: number,
  minimumFractionDigits = 0
) {
  return new Intl.NumberFormat("en-GB", {
    maximumFractionDigits,
    minimumFractionDigits
  }).format(value);
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
    maximumFractionDigits: 0
  }).format(value);
}

function roundScore(value: number) {
  return Math.round(value * 10) / 10;
}

function normalizeBoroughName(value: string | null) {
  return value?.trim().toLocaleLowerCase("en-GB") ?? "";
}

function waitForProgressCompletion(delay: number) {
  return new Promise<void>((resolve) => window.setTimeout(resolve, delay));
}

function completedAIProvider(
  metadata: CompletedAnalysisMetadata | null
): AIProvider | undefined {
  return metadata?.ai_insights_applied &&
    (metadata.ai_provider === "deepseek" || metadata.ai_provider === "qwen")
    ? metadata.ai_provider
    : undefined;
}

function providerDisplayName(
  t: TFunction,
  provider: CompletedAnalysisMetadata["ai_provider"]
) {
  if (provider === "qwen") return t("ai.providers.qwen");
  if (provider === "deepseek") return t("ai.providers.deepseek");
  return t("ai.insightsControl");
}

function downloadMarkdown(content: string, boroughName: string, locale: SupportedLocale) {
  const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  const slug = boroughName.toLowerCase().replace(/\s+/g, "-");
  anchor.download = locale === "zh-CN"
    ? `urbaninsight-${slug}-分析报告.md`
    : `urbaninsight-${slug}-report.md`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

function downloadPDF(
  blob: Blob,
  boroughName: string,
  locale: SupportedLocale,
  aiInsightsApplied: boolean
) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  const date = new Date().toISOString().slice(0, 10);
  const borough = safeFilenamePart(boroughName);
  const reportType = locale === "zh-CN"
    ? aiInsightsApplied ? "AI深度分析报告" : "基础分析报告"
    : aiInsightsApplied ? "AI_In-depth_Analysis_Report" : "Basic_Analysis_Report";
  anchor.href = url;
  anchor.download = `UrbanInsight_${borough}_${reportType}_${date}.pdf`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

function safeFilenamePart(value: string) {
  return value
    .trim()
    .replace(/[<>:"/\\|?*\u0000-\u001F]/g, "_")
    .replace(/\s+/g, "_")
    .replace(/_+/g, "_");
}
