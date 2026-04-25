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

/**
 * Searchable topic picker for the Site Safety Meeting form.
 *
 * Props:
 *   value          - current selected key (CUSTOM_TOPIC_KEY or topic key)
 *   onChange(key)  - called when user picks an option
 *   topics         - array of topic objects { key, title, category }
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

  const selectedLabel = useMemo(() => {
    if (!value || value === customKey) return null;
    const t = topics.find((t) => t.key === value);
    return t ? t.title : null;
  }, [value, topics, customKey]);

  // Group topics by category for nicer scanning
  const grouped = useMemo(() => {
    const map = new Map();
    topics.forEach((t) => {
      const cat = t.category || "Other";
      if (!map.has(cat)) map.set(cat, []);
      map.get(cat).push(t);
    });
    return Array.from(map.entries());
  }, [topics]);

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
                ? "Custom Topic — write your own"
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
        <Command
          filter={(itemValue, search) => {
            // itemValue is "<title> <category>" lowercased — match on substring
            return itemValue.toLowerCase().includes(search.toLowerCase()) ? 1 : 0;
          }}
        >
          <CommandInput
            placeholder="Search topics (e.g. trench, silica, heat)..."
            className="h-12 text-base"
            data-testid="topic-picker-search"
          />
          <CommandList className="max-h-[55vh]">
            <CommandEmpty>No topic matches that search.</CommandEmpty>

            <CommandGroup heading="Custom">
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
                    <div className="font-bold text-slate-900">Custom Topic</div>
                    <div className="text-xs text-slate-500 mt-0.5">
                      Clear all fields and write your own
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
                {list.map((t) => (
                  <CommandItem
                    key={t.key}
                    // include both title and category for searchability
                    value={`${t.title} ${t.category} ${t.key}`}
                    onSelect={() => {
                      onChange(t.key);
                      setOpen(false);
                    }}
                    className="py-2.5 cursor-pointer"
                    data-testid={`topic-picker-item-${t.key}`}
                  >
                    <div className="flex items-start gap-3 w-full">
                      <span className="inline-flex w-1.5 h-1.5 rounded-full bg-red-700 shrink-0 mt-2" />
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-slate-900 leading-snug">
                          {t.title}
                        </div>
                      </div>
                      {value === t.key && (
                        <Check className="w-4 h-4 text-red-700 shrink-0 mt-1" />
                      )}
                    </div>
                  </CommandItem>
                ))}
              </CommandGroup>
            ))}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
