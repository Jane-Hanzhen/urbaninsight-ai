import { FormEvent, useState } from "react";
import type { TFunction } from "i18next";
import { Bot, CheckCircle2, CircleDot, CircleDotDashed, MapPin, Send, Sparkles } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import type { AIMessage, AnalysisPhase, MockAnalysis } from "@/types/urban";

type AIPanelProps = {
  phase: AnalysisPhase;
  hoveredBorough: string | null;
  selectedBorough: string | null;
  selectedBoroughId: string | null;
  analysis: MockAnalysis;
  boroughs: { id: string; name: string }[];
  messages: AIMessage[];
  aiError: string | null;
  includeAIInsights: boolean;
  analysisUsedAI: boolean;
  progressStep: number;
  isReplying: boolean;
  onAsk: (question: string) => Promise<void>;
  onCompare: (boroughId: string) => Promise<void>;
};

export function AIPanel({ phase, hoveredBorough, selectedBorough, selectedBoroughId, analysis, boroughs, messages, aiError, includeAIInsights, analysisUsedAI, progressStep, isReplying, onAsk, onCompare }: AIPanelProps) {
  const { t } = useTranslation();
  const activeBorough = selectedBorough ?? hoveredBorough;
  return (
    <aside className="sticky top-[96px] h-fit rounded-lg bg-white/88 p-lg shadow-panel backdrop-blur">
      <div className="flex items-center gap-md">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-blue-50 text-primary"><Bot size={22} aria-hidden="true" /></div>
        <div className="min-w-0"><h2 className="text-[18px] font-semibold text-text-primary">UrbanInsight AI</h2><p className="mt-xs text-caption text-text-secondary">{t("ai.platform")}</p></div>
      </div>
      <Card className="mt-lg shadow-card hover:translate-y-0" aria-live="polite">
        <CardHeader><CardTitle>{getPanelTitle(t, phase, activeBorough)}</CardTitle></CardHeader>
        <CardContent>{renderPanelContent(t, phase, activeBorough, analysis, aiError, analysisUsedAI)}</CardContent>
      </Card>
      {phase === "selected" || phase === "analyzing" ? <Progress includeAIInsights={includeAIInsights} progressStep={progressStep} /> : null}
      {phase === "completed" && selectedBoroughId && analysisUsedAI ? <Conversation boroughs={boroughs.filter((borough) => borough.id !== selectedBoroughId)} messages={messages} isReplying={isReplying} onAsk={onAsk} onCompare={onCompare} /> : null}
    </aside>
  );
}

function Progress({ includeAIInsights, progressStep }: { includeAIInsights: boolean; progressStep: number }) {
  const { t } = useTranslation();
  const steps = t("ai.progress", { returnObjects: true }) as string[];
  const completedSteps = t("ai.progressComplete", { returnObjects: true }) as string[];
  const visibleSteps = includeAIInsights ? steps : steps.slice(0, 2);
  return <div className="mt-lg space-y-sm" aria-label={t("ai.progressLabel")}>{visibleSteps.map((step, index) => <div key={step} className="flex items-center gap-sm rounded-md bg-background px-md py-sm text-caption text-text-secondary">{index < progressStep ? <CheckCircle2 className="shrink-0 text-success" size={16} aria-hidden="true" /> : index === progressStep ? <CircleDotDashed className="shrink-0 animate-pulse text-primary" size={16} aria-hidden="true" /> : <CircleDot className="shrink-0 text-border" size={16} aria-hidden="true" />}<span>{index < progressStep ? completedSteps[index] : step}</span></div>)}</div>;
}

function Conversation({ boroughs, messages, isReplying, onAsk, onCompare }: { boroughs: { id: string; name: string }[]; messages: AIMessage[]; isReplying: boolean; onAsk: (question: string) => Promise<void>; onCompare: (boroughId: string) => Promise<void> }) {
  const { t } = useTranslation();
  const [question, setQuestion] = useState("");
  const [comparisonId, setComparisonId] = useState("");
  const handleSubmit = (event: FormEvent) => { event.preventDefault(); const trimmed = question.trim(); if (!trimmed || isReplying) return; setQuestion(""); void onAsk(trimmed); };
  return <div className="mt-lg border-t border-border pt-lg">
    {messages.length ? <div className="mb-md max-h-64 space-y-sm overflow-y-auto" aria-live="polite">{messages.map((message, index) => <div key={`${message.role}-${index}`} className={`break-words rounded-md px-md py-sm text-caption ${message.role === "user" ? "ml-lg bg-blue-50 text-text-primary" : "mr-lg bg-background text-text-secondary"}`}>{message.content}</div>)}</div> : null}
    <form onSubmit={handleSubmit} className="flex min-w-0 gap-sm"><Input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder={t("ai.askPlaceholder")} aria-label={t("ai.askLabel")} /><Button type="submit" size="icon" className="shrink-0" disabled={!question.trim() || isReplying} title={t("ai.send")}><Send size={17} aria-hidden="true" /></Button></form>
    <div className="mt-sm flex min-w-0 flex-wrap gap-sm"><select value={comparisonId} onChange={(event) => setComparisonId(event.target.value)} className="h-11 min-w-[160px] flex-1 rounded-md border border-border bg-white px-md text-caption text-text-primary outline-none transition focus:border-primary focus:ring-2 focus:ring-blue-100" aria-label={t("ai.compareLabel")}><option value="">{t("ai.comparePlaceholder")}</option>{boroughs.map((borough) => <option key={borough.id} value={borough.id}>{borough.name}</option>)}</select><Button type="button" variant="secondary" disabled={!comparisonId || isReplying} onClick={() => void onCompare(comparisonId)}>{t("ai.compare")}</Button></div>
  </div>;
}

function getPanelTitle(t: TFunction, phase: AnalysisPhase, boroughName: string | null) {
  const borough = boroughName ?? t("map.london");
  if (phase === "hover") return t("ai.looking", { borough });
  if (phase === "selected") return t("ai.selectedTitle", { borough });
  if (phase === "analyzing") return t("ai.analyzingTitle", { borough });
  if (phase === "completed") return t("ai.complete");
  return t("ai.idleTitle");
}

function renderPanelContent(t: TFunction, phase: AnalysisPhase, boroughName: string | null, analysis: MockAnalysis, aiError: string | null, analysisUsedAI: boolean) {
  const borough = boroughName ?? t("map.london");
  if (phase === "hover") return <p className="text-body text-text-secondary">{t("ai.clickAnalyze", { borough })}</p>;
  if (phase === "selected" || phase === "analyzing") { const Icon = phase === "selected" ? MapPin : Sparkles; return <div className="flex items-start gap-sm text-body text-text-secondary"><Icon className={`mt-xs shrink-0 text-primary ${phase === "analyzing" ? "animate-pulse" : ""}`} size={18} aria-hidden="true" /><p>{t(phase === "selected" ? "ai.selectedBody" : "ai.analyzingBody", { borough })}</p></div>; }
  if (phase === "completed") return <div><div className="flex items-center gap-sm text-success"><CheckCircle2 size={18} aria-hidden="true" /><p className="font-semibold">{boroughName ?? analysis.boroughName}</p></div><div className="mt-md grid grid-cols-2 gap-md"><PanelMetric label={t("ai.overallScore")} value={analysis.overallScore.toString()} /><PanelMetric label={t("ai.regionalRank")} value={`#${analysis.rank}`} /></div>{aiError ? <p className="mt-md break-words text-caption text-warning">{aiError}</p> : <p className="mt-md text-caption text-text-secondary">{t(analysisUsedAI ? "ai.followUpHint" : "ai.basicCompleteHint")}</p>}</div>;
  return <div className="space-y-md"><p className="max-w-[70ch] text-body text-text-secondary">{t("ai.assistant")}<br />{t("ai.capabilities")}</p><div><p className="text-body font-semibold text-text-primary">{t("ai.explore")}</p><p className="max-w-[70ch] text-body text-text-secondary">{t("ai.begin")}</p></div></div>;
}

function PanelMetric({ label, value }: { label: string; value: string }) { return <div className="min-w-0 rounded-md bg-background p-md"><p className="text-caption text-text-secondary">{label}</p><p className="mt-xs text-heading text-text-primary">{value}</p></div>; }
