import React, { useState, useMemo } from "react";
import { Check, ChevronDown, Search, Pencil } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { cn } from "@/lib/utils";
import { useT } from "@/lib/i18n";
import { TOPIC_LIBRARY_ES } from "@/lib/meetingTopicLibrary.es";

// Domain chip labels (EN + ES). Keep this list short and operational.
// `key` matches the `domain` field on each topic in meetingTopicLibrary.js.
// Topics with no `domain` fall under "general".
const DOMAIN_CHIPS = [
  { key: null, en: "All", es: "Todos" },
  { key: "trucking", en: "Trucking", es: "Camiones" },
  { key: "dewatering", en: "Dewatering", es: "Desagüe" },
  { key: "shop", en: "Shop", es: "Taller" },
  { key: "plant", en: "Plant / Lab", es: "Planta / Lab" },
  { key: "airport", en: "Airport", es: "Aeropuerto" },
  { key: "office", en: "Office", es: "Oficina" },
  { key: "general", en: "General", es: "General" },
];

/**
 * Searchable topic picker for the Site Safety Meeting form.
 *
 * Props:
 *   value          - current selected key (CUSTOM_TOPIC_KEY or topic key)
 *   onChange(key)  - called when user picks an option
 *   topics         - array of topic objects { key, title, category, domain? }
 *   customKey      - special key representing "Custom Topic"
 *   placeholder    - placeholder text for trigger
 */
export function TopicPicker({
  value,
  onChange,
  topics,
  customKey,
  placeholder = "Select a topic...",
}) {
  const [open, setOpen] = useState(false);
  const [domainFilter, setDomainFilter] = useState(null); // null = all
  const { t, lang } = useT();

  // Helper: returns the topic title in the active language.
  const titleFor = (topic) => {
    if (lang === "es" && TOPIC_LIBRARY_ES[topic.key]?.title) {
      return TOPIC_LIBRARY_ES[topic.key].title;
    }
    return topic.title;
  };

  const selectedLabel = useMemo(() => {
    if (!value || value === customKey) return null;
    const found = topics.find((tt) => tt.key === value);
    return found ? titleFor(found) : null;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, topics, customKey, lang]);

  // Domain counts (over the full topic list, ignoring current filter)
  const domainCounts = useMemo(() => {
    const counts = { __all: topics.length };
    topics.forEach((tt) => {
      const d = tt.domain || "general";
      counts[d] = (counts[d] || 0) + 1;
    });
    return counts;
  }, [topics]);

  // Only show chips that have at least one topic
  const visibleChips = useMemo(
    () =>
      DOMAIN_CHIPS.filter(
        (c) => c.key === null || (domainCounts[c.key] || 0) > 0
      ),
    [domainCounts]
  );

  // Apply domain filter
  const filteredTopics = useMemo(() => {
    if (!domainFilter) return topics;
    return topics.filter((tt) => (tt.domain || "general") === domainFilter);
  }, [topics, domainFilter]);

  // Group topics by category for nicer scanning
  const grouped = useMemo(() => {
    const map = new Map();
    filteredTopics.forEach((tt) => {
      const cat = tt.category || "Other";
      if (!map.has(cat)) map.set(cat, []);
      map.get(cat).push(tt);
    });
    return Array.from(map.entries());
  }, [filteredTopics]);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          role="combobox"
          aria-expanded={open}
          variant="outline"
          className={cn(
            "h-14 w-full mt-2 justify-between text-base font-normal",
            "border-2 border-red-300 bg-white hover:bg-white hover:border-red-500",
            "focus-visible:ring-2 focus-visible:ring-red-500 focus-visible:ring-offset-2"
          )}
          data-testid="topic-picker-trigger"
        >
          <span className="flex items-center gap-2 truncate">
            <Search className="w-4 h-4 text-slate-500 shrink-0" />
            <span className="truncate text-slate-900">
              {selectedLabel
                ? selectedLabel
                : value === customKey
                ? t("Custom Topic — write your own")
                : placeholder}
            </span>
          </span>
          <ChevronDown className="w-4 h-4 text-slate-500 shrink-0 ml-2" />
        </Button>
      </PopoverTrigger>
      <PopoverContent
        className="p-0 w-[var(--radix-popover-trigger-width)] max-w-none"
        align="start"
        data-testid="topic-picker-content"
      >
        {/* Domain filter chip row */}
        <div
          className="flex gap-1.5 overflow-x-auto px-3 pt-3 pb-2 border-b border-slate-100 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
          data-testid="topic-picker-domain-row"
        >
          {visibleChips.map((chip) => {
            const isActive = domainFilter === chip.key;
            const count =
              chip.key === null
                ? domainCounts.__all
                : domainCounts[chip.key] || 0;
            const label = lang === "es" ? chip.es : chip.en;
            return (
              <button
                key={chip.key || "all"}
                type="button"
                onClick={() => setDomainFilter(chip.key)}
                className={cn(
                  "shrink-0 inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors",
                  isActive
                    ? "bg-red-700 text-white border-red-700"
                    : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
                )}
                data-testid={`topic-picker-domain-${chip.key || "all"}`}
              >
                <span>{label}</span>
                <span
                  className={cn(
                    "text-[10px] font-semibold",
                    isActive ? "text-white/90" : "text-slate-500"
                  )}
                >
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        <Command
          filter={(itemValue, search) => {
            // itemValue is "<title> <category>" lowercased — match on substring
            return itemValue.toLowerCase().includes(search.toLowerCase()) ? 1 : 0;
          }}
        >
          <CommandInput
            placeholder={t("Search topics (e.g. trench, silica, heat)...")}
            className="h-12 text-base"
            data-testid="topic-picker-search"
          />
          <CommandList className="max-h-[55vh]">
            <CommandEmpty>{t("No topic matches that search.")}</CommandEmpty>

            <CommandGroup heading={t("Custom")}>
              <CommandItem
                value="custom topic write your own free form"
                onSelect={() => {
                  onChange(customKey);
                  setOpen(false);
                }}
                className="py-3 cursor-pointer"
                data-testid="topic-picker-custom"
              >
                <div className="flex items-start gap-3 w-full">
                  <span className="inline-flex w-7 h-7 items-center justify-center rounded bg-slate-900 text-white shrink-0 mt-0.5">
                    <Pencil className="w-3.5 h-3.5" />
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="font-bold text-slate-900">{t("Custom Topic")}</div>
                    <div className="text-xs text-slate-500 mt-0.5">
                      {t("Clear all fields and write your own")}
                    </div>
                  </div>
                  {value === customKey && (
                    <Check className="w-4 h-4 text-red-700 shrink-0 mt-1" />
                  )}
                </div>
              </CommandItem>
            </CommandGroup>

            {grouped.map(([category, list]) => (
              <CommandGroup
                key={category}
                heading={`${category} · ${list.length}`}
              >
                {list.map((topic) => {
                  const displayTitle = titleFor(topic);
                  return (
                    <CommandItem
                      key={topic.key}
                      // include EN + ES titles + category so search matches either language
                      value={`${topic.title} ${displayTitle} ${topic.category} ${topic.key}`}
                      onSelect={() => {
                        onChange(topic.key);
                        setOpen(false);
                      }}
                      className="py-2.5 cursor-pointer"
                      data-testid={`topic-picker-item-${topic.key}`}
                    >
                      <div className="flex items-start gap-3 w-full">
                        <span className="inline-flex w-1.5 h-1.5 rounded-full bg-red-700 shrink-0 mt-2" />
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-slate-900 leading-snug">
                            {displayTitle}
                          </div>
                        </div>
                        {value === topic.key && (
                          <Check className="w-4 h-4 text-red-700 shrink-0 mt-1" />
                        )}
                      </div>
                    </CommandItem>
                  );
                })}
              </CommandGroup>
            ))}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
