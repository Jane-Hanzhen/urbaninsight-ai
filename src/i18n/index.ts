import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "@/i18n/locales/en.json";
import zhCN from "@/i18n/locales/zh-CN.json";

export const supportedLocales = ["en", "zh-CN"] as const;
export type SupportedLocale = (typeof supportedLocales)[number];
const STORAGE_KEY = "urbaninsight-language";

function detectLocale(): SupportedLocale {
  const saved = window.localStorage.getItem(STORAGE_KEY);
  if (saved === "en" || saved === "zh-CN") return saved;
  return window.navigator.language.toLowerCase().startsWith("zh") ? "zh-CN" : "en";
}

void i18n.use(initReactI18next).init({
  resources: { en: { translation: en }, "zh-CN": { translation: zhCN } },
  lng: detectLocale(),
  fallbackLng: "en",
  interpolation: { escapeValue: false }
});

i18n.on("languageChanged", (language) => {
  if (language === "en" || language === "zh-CN") {
    window.localStorage.setItem(STORAGE_KEY, language);
    document.documentElement.lang = language;
  }
});
document.documentElement.lang = i18n.resolvedLanguage ?? "en";

export function currentLocale(): SupportedLocale {
  return i18n.resolvedLanguage === "zh-CN" ? "zh-CN" : "en";
}

export default i18n;
