import { useEffect, useRef, useState } from "react";
import { Check, Globe2 } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import type { SupportedLocale } from "@/i18n";

export function LanguageSwitcher() {
  const { i18n, t } = useTranslation();
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const locale: SupportedLocale = i18n.resolvedLanguage === "zh-CN" ? "zh-CN" : "en";

  useEffect(() => {
    const close = (event: PointerEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("pointerdown", close);
    return () => document.removeEventListener("pointerdown", close);
  }, []);

  const select = (next: SupportedLocale) => {
    void i18n.changeLanguage(next);
    setOpen(false);
  };

  return (
    <div ref={containerRef} className="relative shrink-0">
      <Button type="button" variant="ghost" aria-label={t("language.label")} aria-haspopup="menu" aria-expanded={open} className="px-sm sm:px-md" onClick={() => setOpen((value) => !value)}>
        <Globe2 size={18} aria-hidden="true" />
        <span className="hidden sm:inline">{locale === "zh-CN" ? t("language.shortChinese") : t("language.shortEnglish")}</span>
      </Button>
      {open ? (
        <div role="menu" className="absolute right-0 top-[calc(100%+8px)] z-30 min-w-40 rounded-md border border-border bg-surface p-xs shadow-panel">
          <LanguageOption active={locale === "en"} label={t("language.english")} onSelect={() => select("en")} />
          <LanguageOption active={locale === "zh-CN"} label={t("language.chinese")} onSelect={() => select("zh-CN")} />
        </div>
      ) : null}
    </div>
  );
}

function LanguageOption({ active, label, onSelect }: { active: boolean; label: string; onSelect: () => void }) {
  return (
    <button type="button" role="menuitemradio" aria-checked={active} onClick={onSelect} className="flex min-h-10 w-full items-center justify-between gap-md rounded-sm px-md text-left text-caption text-text-primary transition-colors hover:bg-blue-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary">
      <span>{label}</span>
      {active ? <Check size={16} className="text-primary" aria-hidden="true" /> : null}
    </button>
  );
}
