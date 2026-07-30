import { Sparkles } from "lucide-react";
import { useTranslation } from "react-i18next";
import { LanguageSwitcher } from "@/components/language/LanguageSwitcher";
import { BoroughSearch } from "@/components/search/BoroughSearch";
import { Switch } from "@/components/ui/switch";
import type { AIProvider } from "@/types/urban";

type AppShellProps = {
  boroughs: string[];
  selectedBorough: string | null;
  onSelectBorough: (boroughName: string) => void;
  map: React.ReactNode;
  aiPanel: React.ReactNode;
  analysis: React.ReactNode;
  aiInsightsEnabled: boolean;
  aiProvider: AIProvider;
  showAISettingNotice: boolean;
  onAIInsightsEnabledChange: (enabled: boolean) => void;
  onAIProviderChange: (provider: AIProvider) => void;
};

export function AppShell({
  boroughs,
  selectedBorough,
  onSelectBorough,
  map,
  aiPanel,
  analysis,
  aiInsightsEnabled,
  aiProvider,
  showAISettingNotice,
  onAIInsightsEnabledChange,
  onAIProviderChange
}: AppShellProps) {
  const { t } = useTranslation();
  return (
    <div className="min-h-screen bg-background text-text-primary">
      <header className="sticky top-0 z-20 border-b border-border bg-background/90 backdrop-blur">
        <div className="mx-auto flex h-[72px] max-w-[1600px] items-center gap-sm px-md sm:gap-md sm:px-xl lg:gap-lg">
          <div className="flex shrink-0 items-center gap-md lg:min-w-[220px]">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-white shadow-card">
              <Sparkles size={18} aria-hidden="true" />
            </div>
            <h1 className="hidden text-[18px] font-bold leading-tight md:block">UrbanInsight AI</h1>
          </div>

          <div className="mx-auto min-w-0 flex-1 lg:max-w-[420px]">
            <BoroughSearch
              boroughs={boroughs}
              selectedBorough={selectedBorough}
              onSelectBorough={onSelectBorough}
            />
          </div>

          <nav className="flex shrink-0 items-center justify-end gap-sm sm:gap-md">
            <div className="flex items-center gap-sm">
              {aiInsightsEnabled ? (
                <Sparkles className="text-primary" size={16} aria-hidden="true" />
              ) : null}
              <span className="hidden whitespace-nowrap text-caption font-semibold text-text-primary sm:inline">
                {t("ai.insightsControl")}
              </span>
              <Switch
                checked={aiInsightsEnabled}
                onCheckedChange={onAIInsightsEnabledChange}
                aria-label={t("ai.insightsControl")}
              />
              <select
                value={aiProvider}
                disabled={!aiInsightsEnabled}
                onChange={(event) => onAIProviderChange(event.target.value as AIProvider)}
                aria-label={t("ai.providerLabel")}
                className="hidden h-9 rounded-full border border-border bg-surface px-md text-caption font-semibold text-text-primary outline-none transition-colors focus:border-primary focus:ring-2 focus:ring-blue-100 disabled:cursor-not-allowed disabled:bg-background disabled:text-text-secondary md:block"
              >
                <option value="deepseek">{t("ai.providers.deepseek")}</option>
                <option value="qwen">{t("ai.providers.qwen")}</option>
              </select>
            </div>
            <span className="hidden h-6 w-px bg-border sm:block" aria-hidden="true" />
            <LanguageSwitcher />
          </nav>
        </div>
      </header>
      {showAISettingNotice ? (
        <div
          role="status"
          className="fixed right-xl top-[84px] z-30 rounded-full border border-border bg-surface px-md py-sm text-caption text-text-secondary shadow-card"
        >
          {t("ai.settingNextAnalysis")}
        </div>
      ) : null}

      <main className="mx-auto max-w-[1600px] space-y-xl px-xl py-xl">
        <section className="grid min-h-[640px] grid-cols-1 gap-lg lg:grid-cols-[minmax(0,7fr)_minmax(340px,3fr)]">
          {map}
          {aiPanel}
        </section>

        {analysis}
      </main>
    </div>
  );
}
