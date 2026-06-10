/**
 * pm/command/PmBoardShell.jsx — shared chrome for PM Command Center
 * sections. Mirrors the dispatch BoardShell shape (skeleton · error ·
 * empty · refresh) so the operator sees the same calm states across
 * Dispatch and PM Command Centers.
 */
import React from "react";
import { RefreshCw, Loader2, Inbox, AlertCircle } from "lucide-react";

const TONE = {
  active_haul:   "bg-emerald-100 text-emerald-900 border-emerald-300",
  active_shift:  "bg-sky-100 text-sky-900 border-sky-300",
  available:     "bg-slate-100 text-slate-800 border-slate-300",
  oos:           "bg-rose-100 text-rose-900 border-rose-300",
  in_shop:       "bg-amber-100 text-amber-900 border-amber-300",
  open_defect:   "bg-amber-100 text-amber-900 border-amber-300",
  failed_dvir:   "bg-amber-100 text-amber-900 border-amber-300",
  breakdown:     "bg-rose-200 text-rose-900 border-rose-400",
  no_assignment: "bg-slate-50 text-slate-600 border-slate-200",
  no_driver:     "bg-slate-50 text-slate-600 border-slate-200",
  no_activity:   "bg-slate-50 text-slate-600 border-slate-200",
  material_in:   "bg-emerald-50 text-emerald-900 border-emerald-200",
  material_out:  "bg-sky-50 text-sky-900 border-sky-200",
  incident_open: "bg-rose-100 text-rose-900 border-rose-300",
  capa_open:     "bg-amber-100 text-amber-900 border-amber-300",
  asset_transfer:"bg-indigo-50 text-indigo-800 border-indigo-200",
  dispatch_state_event:"bg-sky-50 text-sky-900 border-sky-200",
  not_connected: "bg-slate-50 text-slate-600 border-slate-200",
  pending_integration: "bg-slate-50 text-slate-600 border-slate-200",
  unknown:       "bg-slate-50 text-slate-500 border-slate-200",
};

export function TrustChip({ state, children, testId }) {
  const cls = TONE[state] || TONE.unknown;
  return (
    <span
      data-testid={testId}
      className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${cls} whitespace-nowrap`}
    >
      {children || state.replace(/_/g, " ")}
    </span>
  );
}

export function IntegrationChip({ name, status, testId }) {
  const display =
    status === "not_connected" ? "Pending Integration" :
    status === "connected" ? "Live" :
    status || "—";
  return (
    <span
      data-testid={testId}
      className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border bg-slate-50 text-slate-500 border-slate-200 whitespace-nowrap"
      title={`${name}: ${display}`}
    >
      {name} · {display}
    </span>
  );
}

export default function PmBoardShell({
  title, subtitle, count, onRefresh, refreshing,
  toolbar, loading, error, empty, emptyText, children, testId,
}) {
  return (
    <section
      data-testid={testId}
      className="bg-white border border-slate-200 rounded-lg p-3 sm:p-4 space-y-3"
    >
      <header className="flex flex-wrap items-baseline justify-between gap-2">
        <div className="flex items-baseline gap-2 flex-wrap">
          <h2 className="font-display text-base sm:text-lg font-black text-slate-900">{title}</h2>
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
        {onRefresh ? (
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
        ) : null}
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
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-9 bg-slate-100 rounded animate-pulse" />
          ))}
          <div className="text-center text-xs text-slate-500 font-mono uppercase tracking-widest pt-1 flex items-center justify-center gap-2">
            <Loader2 className="w-3.5 h-3.5 animate-spin" /> loading…
          </div>
        </div>
      ) : empty ? (
        <div
          data-testid={`${testId}-empty`}
          className="text-center py-8 text-slate-500"
        >
          <Inbox className="w-7 h-7 mx-auto mb-2 opacity-50" />
          <div className="text-sm">{emptyText || "Nothing here yet."}</div>
        </div>
      ) : children}
    </section>
  );
}
