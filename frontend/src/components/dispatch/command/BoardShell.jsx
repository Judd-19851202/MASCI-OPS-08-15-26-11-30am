/**
 * Shared low-level UI primitives for the Dispatch Command Center boards.
 *
 *   <BoardShell> — page chrome: header, search/filter strip slot, status
 *     row count, refresh button, skeleton + empty + error states.
 *   <StatusChip> — calm, tone-keyed status badge.
 *   <IntegrationDot> — small dot indicator for Motive / FleetWatcher /
 *     MaintainX with tooltip-style aria-label.
 */
import React from "react";
import { RefreshCw, Loader2, Inbox, AlertCircle, Search } from "lucide-react";

const TONE = {
  active:       "bg-emerald-100 text-emerald-900 border-emerald-300",
  available:    "bg-slate-100 text-slate-800 border-slate-300",
  oos:          "bg-rose-100 text-rose-900 border-rose-300",
  in_shop:      "bg-amber-100 text-amber-900 border-amber-300",
  defect_open:  "bg-amber-100 text-amber-900 border-amber-300",
  unknown:      "bg-slate-50 text-slate-600 border-slate-200",
  attention:    "bg-rose-100 text-rose-900 border-rose-300",
  waiting:      "bg-amber-100 text-amber-900 border-amber-300",
  breakdown:    "bg-rose-200 text-rose-900 border-rose-400",
  pass:         "bg-emerald-50 text-emerald-800 border-emerald-200",
  fail:         "bg-rose-50 text-rose-800 border-rose-200",
  pending:      "bg-slate-50 text-slate-700 border-slate-200",
  info:         "bg-sky-50 text-sky-900 border-sky-200",
};

export function StatusChip({ tone = "available", children, testId }) {
  const cls = TONE[tone] || TONE.available;
  return (
    <span
      data-testid={testId}
      className={`inline-flex items-center px-2 py-0.5 rounded text-[10.5px] font-bold uppercase tracking-wider border ${cls} whitespace-nowrap`}
    >
      {children}
    </span>
  );
}

export function IntegrationDot({ name, connected, mapped, stale, testId }) {
  const aria = `${name}: ${
    connected ? (stale ? "stale" : mapped ? "live" : "active") : "not connected"
  }`;
  const cls = !connected
    ? "bg-slate-300"
    : stale ? "bg-amber-500"
    : "bg-emerald-500";
  return (
    <span
      data-testid={testId}
      aria-label={aria}
      title={aria}
      className={`inline-block w-2 h-2 rounded-full ${cls}`}
    />
  );
}

export function SearchBar({ value, onChange, placeholder, testId }) {
  return (
    <div className="relative">
      <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder || "Search…"}
        data-testid={testId}
        className="w-full sm:w-72 pl-8 pr-3 py-2 text-sm border border-slate-300 rounded-md focus:border-slate-500 focus:ring-1 focus:ring-slate-400 focus:outline-none bg-white"
      />
    </div>
  );
}

export function FilterChips({ options, value, onChange, testIdRoot }) {
  return (
    <div className="flex flex-wrap items-center gap-1.5" data-testid={`${testIdRoot}-filters`}>
      {options.map((o) => {
        const active = o.value === value;
        return (
          <button
            key={o.value || "all"}
            type="button"
            onClick={() => onChange(o.value)}
            data-testid={`${testIdRoot}-filter-${o.value || "all"}`}
            className={`px-2.5 py-1 text-[11px] font-bold uppercase tracking-wider rounded border transition-colors ${
              active
                ? "bg-slate-900 text-white border-slate-900"
                : "bg-white text-slate-700 border-slate-300 hover:border-slate-500"
            }`}
          >
            {o.label}
            {o.count != null ? (
              <span className={`ml-1.5 font-mono ${active ? "text-slate-200" : "text-slate-500"}`}>
                {o.count}
              </span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}

export function BoardShell({
  title,
  subtitle,
  count,
  onRefresh,
  refreshing,
  toolbar,
  loading,
  error,
  empty,
  emptyText,
  children,
  testId,
}) {
  return (
    <section
      data-testid={testId}
      className="bg-white border border-slate-200 rounded-lg p-3 sm:p-4 space-y-3"
    >
      <header className="flex flex-wrap items-baseline justify-between gap-2">
        <div className="flex items-baseline gap-2">
          <h2 className="font-display text-lg font-black text-slate-900">{title}</h2>
          {count != null ? (
            <span
              data-testid={`${testId}-count`}
              className="font-mono text-xs text-slate-500"
            >
              · {count} {count === 1 ? "row" : "rows"}
            </span>
          ) : null}
          {subtitle ? (
            <span className="font-mono text-[10px] uppercase tracking-widest text-slate-500">
              · {subtitle}
            </span>
          ) : null}
        </div>
        <button
          type="button"
          onClick={onRefresh}
          disabled={refreshing}
          data-testid={`${testId}-refresh`}
          className="inline-flex items-center gap-1.5 text-xs text-slate-600 hover:text-slate-900 border border-slate-300 hover:border-slate-500 rounded px-2.5 py-1 font-mono uppercase tracking-wider disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </header>

      {toolbar ? <div className="flex flex-wrap items-center gap-2">{toolbar}</div> : null}

      {error ? (
        <div
          data-testid={`${testId}-error`}
          className="bg-rose-50 border border-rose-200 text-rose-900 rounded p-3 text-sm flex items-start gap-2"
        >
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
          <div>
            <div className="font-bold">Unable to load</div>
            <div className="text-xs mt-0.5 break-words">{String(error)}</div>
          </div>
        </div>
      ) : loading && !children ? (
        <div className="space-y-2" data-testid={`${testId}-skeleton`}>
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-9 bg-slate-100 rounded animate-pulse" />
          ))}
          <div className="text-center text-xs text-slate-500 font-mono uppercase tracking-widest pt-1 flex items-center justify-center gap-2">
            <Loader2 className="w-3.5 h-3.5 animate-spin" /> loading…
          </div>
        </div>
      ) : empty ? (
        <div
          data-testid={`${testId}-empty`}
          className="text-center py-12 text-slate-500"
        >
          <Inbox className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <div className="text-sm">{emptyText || "Nothing here yet."}</div>
        </div>
      ) : children}
    </section>
  );
}

export default BoardShell;
