import { useEffect, useMemo, useRef, useState } from "react";
import { MapPin, Search, X } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

type BoroughSearchProps = {
  boroughs: string[];
  selectedBorough: string | null;
  onSelectBorough: (boroughName: string) => void;
};

export function BoroughSearch({
  boroughs,
  selectedBorough,
  onSelectBorough
}: BoroughSearchProps) {
  const { t } = useTranslation();
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setQuery(selectedBorough ?? "");
  }, [selectedBorough]);

  useEffect(() => {
    const handlePointerDown = (event: PointerEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("pointerdown", handlePointerDown);
    return () => document.removeEventListener("pointerdown", handlePointerDown);
  }, []);

  const matches = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized || normalized === selectedBorough?.toLowerCase()) {
      return boroughs.slice(0, 6);
    }
    return boroughs
      .filter((borough) => borough.toLowerCase().includes(normalized))
      .slice(0, 6);
  }, [boroughs, query, selectedBorough]);

  const selectBorough = (boroughName: string) => {
    setQuery(boroughName);
    setIsOpen(false);
    onSelectBorough(boroughName);
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Escape") {
      setIsOpen(false);
      return;
    }

    if (event.key === "Enter" && matches[0]) {
      event.preventDefault();
      selectBorough(matches[0]);
    }
  };

  return (
    <div ref={containerRef} className="relative">
      <Search
        className="pointer-events-none absolute left-md top-1/2 z-10 -translate-y-1/2 text-text-secondary"
        size={17}
        aria-hidden="true"
      />
      <Input
        role="combobox"
        aria-expanded={isOpen}
        aria-controls="borough-search-results"
        aria-autocomplete="list"
        aria-label={t("search.label")}
        value={query}
        placeholder={t("search.placeholder")}
        className="pl-[44px] pr-[44px]"
        onFocus={() => setIsOpen(true)}
        onChange={(event) => {
          setQuery(event.target.value);
          setIsOpen(true);
        }}
        onKeyDown={handleKeyDown}
      />

      {query ? (
        <Button
          type="button"
          variant="ghost"
          size="icon"
          aria-label={t("search.clear")}
          className="absolute right-xs top-1/2 h-9 min-h-9 w-9 -translate-y-1/2"
          onClick={() => {
            setQuery("");
            setIsOpen(true);
          }}
        >
          <X size={16} aria-hidden="true" />
        </Button>
      ) : null}

      {isOpen ? (
        <div
          id="borough-search-results"
          role="listbox"
          className="absolute left-0 right-0 top-[calc(100%+8px)] z-30 rounded-lg border border-border bg-surface p-sm shadow-panel"
        >
          {matches.length ? (
            matches.map((borough) => (
              <button
                key={borough}
                type="button"
                role="option"
                aria-selected={borough === selectedBorough}
                className="flex min-h-10 w-full items-center gap-sm rounded-full px-md text-left text-caption text-text-primary transition-colors duration-fast hover:bg-blue-50 hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                onClick={() => selectBorough(borough)}
              >
                <MapPin size={15} className="shrink-0 text-text-secondary" aria-hidden="true" />
                <span>{borough}</span>
              </button>
            ))
          ) : (
            <p className="px-md py-sm text-caption text-text-secondary">
              {t("search.empty")}
            </p>
          )}
        </div>
      ) : null}
    </div>
  );
}
