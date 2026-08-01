import { FormEvent, useState } from "react";
import type { TFunction } from "i18next";
import { Bot, CheckCircle2, CircleAlert, CircleDot, CircleDotDashed, FileDown, Lightbulb, MapPin, Send, Sparkles } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import type { AIChatAnswer, AICompareAnswer, AIMessage, AnalysisPhase, MockAnalysis } from "@/types/urban";

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
  hasFailedRequest: boolean;
  isConversationExporting: boolean;
  conversationExportError: string | null;
  onAsk: (question: string) => Promise<void>;
  onCompare: (boroughId: string) => Promise<void>;
  onRetry: () => Promise<void>;
  onExportConversation: () => Promise<void>;
};

export function AIPanel({ phase, hoveredBorough, selectedBorough, selectedBoroughId, analysis, boroughs, messages, aiError, includeAIInsights, analysisUsedAI, progressStep, isReplying, hasFailedRequest, isConversationExporting, conversationExportError, onAsk, onCompare, onRetry, onExportConversation }: AIPanelProps) {
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
      {phase === "completed" && selectedBoroughId && analysisUsedAI ? <Conversation boroughs={boroughs.filter((borough) => borough.id !== selectedBoroughId)} messages={messages} isReplying={isReplying} hasFailedRequest={hasFailedRequest} isConversationExporting={isConversationExporting} conversationExportError={conversationExportError} onAsk={onAsk} onCompare={onCompare} onRetry={onRetry} onExportConversation={onExportConversation} /> : null}
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

function Conversation({ boroughs, messages, isReplying, hasFailedRequest, isConversationExporting, conversationExportError, onAsk, onCompare, onRetry, onExportConversation }: { boroughs: { id: string; name: string }[]; messages: AIMessage[]; isReplying: boolean; hasFailedRequest: boolean; isConversationExporting: boolean; conversationExportError: string | null; onAsk: (question: string) => Promise<void>; onCompare: (boroughId: string) => Promise<void>; onRetry: () => Promise<void>; onExportConversation: () => Promise<void> }) {
  const { t } = useTranslation();
  const [question, setQuestion] = useState("");
  const [comparisonId, setComparisonId] = useState("");
  const handleSubmit = (event: FormEvent) => { event.preventDefault(); const trimmed = question.trim(); if (!trimmed || isReplying) return; setQuestion(""); void onAsk(trimmed); };
  return <div className="mt-lg border-t border-border pt-lg">
    {messages.length || isReplying || hasFailedRequest ? <div className="mb-md max-h-[32rem] space-y-sm overflow-y-auto" aria-live="polite">{messages.map((message, index) => <ConversationMessage key={`${message.role}-${index}`} message={message} />)}{isReplying ? <AIThinkingMessage /> : null}{hasFailedRequest && !isReplying ? <AIErrorMessage onRetry={onRetry} /> : null}</div> : null}
    <form onSubmit={handleSubmit} className="flex min-w-0 gap-sm"><Input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder={t("ai.askPlaceholder")} aria-label={t("ai.askLabel")} /><Button type="submit" size="icon" className="shrink-0" disabled={!question.trim() || isReplying} title={t("ai.send")}><Send size={17} aria-hidden="true" /></Button></form>
    <div className="mt-sm flex min-w-0 flex-wrap gap-sm"><select value={comparisonId} onChange={(event) => setComparisonId(event.target.value)} className="h-11 min-w-[160px] flex-1 rounded-md border border-border bg-white px-md text-caption text-text-primary outline-none transition focus:border-primary focus:ring-2 focus:ring-blue-100" aria-label={t("ai.compareLabel")}><option value="">{t("ai.comparePlaceholder")}</option>{boroughs.map((borough) => <option key={borough.id} value={borough.id}>{borough.name}</option>)}</select><Button type="button" variant="secondary" disabled={!comparisonId || isReplying} onClick={() => void onCompare(comparisonId)}>{t("ai.compare")}</Button></div>
    {messages.length ? <div className="mt-md border-t border-border pt-md"><Button type="button" variant="ghost" size="sm" disabled={isReplying || isConversationExporting} onClick={() => void onExportConversation()}><FileDown size={16} aria-hidden="true" />{isConversationExporting ? t("ai.exportingConversation") : t("ai.exportConversation")}</Button>{conversationExportError ? <p className="mt-xs text-caption text-warning">{conversationExportError}</p> : null}</div> : null}
  </div>;
}

function AIErrorMessage({ onRetry }: { onRetry: () => Promise<void> }) {
  const { t } = useTranslation();
  return <div className="mr-lg rounded-lg border border-amber-200 bg-amber-50/70 px-md py-md text-caption" role="alert"><div className="flex items-start gap-sm"><CircleAlert className="mt-[2px] shrink-0 text-warning" size={16} aria-hidden="true" /><div><p className="font-semibold text-text-primary">{t("ai.requestErrorTitle")}</p><p className="mt-xs text-text-secondary">{t("ai.requestErrorBody")}</p></div></div><Button type="button" variant="secondary" size="sm" className="mt-md" onClick={() => void onRetry()}>{t("ai.retryAnalysis")}</Button></div>;
}

function AIThinkingMessage() {
  const { t } = useTranslation();
  return <div className="mr-lg flex items-center gap-sm rounded-lg border border-blue-100 bg-blue-50/60 px-md py-sm text-caption text-text-secondary" role="status"><Sparkles className="shrink-0 animate-pulse text-primary" size={15} aria-hidden="true" /><span>{t("ai.analyzingResponse")}</span><span className="flex gap-[3px]" aria-hidden="true"><span className="h-1 w-1 animate-pulse rounded-full bg-primary" /><span className="h-1 w-1 animate-pulse rounded-full bg-primary [animation-delay:150ms]" /><span className="h-1 w-1 animate-pulse rounded-full bg-primary [animation-delay:300ms]" /></span></div>;
}

function ConversationMessage({ message }: { message: AIMessage }) {
  if (message.role === "user") return <div className="ml-lg break-words rounded-md bg-blue-50 px-md py-sm text-caption text-text-primary">{message.content}</div>;
  if (message.answer?.response_type === "comparison") return <CompareResponseCard answer={message.answer} />;
  if (message.answer) return <ChatResponseCard answer={message.answer} />;
  return <div className="mr-lg whitespace-pre-wrap break-words rounded-md bg-background px-md py-sm text-caption text-text-secondary">{message.content}</div>;
}

function ChatResponseCard({ answer }: { answer: AIChatAnswer }) {
  return <article className="mr-lg overflow-hidden rounded-lg border border-blue-100 bg-white shadow-card"><div className="border-b border-blue-100 bg-blue-50/60 px-md py-sm"><p className="text-caption font-semibold text-text-primary">{answer.headline}</p></div><div className="space-y-md px-md py-md text-caption text-text-secondary"><p>{answer.summary}</p>{answer.key_points.length ? <div className="space-y-sm">{answer.key_points.map((point) => { const Icon = point.tone === "positive" ? CheckCircle2 : point.tone === "attention" ? CircleAlert : CircleDot; return <div key={`${point.title}-${point.detail}`} className="flex items-start gap-sm"><Icon className={`mt-[2px] shrink-0 ${point.tone === "positive" ? "text-success" : point.tone === "attention" ? "text-warning" : "text-primary"}`} size={15} aria-hidden="true" /><div><p className="font-semibold text-text-primary">{point.title}</p><p className="mt-xs">{point.detail}</p></div></div>; })}</div> : null}{answer.bottom_line ? <div className="flex items-start gap-sm rounded-md bg-background p-sm"><Lightbulb className="mt-[2px] shrink-0 text-primary" size={15} aria-hidden="true" /><p>{answer.bottom_line}</p></div> : null}{answer.limitations ? <p className="text-warning">{answer.limitations}</p> : null}</div></article>;
}

function CompareResponseCard({ answer }: { answer: AICompareAnswer }) {
  const { t } = useTranslation();
  return <article className="mr-lg overflow-hidden rounded-lg border border-blue-100 bg-white shadow-card"><div className="border-b border-blue-100 bg-blue-50/60 px-md py-sm"><p className="text-caption font-semibold text-text-primary">{answer.headline}</p><p className="mt-xs text-caption text-text-secondary">{answer.summary}</p></div><div className="space-y-md px-md py-md text-caption text-text-secondary"><ComparisonGroup title={answer.primary_positioning.borough_name} items={answer.primary_advantages} /><ComparisonGroup title={answer.comparison_positioning.borough_name} items={answer.comparison_advantages} /><div className="grid gap-sm sm:grid-cols-2">{[answer.primary_positioning, answer.comparison_positioning].map((item) => <div key={item.borough_name} className="rounded-md bg-background p-sm"><p className="font-semibold text-text-primary">{item.borough_name}</p><p className="mt-xs font-medium text-primary">{item.label}</p><p className="mt-xs">{item.description}</p></div>)}</div><div className="flex items-start gap-sm rounded-md bg-blue-50/60 p-sm"><Lightbulb className="mt-[2px] shrink-0 text-primary" size={15} aria-hidden="true" /><p>{answer.decision_note}</p></div>{answer.evidence.length ? <details className="rounded-md border border-border px-sm py-sm"><summary className="cursor-pointer font-semibold text-text-primary">{t("ai.viewEvidence")}</summary><div className="mt-sm space-y-xs">{answer.evidence.map((item) => <p key={`${item.label}-${item.primary_value}`}>{item.label}: {formatEvidenceValue(item.primary_value)} vs {formatEvidenceValue(item.comparison_value)}</p>)}</div></details> : null}</div></article>;
}

function ComparisonGroup({ title, items }: { title: string; items: AICompareAnswer["primary_advantages"] }) {
  if (!items.length) return null;
  return <div><p className="font-semibold text-text-primary">{title}</p><div className="mt-sm space-y-sm">{items.map((item) => <div key={`${item.dimension}-${item.explanation}`} className="flex items-start gap-sm"><CheckCircle2 className="mt-[2px] shrink-0 text-success" size={15} aria-hidden="true" /><div><p className="font-semibold text-text-primary">{item.dimension}</p><p className="mt-xs">{item.explanation}</p></div></div>)}</div></div>;
}

function formatEvidenceValue(value: string) {
  const normalized = value.trim().replace(/,/g, "");
  if (!/^-?\d+(?:\.\d+)?$/.test(normalized)) return value;
  const numericValue = Number(normalized);
  if (!Number.isFinite(numericValue)) return value;
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: 1 }).format(numericValue);
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
