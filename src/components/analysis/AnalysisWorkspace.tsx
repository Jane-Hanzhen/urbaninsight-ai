import {
  ArrowUpRight,
  BriefcaseBusiness,
  Building2,
  Check,
  CircleAlert,
  Download,
  FileText,
  GraduationCap,
  HeartPulse,
  House,
  Info,
  Leaf,
  Lightbulb,
  MapPinned,
  Sparkles,
  Users,
  Zap,
  X
} from "lucide-react";
import { useCallback, useEffect, useId, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { useTranslation } from "react-i18next";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AIStatusResponse } from "@/lib/api";
import type {
  AIAnalysisInsights,
  AnalysisInsight,
  AnalysisRecommendation,
  IndicatorDimension,
  KeyIndicator,
  MockAnalysis
} from "@/types/urban";

type AnalysisWorkspaceProps = {
  analysis: MockAnalysis;
  aiInsights: AIAnalysisInsights | null;
  analysisRequestedAI: boolean;
  analysisUsedAI: boolean;
  aiRuntimeStatus: AIStatusResponse | null;
  activeAIProvider: string | null;
  reportFormat: "pdf" | "markdown" | null;
  reportError: string | null;
  onGeneratePDF: () => Promise<void>;
  onGenerateMarkdown: () => Promise<void>;
};

const dimensionIcons = {
  Economic: BriefcaseBusiness,
  Social: Users,
  Ecological: Leaf
};

const indicatorDimensions: IndicatorDimension[] = ["Economic", "Social", "Ecological"];

const indicatorIcons = {
  gdhi_per_head_gbp: Building2,
  business_density_per_1000: BriefcaseBusiness,
  house_price_earnings_ratio_reverse: House,
  police_mean: Users,
  convenient_service_mean: MapPinned,
  cultural_mean: GraduationCap,
  medical_mean: HeartPulse,
  bus_mean: MapPinned,
  ndvi_mean: Leaf,
  wet_mean: Leaf,
  landscape_index: Leaf,
  household_waste_recycling_rate_pct: Leaf
};

export function AnalysisWorkspace({
  analysis,
  aiInsights,
  analysisRequestedAI,
  analysisUsedAI,
  aiRuntimeStatus,
  activeAIProvider,
  reportFormat,
  reportError,
  onGeneratePDF,
  onGenerateMarkdown
}: AnalysisWorkspaceProps) {
  const { t } = useTranslation();
  const dimensionName = (label: string) => t(`analysis.${label.toLowerCase()}`, { defaultValue: label });
  return (
    <section className="animate-panel-in rounded-lg bg-surface p-xl shadow-panel">
      <div className="flex flex-col gap-md lg:flex-row lg:items-end lg:justify-between">
        <div>
          <Badge>{t("analysis.badge")}</Badge>
          <h2 className="mt-md text-title">{t("analysis.title", { borough: analysis.boroughName })}</h2>
          <p className="mt-sm max-w-[70ch] text-body text-text-secondary">
            {t("analysis.intro")}
          </p>
        </div>
        <ReportActions
          reportFormat={reportFormat}
          onGeneratePDF={onGeneratePDF}
          onGenerateMarkdown={onGenerateMarkdown}
        />
      </div>

      <AIRuntimeStatusBanner
        status={aiRuntimeStatus}
        analysisUsedAI={analysisUsedAI}
        activeAIProvider={activeAIProvider}
      />

      <Card className="mt-xl overflow-hidden hover:translate-y-0">
        <div className="grid gap-xl lg:grid-cols-[220px_1fr] lg:items-center">
          <div className="flex items-center gap-lg lg:block">
            <div className="flex h-28 w-28 shrink-0 items-center justify-center rounded-full border-[10px] border-blue-100 bg-white text-title text-primary shadow-card">
              {analysis.overallScore}
            </div>
            <div className="lg:mt-md">
              <p className="text-caption text-text-secondary">{t("analysis.overallScore")}</p>
              <p className="mt-xs text-[18px] font-semibold">{t("analysis.rank", { rank: analysis.rank })}</p>
              <p className="mt-xs flex items-center gap-xs text-caption text-success">
                <ArrowUpRight size={15} aria-hidden="true" /> {t("analysis.rankedAcross")}
              </p>
            </div>
          </div>
          <div>
            <div className="flex items-center gap-sm text-primary">
              <Sparkles size={18} aria-hidden="true" />
              <p className="text-caption font-semibold">{t("analysis.statisticalSummary")}</p>
            </div>
            <p className="mt-md max-w-[70ch] text-body text-text-primary">
              {analysis.boroughName} {analysis.summary}
            </p>
          </div>
        </div>
      </Card>

      <SectionHeading
        eyebrow={t("analysis.performance")}
        title={t("analysis.dimensionsTitle")}
        description={t("analysis.dimensionsDescription")}
      />
      <div className="grid gap-lg md:grid-cols-3">
        {analysis.dimensions.map((dimension) => {
          const Icon = dimensionIcons[dimension.label as keyof typeof dimensionIcons];
          return (
            <Card key={dimension.label}>
              <CardHeader className="flex-row items-center justify-between space-y-0">
                <div className="flex items-center gap-sm">
                  {Icon ? <Icon size={18} className="text-primary" aria-hidden="true" /> : null}
                  <CardTitle>{dimensionName(dimension.label)}</CardTitle>
                </div>
                <span className="text-heading text-primary">{dimension.score}</span>
              </CardHeader>
              <CardContent>
                <div className="h-sm overflow-hidden rounded-full bg-blue-50">
                  <div
                    className="h-full rounded-full bg-primary transition-[width] duration-slow ease-smooth"
                    style={{ width: `${dimension.score}%` }}
                  />
                </div>
                <p className="mt-md text-caption text-text-secondary">
                  {dimension.description}
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="mt-xl grid gap-lg lg:grid-cols-2">
        <ChartCard title={t("analysis.profile")} description={t("analysis.profileDescription")}>
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={analysis.dimensions} outerRadius="68%">
              <PolarGrid stroke="#E5E7EB" />
              <PolarAngleAxis dataKey="label" tickFormatter={dimensionName} tick={{ fill: "#64748B", fontSize: 14 }} />
              <Radar
                dataKey="score"
                stroke="#3B82F6"
                fill="#60A5FA"
                fillOpacity={0.28}
                strokeWidth={2}
                animationDuration={400}
              />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title={t("analysis.contribution")} description={t("analysis.contributionDescription")}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={analysis.contributions} layout="vertical" margin={{ left: 8, right: 24 }}>
              <CartesianGrid stroke="#E5E7EB" horizontal={false} />
              <XAxis type="number" domain={[0, 100]} hide />
              <YAxis
                dataKey="dimension"
                type="category"
                axisLine={false}
                tickLine={false}
                tick={{ fill: "#64748B", fontSize: 14 }}
                width={82}
                tickFormatter={dimensionName}
              />
              <Tooltip />
              <Bar
                dataKey="contribution"
                fill="#34D399"
                radius={[0, 8, 8, 0]}
                barSize={28}
                animationDuration={400}
              />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <SectionHeading
        eyebrow={t("analysis.indicators")}
        title={t("analysis.indicatorTitle")}
        description={t("analysis.indicatorDescription")}
      />
      <div className="space-y-xl" data-testid="indicator-groups">
        {indicatorDimensions.map((dimension) => {
          const Icon = dimensionIcons[dimension];
          const groupedIndicators = analysis.indicators.filter(
            (indicator) => indicator.dimension === dimension
          );
          if (groupedIndicators.length === 0) return null;
          return (
            <section key={dimension} aria-labelledby={`indicator-group-${dimension.toLowerCase()}`}>
              <div className="mb-md flex items-start gap-sm border-b border-border pb-sm">
                <div className="mt-xs flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-blue-50 text-primary">
                  <Icon size={18} aria-hidden="true" />
                </div>
                <div className="min-w-0">
                  <h4
                    id={`indicator-group-${dimension.toLowerCase()}`}
                    className="text-[18px] font-semibold text-text-primary"
                  >
                    {dimensionName(dimension)}
                  </h4>
                  <p className="mt-xs text-caption text-text-secondary">
                    {t(`analysis.${dimension.toLowerCase()}Description`)}
                  </p>
                </div>
              </div>
              <div className="grid gap-md sm:grid-cols-2 xl:grid-cols-3">
                {groupedIndicators.map((indicator) => (
                  <IndicatorCard key={indicator.id} indicator={indicator} />
                ))}
              </div>
            </section>
          );
        })}
      </div>

      <SectionHeading
        eyebrow={t("analysis.interpretation")}
        title={t("analysis.attentionTitle")}
        description={t(
          analysisUsedAI
            ? "analysis.attentionDescription"
            : "analysis.basicInterpretationDescription"
        )}
      />
      {aiInsights ? (
        <Card className="mb-lg hover:translate-y-0">
          <CardHeader><CardTitle>{t("analysis.drivers")}</CardTitle></CardHeader>
          <CardContent>
            <p className="max-w-[70ch] text-body text-text-secondary">{aiInsights.indicator_interpretation}</p>
            <div className="mt-md grid gap-md md:grid-cols-2">
              {aiInsights.main_drivers.map((driver) => (
                <div key={driver.title} className="rounded-md bg-background p-md">
                  <p className="text-caption font-semibold text-text-primary">{driver.title}</p>
                  <p className="mt-xs text-caption text-text-secondary">{driver.detail}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ) : null}
      {aiInsights ? (
        <div className="grid gap-lg lg:grid-cols-3">
          <InsightCard
            title={t("analysis.strengths")}
            icon={<Check size={18} aria-hidden="true" />}
            tone="positive"
            items={analysis.strengths}
          />
          <InsightCard
            title={t("analysis.weaknesses")}
            icon={<CircleAlert size={18} aria-hidden="true" />}
            tone="attention"
            items={analysis.weaknesses}
          />
          <RecommendationCard title={t("analysis.recommendations")} items={analysis.recommendations} />
        </div>
      ) : (
        <Card className="hover:translate-y-0">
          <CardContent className="flex items-start gap-md">
            <CircleAlert className="mt-xs shrink-0 text-warning" size={20} aria-hidden="true" />
            <div>
              <p className="text-caption font-semibold text-text-primary">
                {t(analysisRequestedAI ? "analysis.unavailable" : "analysis.basicAnalysis")}
              </p>
              <p className="mt-xs text-caption text-text-secondary">
                {t(analysisRequestedAI ? "analysis.unavailableDescription" : "analysis.basicAnalysisDescription")}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="mt-xl flex flex-col gap-md border-t border-border pt-xl sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-[18px] font-semibold">{t("analysis.shareTitle")}</p>
          <p className="mt-xs text-caption text-text-secondary">
            {t("analysis.shareDescription")}
          </p>
          {reportError ? <p className="mt-xs text-caption text-danger">{reportError}</p> : null}
        </div>
        <ReportActions
          reportFormat={reportFormat}
          onGeneratePDF={onGeneratePDF}
          onGenerateMarkdown={onGenerateMarkdown}
        />
      </div>
    </section>
  );
}

function AIRuntimeStatusBanner({
  status,
  analysisUsedAI,
  activeAIProvider
}: {
  status: AIStatusResponse | null;
  analysisUsedAI: boolean;
  activeAIProvider: string | null;
}) {
  const { t } = useTranslation();
  if (!status) return null;

  if (status.mode === "mock") {
    return (
      <div
        role="status"
        data-testid="ai-runtime-status"
        className="mt-lg flex items-start gap-sm rounded-md border border-amber-100 bg-amber-50/70 px-md py-sm"
      >
        <Zap className="mt-[2px] shrink-0 text-amber-600" size={16} aria-hidden="true" />
        <div>
          <p className="text-caption font-semibold text-amber-900">
            {t("analysis.runtime.mockTitle")}
          </p>
          <p className="mt-xs text-caption text-amber-900/75">
            {t("analysis.runtime.mockDescription")}
          </p>
          <p className="text-caption text-amber-900/75">
            {t("analysis.runtime.mockSecondary")}
          </p>
        </div>
      </div>
    );
  }

  if (!analysisUsedAI) return null;
  const providerKey = activeAIProvider ?? status.provider;
  const provider = t(`ai.providers.${providerKey}`, {
    defaultValue: providerKey
  });
  return (
    <div
      role="status"
      data-testid="ai-runtime-status"
      className="mt-lg flex items-start gap-sm rounded-md border border-blue-100 bg-blue-50/70 px-md py-sm"
    >
      <Sparkles className="mt-[2px] shrink-0 text-primary" size={16} aria-hidden="true" />
      <div>
        <p className="text-caption font-semibold text-blue-950">
          {t("analysis.runtime.liveTitle")}
        </p>
        <p className="mt-xs text-caption text-blue-900/75">
          {t("analysis.runtime.liveProvider", { provider })}
        </p>
      </div>
    </div>
  );
}

function ReportActions({
  reportFormat,
  onGeneratePDF,
  onGenerateMarkdown
}: {
  reportFormat: "pdf" | "markdown" | null;
  onGeneratePDF: () => Promise<void>;
  onGenerateMarkdown: () => Promise<void>;
}) {
  const { t } = useTranslation();
  const isGenerating = reportFormat !== null;
  return (
    <div className="flex flex-wrap items-center gap-sm">
      <Button
        type="button"
        onClick={() => void onGeneratePDF()}
        disabled={isGenerating}
      >
        <Download size={18} aria-hidden="true" />
        {reportFormat === "pdf"
          ? t("analysis.generatingPDF")
          : t("analysis.downloadPDF")}
      </Button>
      <Button
        type="button"
        variant="ghost"
        onClick={() => void onGenerateMarkdown()}
        disabled={isGenerating}
      >
        <FileText size={17} aria-hidden="true" />
        {reportFormat === "markdown"
          ? t("analysis.generatingMarkdown")
          : t("analysis.exportMarkdown")}
      </Button>
    </div>
  );
}

function SectionHeading({
  eyebrow,
  title,
  description
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <div className="mb-lg mt-xl">
      <p className="text-caption font-semibold text-primary">{eyebrow}</p>
      <h3 className="mt-xs text-heading">{title}</h3>
      <p className="mt-sm max-w-[70ch] text-caption text-text-secondary">{description}</p>
    </div>
  );
}

function ChartCard({
  title,
  description,
  children
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <Card className="hover:translate-y-0">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <p className="text-caption text-text-secondary">{description}</p>
      </CardHeader>
      <CardContent className="h-[300px]">{children}</CardContent>
    </Card>
  );
}

function IndicatorCard({ indicator }: { indicator: KeyIndicator }) {
  const Icon = indicatorIcons[indicator.id as keyof typeof indicatorIcons] ?? MapPinned;
  const statusStyle = {
    positive: "bg-emerald-50 text-success",
    neutral: "bg-blue-50 text-primary",
    attention: "bg-amber-50 text-warning"
  }[indicator.status];

  return (
    <Card
      className="relative flex min-w-0 items-start justify-between gap-md"
      data-indicator-card={indicator.id}
    >
      <div className="min-w-0">
        <div className="flex items-center gap-xs">
          <p className="min-w-0 text-caption text-text-secondary">{indicator.label}</p>
          <IndicatorInfoTooltip indicator={indicator} />
        </div>
        <p className="mt-xs text-heading">{indicator.value}</p>
        <p className="mt-sm text-caption text-text-secondary">{indicator.context}</p>
      </div>
      <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full ${statusStyle}`}>
        <Icon size={18} aria-hidden="true" />
      </div>
    </Card>
  );
}

function IndicatorInfoTooltip({ indicator }: { indicator: KeyIndicator }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [position, setPosition] = useState<{
    top: number;
    left: number;
    width: number;
    placement: "right" | "left" | "contained" | "above" | "below";
  } | null>(null);
  const tooltipId = useId();
  const rootRef = useRef<HTMLDivElement | null>(null);
  const buttonRef = useRef<HTMLButtonElement | null>(null);
  const panelRef = useRef<HTMLDivElement | null>(null);
  const closeTimerRef = useRef<number | null>(null);

  const cancelScheduledClose = useCallback(() => {
    if (closeTimerRef.current !== null) {
      window.clearTimeout(closeTimerRef.current);
      closeTimerRef.current = null;
    }
  }, []);

  const scheduleHoverClose = useCallback(() => {
    cancelScheduledClose();
    closeTimerRef.current = window.setTimeout(() => setOpen(false), 120);
  }, [cancelScheduledClose]);

  const updatePosition = useCallback(() => {
    const trigger = buttonRef.current;
    if (!trigger) return;

    const triggerRect = trigger.getBoundingClientRect();
    const cardRect = trigger.closest("[data-indicator-card]")?.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    const mobile = viewportWidth < 768;
    const edge = mobile ? 16 : 12;
    const gap = 10;
    const width = Math.min(mobile ? 300 : 288, viewportWidth - edge * 2);
    const panelHeight = panelRef.current?.offsetHeight ?? 176;
    const clamp = (value: number, minimum: number, maximum: number) =>
      Math.min(Math.max(value, minimum), Math.max(minimum, maximum));

    if (mobile) {
      const below = triggerRect.bottom + gap;
      const above = triggerRect.top - panelHeight - gap;
      const top = below + panelHeight <= viewportHeight - edge || above < edge
        ? below
        : above;
      setPosition({
        top: clamp(top, edge, viewportHeight - panelHeight - edge),
        left: clamp(
          triggerRect.left + triggerRect.width / 2 - width / 2,
          edge,
          viewportWidth - width - edge
        ),
        width,
        placement: top === below ? "below" : "above"
      });
      return;
    }

    const cardLeft = cardRect?.left ?? edge;
    const cardRight = cardRect?.right ?? viewportWidth - edge;
    const rightCandidate = triggerRect.right + gap;
    const leftCandidate = triggerRect.left - width - gap;
    const activeCard = trigger.closest("[data-indicator-card]");
    const otherCards = Array.from(
      document.querySelectorAll<HTMLElement>("[data-indicator-card]")
    )
      .filter((card) => card !== activeCard)
      .map((card) => card.getBoundingClientRect());
    const overlapsCurrentRow = (left: number) =>
      otherCards.some(
        (rect) =>
          left < rect.right &&
          left + width > rect.left &&
          triggerRect.top < rect.bottom &&
          triggerRect.bottom > rect.top
      );
    const fitsRight =
      rightCandidate + width <= viewportWidth - edge &&
      !overlapsCurrentRow(rightCandidate);
    const fitsLeft = leftCandidate >= edge && !overlapsCurrentRow(leftCandidate);
    const placement = fitsRight ? "right" : fitsLeft ? "left" : "contained";
    const left = placement === "right"
      ? rightCandidate
      : placement === "left"
        ? leftCandidate
        : clamp(cardRight - width - edge, cardLeft + edge, viewportWidth - width - edge);

    const horizontalBlockers = otherCards.filter(
      (rect) => left < rect.right && left + width > rect.left
    );
    const clearTop = horizontalBlockers.reduce(
      (value, rect) => (rect.bottom <= triggerRect.top ? Math.max(value, rect.bottom + gap) : value),
      edge
    );
    const clearBottom = horizontalBlockers.reduce(
      (value, rect) => (rect.top >= triggerRect.bottom ? Math.min(value, rect.top - gap) : value),
      viewportHeight - edge
    );
    const availableTop = clearBottom - panelHeight;
    const alignedTop = availableTop >= clearTop
      ? clamp(triggerRect.top - 10, clearTop, availableTop)
      : clamp(triggerRect.top - 10, edge, viewportHeight - panelHeight - edge);

    setPosition({
      top: alignedTop,
      left,
      width,
      placement
    });
  }, []);

  useEffect(() => {
    if (!open) return;
    const closeOnOutsidePointer = (event: PointerEvent) => {
      const target = event.target as Node;
      if (
        !rootRef.current?.contains(target) &&
        !panelRef.current?.contains(target)
      ) {
        setOpen(false);
      }
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("pointerdown", closeOnOutsidePointer);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("pointerdown", closeOnOutsidePointer);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [open]);

  useLayoutEffect(() => {
    if (!open) {
      setPosition(null);
      return;
    }
    updatePosition();
    const frame = window.requestAnimationFrame(updatePosition);
    window.addEventListener("resize", updatePosition);
    window.addEventListener("scroll", updatePosition, true);
    return () => {
      window.cancelAnimationFrame(frame);
      window.removeEventListener("resize", updatePosition);
      window.removeEventListener("scroll", updatePosition, true);
    };
  }, [open, updatePosition]);

  useEffect(() => () => cancelScheduledClose(), [cancelScheduledClose]);

  return (
    <div
      ref={rootRef}
      className="shrink-0"
      onPointerEnter={(event) => {
        if (event.pointerType !== "touch") {
          cancelScheduledClose();
          setOpen(true);
        }
      }}
      onPointerLeave={(event) => {
        if (event.pointerType !== "touch") scheduleHoverClose();
      }}
      onBlur={(event) => {
        const next = event.relatedTarget as Node | null;
        if (
          next &&
          !event.currentTarget.contains(next) &&
          !panelRef.current?.contains(next)
        ) {
          setOpen(false);
        }
      }}
    >
      <button
        ref={buttonRef}
        type="button"
        className="flex h-7 w-7 items-center justify-center rounded-full text-text-secondary/80 transition-colors duration-fast hover:bg-blue-50 hover:text-primary focus-visible:bg-blue-50 focus-visible:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
        aria-label={t("analysis.indicatorInfo", { indicator: indicator.label })}
        aria-expanded={open}
        aria-controls={tooltipId}
        data-testid={`indicator-info-${indicator.id}`}
        onClick={() => setOpen(true)}
        onFocus={() => setOpen(true)}
      >
        <Info size={15} strokeWidth={1.75} aria-hidden="true" />
      </button>
      {open && position
        ? createPortal(
            <div
              ref={panelRef}
              id={tooltipId}
              role="tooltip"
              data-testid={`indicator-tooltip-${indicator.id}`}
              data-placement={position.placement}
              className="fixed z-50 rounded-md border border-border bg-surface px-sm py-[10px] shadow-card"
              style={{
                top: position.top,
                left: position.left,
                width: position.width
              }}
              onPointerEnter={cancelScheduledClose}
              onPointerLeave={(event) => {
                if (event.pointerType !== "touch") scheduleHoverClose();
              }}
            >
              <button
                type="button"
                className="absolute right-xs top-xs flex h-7 w-7 items-center justify-center rounded-full text-text-secondary transition-colors duration-fast hover:bg-background hover:text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary md:hidden"
                aria-label={t("analysis.closeIndicatorInfo")}
                onClick={() => setOpen(false)}
              >
                <X size={15} aria-hidden="true" />
              </button>
              <p className="pr-xl text-caption font-semibold leading-snug text-text-primary">
                {indicator.tooltip.title}
              </p>
              <div className="mt-xs">
                <p className="text-[11px] font-medium text-text-secondary">
                  {t("analysis.tooltipMeasures")}
                </p>
                <p className="mt-[2px] text-caption leading-snug text-text-secondary">
                  {indicator.tooltip.description}
                </p>
              </div>
              <div className="mt-xs border-t border-border pt-xs">
                <p className="text-[11px] font-medium text-text-secondary">
                  {t("analysis.tooltipInterpretation")}
                </p>
                <p className="mt-[2px] text-caption leading-snug text-text-secondary">
                  {indicator.tooltip.interpretation}
                </p>
              </div>
            </div>,
            document.body
          )
        : null}
    </div>
  );
}

function InsightCard({
  title,
  icon,
  tone,
  items
}: {
  title: string;
  icon: React.ReactNode;
  tone: "positive" | "attention";
  items: AnalysisInsight[];
}) {
  const toneStyle = tone === "positive" ? "bg-emerald-50 text-success" : "bg-red-50 text-danger";

  return (
    <Card className="hover:translate-y-0">
      <CardHeader className="flex-row items-center gap-sm space-y-0">
        <div className={`flex h-9 w-9 items-center justify-center rounded-full ${toneStyle}`}>{icon}</div>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-md">
        {items.map((item) => (
          <div key={item.title}>
            <p className="text-caption font-semibold text-text-primary">{item.title}</p>
            <p className="mt-xs text-caption text-text-secondary">{item.detail}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function RecommendationCard({ title, items }: { title: string; items: AnalysisRecommendation[] }) {
  const { t } = useTranslation();
  return (
    <Card className="hover:translate-y-0">
      <CardHeader className="flex-row items-center gap-sm space-y-0">
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-50 text-primary">
          <Lightbulb size={18} aria-hidden="true" />
        </div>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-md">
        {items.map((item) => (
          <div key={item.title}>
            <div className="flex items-center justify-between gap-sm">
              <p className="text-caption font-semibold text-text-primary">{item.title}</p>
              <Badge className={item.priority === "High" ? "bg-red-50 text-danger" : "bg-blue-50 text-primary"}>
                {t(`analysis.priority.${item.priority.toLowerCase()}`, { defaultValue: item.priority })}
              </Badge>
            </div>
            <p className="mt-xs text-caption text-text-secondary">{item.detail}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
