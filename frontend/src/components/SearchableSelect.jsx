import React, { useEffect, useMemo, useRef, useState } from "react";
import { Check, ChevronDown, Search, X } from "lucide-react";

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
        className={`w-full h-12 border-2 border-slate-300 rounded px-3 text-base bg-white text-left flex items-center justify-between gap-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-700 focus-visible:ring-offset-2 ${
          disabled ? "opacity-60 cursor-not-allowed" : "hover:border-slate-400"
        } ${className}`}
      >
        <span className={`truncate ${selectedLabel ? "text-slate-900" : "text-slate-400"}`}>
          {selectedLabel || placeholder}
        </span>
        <ChevronDown
          className={`w-4 h-4 text-slate-500 shrink-0 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open && (
        <div
          className="absolute z-30 mt-1 w-full bg-white border-2 border-slate-300 rounded-md shadow-xl overflow-hidden"
          data-testid={testId ? `${testId}-menu` : undefined}
        >
          <div className="p-2 border-b border-slate-200 bg-slate-50">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-2 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
              <input
                ref={searchRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={onKeyDown}
                placeholder={searchPlaceholder}
                className="w-full h-9 pl-8 pr-8 border-2 border-slate-200 rounded text-sm focus:outline-none focus:border-red-700"
                data-testid={testId ? `${testId}-search` : undefined}
              />
              {query && (
                <button
                  type="button"
                  onClick={() => setQuery("")}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700"
                  aria-label="Clear search"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
          <ul className="max-h-64 overflow-y-auto py-1" role="listbox">
            {filtered.length === 0 && (
              <li className="px-3 py-2 text-sm text-slate-500 italic">No matches</li>
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
                  onMouseDown={(e) => {
                    e.preventDefault();
                    choose(opt.value);
                  }}
                  className={`px-3 py-2 text-sm cursor-pointer flex items-center justify-between gap-2 ${
                    active ? "bg-red-50 text-slate-900" : "text-slate-700"
                  } ${selected ? "font-bold" : ""}`}
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
