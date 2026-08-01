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
  Leaf,
  Lightbulb,
  MapPinned,
  Sparkles,
  Users
} from "lucide-react";
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
    <Card className="flex min-w-0 items-start justify-between gap-md">
      <div className="min-w-0">
        <p className="text-caption text-text-secondary">{indicator.label}</p>
        <p className="mt-xs text-heading">{indicator.value}</p>
        <p className="mt-sm text-caption text-text-secondary">{indicator.context}</p>
      </div>
      <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full ${statusStyle}`}>
        <Icon size={18} aria-hidden="true" />
      </div>
    </Card>
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
