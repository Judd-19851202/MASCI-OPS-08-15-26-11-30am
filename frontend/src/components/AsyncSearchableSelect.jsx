import React, { useCallback, useEffect, useRef, useState } from "react";
import { Check, Search, X } from "lucide-react";
import { useT } from "@/lib/i18n";

export function AsyncSearchableSelect({
  testId,
  label,
  optionalHint,
  placeholder,
  required,
  value,
  onChange,
  loadOptions,
  emptyHint,
  tempPrefix,
  autoFocus,
  prefetch,
  minQuery,
}) {
  const { t } = useT();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef(null);
  const containerRef = useRef(null);

  const refresh = useCallback(
    async (q) => {
      if ((q || "").length < (minQuery || 0)) {
        setOptions([]);
        return;
      }
      setLoading(true);
      try {
        const opts = await loadOptions(q);
        setOptions(Array.isArray(opts) ? opts : []);
      } catch {
        setOptions([]);
      } finally {
        setLoading(false);
      }
    },
    [loadOptions, minQuery],
  );

  useEffect(() => {
    if (prefetch) refresh("");
  }, [prefetch, refresh]);

  useEffect(() => {
    if (!open) return;
    const timer = setTimeout(() => refresh(query), 180);
    return () => clearTimeout(timer);
  }, [query, open, refresh]);

  useEffect(() => {
    if (!open) return;
    const handler = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    document.addEventListener("touchstart", handler);
    return () => {
      document.removeEventListener("mousedown", handler);
      document.removeEventListener("touchstart", handler);
    };
  }, [open]);

  const display = value?.label || "";
  const canAddTemp =
    query.trim().length > 0 &&
    !options.some((opt) => opt.label.toLowerCase() === query.trim().toLowerCase());

  const choose = (opt) => {
    onChange({ label: opt.label, refId: opt.refId || "", isTemp: false });
    setQuery("");
    setOpen(false);
  };

  const addTemp = () => {
    const nextValue = query.trim();
    if (!nextValue) return;
    onChange({ label: nextValue, refId: "", isTemp: true });
    setQuery("");
    setOpen(false);
  };

  const clear = () => {
    onChange(null);
    setQuery("");
    inputRef.current?.focus();
  };

  return (
    <div ref={containerRef} className="block" data-testid={`${testId}-wrap`}>
      <div className="mb-2 flex items-baseline justify-between gap-3">
        <span className="font-mono text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">
          {label}
          {required ? <span className="ml-1 text-red-700">*</span> : null}
        </span>
        {optionalHint ? (
          <span className="text-[10px] uppercase tracking-[0.25em] text-slate-400">
            {optionalHint}
          </span>
        ) : null}
      </div>

      {value?.label ? (
        <button
          type="button"
          data-testid={`${testId}-selected`}
          onClick={clear}
          className="wp17-control w-full rounded-[1rem] border border-emerald-300 bg-emerald-50/70 px-4 py-3 text-left shadow-[0_18px_30px_rgba(5,150,105,0.08)]"
        >
          <span className="flex items-center justify-between gap-3">
            <span className="truncate text-[0.95rem] font-semibold text-[color:var(--ink-strong)]">
              {display}
              {value.isTemp ? (
                <span className="ml-2 rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 font-mono text-[10px] uppercase tracking-[0.18em] text-amber-800">
                  {t("temp")}
                </span>
              ) : null}
            </span>
            <span className="inline-flex items-center gap-1 text-[11px] font-mono uppercase tracking-[0.2em] text-emerald-700">
              <X className="h-3.5 w-3.5" />
              {t("Change")}
            </span>
          </span>
        </button>
      ) : (
        <>
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              ref={inputRef}
              type="text"
              data-testid={testId}
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setOpen(true);
              }}
              onFocus={() => setOpen(true)}
              placeholder={t(placeholder)}
              required={!!required}
              autoFocus={!!autoFocus}
              autoComplete="off"
              autoCorrect="off"
              autoCapitalize="words"
              spellCheck={false}
              className="wp17-focus-ring wp17-control w-full rounded-[1rem] border border-[color:var(--border-bold)] bg-white py-3 pl-10 pr-4 text-[0.95rem] text-[color:var(--ink-strong)] placeholder:text-[color:var(--ink-faint)]"
            />
          </div>
          {open ? (
            <div
              data-testid={`${testId}-panel`}
              className="wp17-picker-panel mt-2 max-h-60 overflow-y-auto p-1.5"
            >
              {loading ? (
                <div className="wp17-picker-empty" data-testid={`${testId}-loading`}>
                  {t("Looking…")}
                </div>
              ) : options.length === 0 ? (
                <div className="wp17-picker-empty" data-testid={`${testId}-empty`}>
                  {query.trim().length < (minQuery || 0)
                    ? emptyHint || t("Type at least 2 letters to search.")
                    : t("No matches yet.")}
                </div>
              ) : (
                options.map((opt) => (
                  <button
                    type="button"
                    key={`${opt.refId || ""}-${opt.label}`}
                    onClick={() => choose(opt)}
                    data-testid={`${testId}-option`}
                  className="wp17-picker-option group text-left text-sm"
                  >
                    <span className="min-w-0 flex-1 truncate">{opt.label}</span>
                    <div className="flex items-center gap-2 shrink-0">
                      {opt.hint ? (
                        <span className="text-[11px] uppercase tracking-[0.18em] text-slate-400">
                          {opt.hint}
                        </span>
                      ) : null}
                      <Check className="h-3.5 w-3.5 text-emerald-600 opacity-0 group-hover:opacity-100" />
                    </div>
                  </button>
                ))
              )}
              {canAddTemp ? (
                <button
                  type="button"
                  onClick={addTemp}
                  data-testid={`${testId}-add-temp`}
                  className="mt-1 flex w-full items-center gap-2 rounded-[0.95rem] border border-amber-200 bg-amber-50 px-3 py-2 text-left text-sm text-amber-900 transition-colors hover:bg-amber-100"
                >
                  <span className="font-mono text-[10px] uppercase tracking-[0.18em]">
                    {tempPrefix || t("Add temporary:")}
                  </span>
                  <span className="truncate font-semibold">{query.trim()}</span>
                </button>
              ) : null}
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}

export default AsyncSearchableSelect;