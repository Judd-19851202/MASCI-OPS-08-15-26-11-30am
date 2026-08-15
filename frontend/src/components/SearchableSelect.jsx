import React, { useEffect, useMemo, useRef, useState } from "react";
import { Check, ChevronDown, Search, X } from "lucide-react";
import { useT } from "@/lib/i18n";

/**
 * SearchableSelect — typeahead combobox that drops in where a native
 * <select> would normally go.
 *
 * Why not use Radix Combobox or react-select? Both are heavier than
 * what we need here, and they handle keyboard / accessibility behavior
 * differently than the rest of the MASCI Hub form inputs. This local
 * widget keeps styling identical to our other border-2 + h-12 inputs,
 * supports search-as-you-type, full keyboard navigation (↑/↓/Enter/Esc),
 * and renders nicely on touch devices (mobile dropdown stays open
 * while you type without jumping).
 *
 * Props:
 *   value:        currently selected option string
 *   onChange:     fn(nextValue) — called with the chosen option
 *   options:      array of strings (or {value,label} objects)
 *   placeholder:  empty-state text
 *   className:    extra classes on the root button
 *   testId:       data-testid for Playwright
 *   searchPlaceholder: optional override for the search input
 */
export function SearchableSelect({
  value,
  onChange,
  options = [],
  placeholder = "Select…",
  className = "",
  testId,
  searchPlaceholder = "Search…",
  disabled = false,
}) {
  const { t } = useT();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [activeIdx, setActiveIdx] = useState(-1);
  const rootRef = useRef(null);
  const searchRef = useRef(null);

  // Normalize options so the rest of the file can lean on .value/.label
  const normalized = useMemo(
    () =>
      options.map((opt) =>
        typeof opt === "string" ? { value: opt, label: opt } : opt,
      ),
    [options],
  );

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return normalized;
    return normalized.filter((o) => o.label.toLowerCase().includes(q));
  }, [normalized, query]);

  // Close on outside click
  useEffect(() => {
    if (!open) return undefined;
    const onDocClick = (e) => {
      if (!rootRef.current?.contains(e.target)) {
        setOpen(false);
        setQuery("");
        setActiveIdx(-1);
      }
    };
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, [open]);

  // Auto-focus the search box when the menu opens
  useEffect(() => {
    if (open) {
      const t = setTimeout(() => searchRef.current?.focus(), 30);
      return () => clearTimeout(t);
    }
    return undefined;
  }, [open]);

  // Reset highlight when filter changes
  useEffect(() => {
    setActiveIdx(filtered.length > 0 ? 0 : -1);
  }, [filtered.length, query]);

  const choose = (val) => {
    onChange?.(val);
    setOpen(false);
    setQuery("");
    setActiveIdx(-1);
  };

  const onKeyDown = (e) => {
    if (e.key === "Escape") {
      setOpen(false);
      setQuery("");
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIdx((i) => Math.min(filtered.length - 1, i + 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIdx((i) => Math.max(0, i - 1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (activeIdx >= 0 && filtered[activeIdx]) choose(filtered[activeIdx].value);
    }
  };

  const selectedLabel = normalized.find((o) => o.value === value)?.label || "";

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        onClick={() => !disabled && setOpen((o) => !o)}
        disabled={disabled}
        data-testid={testId}
        className={`wp17-focus-ring wp17-control w-full h-12 rounded-[1rem] border border-[color:var(--border-bold)] bg-white px-3.5 text-[0.95rem] text-left flex items-center justify-between gap-2 ${
          disabled ? "opacity-60 cursor-not-allowed border-[color:var(--border-hairline)] bg-[color:var(--surface-disabled)] text-[color:var(--ink-disabled)]" : open ? "border-[color:var(--brand-primary)]" : "hover:border-slate-400"
        } ${className}`}
      >
        <span className={`truncate ${selectedLabel ? "text-[color:var(--ink-strong)]" : "text-[color:var(--ink-faint)]"}`}>
          {selectedLabel || t(placeholder)}
        </span>
        <ChevronDown
          className={`w-4 h-4 text-[color:var(--ink-faint)] shrink-0 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open && (
        <div
          className="wp17-picker-panel absolute z-40 mt-2 w-full overflow-hidden"
          data-testid={testId ? `${testId}-menu` : undefined}
        >
          <div className="wp17-picker-toolbar p-2.5">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-2 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
              <input
                ref={searchRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={onKeyDown}
                placeholder={t(searchPlaceholder)}
                className="wp17-focus-ring wp17-control w-full h-11 rounded-[0.9rem] border border-[color:var(--border-bold)] bg-white pl-8 pr-8 text-[0.95rem] text-[color:var(--ink-strong)] placeholder:text-[color:var(--ink-faint)]"
                data-testid={testId ? `${testId}-search` : undefined}
              />
              {query && (
                <button
                  type="button"
                  onClick={() => setQuery("")}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700"
                  aria-label={t("Clear search")}
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
          <ul className="masci-selector-scroll max-h-64 p-1.5" role="listbox">
            {filtered.length === 0 && (
              <li className="wp17-picker-empty italic">{t("No matches")}</li>
            )}
            {filtered.map((opt, i) => {
              const active = i === activeIdx;
              const selected = opt.value === value;
              return (
                <li
                  key={opt.value}
                  role="option"
                  aria-selected={selected}
                  onMouseEnter={() => setActiveIdx(i)}
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => choose(opt.value)}
                  className={`wp17-picker-option cursor-pointer text-[0.95rem] ${selected ? "font-semibold" : ""}`}
                  data-active={active ? "true" : "false"}
                  data-selected={selected ? "true" : "false"}
                  data-testid={testId ? `${testId}-option-${opt.value}` : undefined}
                >
                  <span className="truncate">{opt.label}</span>
                  {selected && <Check className="w-4 h-4 text-red-700 shrink-0" />}
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}

export default SearchableSelect;
