// OperationalTimelineSidecar.jsx — Phase V-Prelude · Wave 1.1 · 2026-05-28.
//
// Calm, READ-ONLY chronology sidecar. Mounts on the PM Project Detail
// surface ONLY (per Wave 1.1 directive). Reads
// `GET /api/timeline?project_id=...` and renders the result via the
// existing `ChronologyPanel` substrate.
//
// Doctrine guarantees (Wave 1.1 hard rules):
//   * PASSIVE — no controls, no mutations, no add-event buttons.
//   * READ-ONLY — every action is a list-render.
//   * ROLE-AWARE — backend already filters audit-only links from
//     non-admin actors; we add no further role gating on the surface
//     because filtering happens server-side.
//   * COMPACT — max-height bounded; no infinite scroll, no overscroll;
//     thumb-safe.
//   * FILTERED — only operationally-meaningful events surface
//     (constraints + chronology + cross-artifact links).
//   * MOBILE-SAFE — single-column rendering at all breakpoints; no
//     horizontal scroll; min tap target ≥ 32 px on mobile.
//
// This is OPERATIONAL CHRONOLOGY, not social activity. Goal: answer
// "what operationally happened?" in calm slate text. Nothing more.

import React from "react";
import { Clock3, RefreshCw } from "lucide-react";
import ChronologyPanel from "@/components/operational/ChronologyPanel";
import { getTimeline } from "@/lib/operationalApi";
import { sanitizeOperatorProjectNumber } from "@/lib/operatorLanguage";

const MAX_VISIBLE = 30;
// Wave 1.1 doctrine: keep the sidecar TIGHT. We bound max-visible at
// 30 with a "show more" affordance — no infinite scroll. If a project
// has >200 events the timeline endpoint flags `truncated=true` and we
// surface that calmly at the foot.

export default function OperationalTimelineSidecar({ projectNumber }) {
  const safeProjectNumber = sanitizeOperatorProjectNumber(projectNumber, "");
  const [state, setState] = React.useState({
    items: null,
    truncated: false,
    error: "",
    generatedAt: null,
    showAll: false,
  });

  const load = React.useCallback(async () => {
    if (!projectNumber) {
      setState((s) => ({ ...s, items: [], error: "" }));
      return;
    }
    setState((s) => ({ ...s, items: null, error: "" }));
    try {
      const r = await getTimeline(projectNumber);
      setState({
        items: Array.isArray(r.items) ? r.items : [],
        truncated: Boolean(r.truncated),
        generatedAt: r.generated_at || null,
        error: "",
        showAll: false,
      });
    } catch (e) {
      setState({
        items: [],
        truncated: false,
        generatedAt: null,
        error: e.message || "Could not load chronology.",
        showAll: false,
      });
    }
  }, [projectNumber]);

  React.useEffect(() => { load(); }, [load]);

  const visible = React.useMemo(() => {
    const all = state.items || [];
    return state.showAll ? all : all.slice(0, MAX_VISIBLE);
  }, [state.items, state.showAll]);

  const total = (state.items || []).length;
  const hidden = Math.max(0, total - MAX_VISIBLE);

  return (
    <section
      data-testid="operational-timeline-sidecar"
      data-project-number={projectNumber || ""}
      className="mt-6 bg-white border border-slate-200 rounded-md"
    >
      {/* Calm header — slate · single accent · no loud chrome. */}
      <header className="px-4 py-3 border-b border-slate-200 flex items-center gap-2 flex-wrap">
        <Clock3
          className="w-4 h-4 text-slate-400 shrink-0"
          aria-hidden="true"
        />
        <h2
          data-testid="operational-timeline-sidecar-title"
          className="text-sm font-semibold text-slate-700 tracking-tight"
        >
          Operational chronology
        </h2>
        <span className="text-xs text-slate-400 ml-1">
          · {safeProjectNumber || "—"}
        </span>
        <button
          type="button"
          onClick={load}
          data-testid="operational-timeline-sidecar-refresh"
          aria-label="Refresh chronology"
          className="ml-auto text-xs text-slate-500 hover:text-slate-700 inline-flex items-center gap-1 px-2 py-1 rounded hover:bg-slate-50 transition-colors min-h-[44px]"
        >
          <RefreshCw className="w-3 h-3" /> Refresh
        </button>
      </header>

      <div className="px-4 py-3">
        {state.error ? (
          <p
            data-testid="operational-timeline-sidecar-error"
            className="text-sm text-rose-700"
          >
            {state.error}
          </p>
        ) : state.items === null ? (
          <p
            data-testid="operational-timeline-sidecar-loading"
            className="text-sm text-slate-500"
          >
            Loading chronology…
          </p>
        ) : total === 0 ? (
          <p
            data-testid="operational-timeline-sidecar-empty"
            className="text-sm text-slate-500 italic py-3"
          >
            No operational events recorded for this project yet.
          </p>
        ) : (
          <>
            {/* Bounded scroll container — mobile thumb-safe; ≤30 rows
                visible until "show all" is clicked. */}
            <div
              data-testid="operational-timeline-sidecar-list"
              className="max-h-[420px] overflow-auto overscroll-contain pr-1"
            >
              <ChronologyPanel
                items={visible}
                emptyText="No operational events recorded for this project yet."
              />
            </div>
            {hidden > 0 && !state.showAll && (
              <button
                type="button"
                onClick={() => setState((s) => ({ ...s, showAll: true }))}
                data-testid="operational-timeline-sidecar-show-all"
                className="mt-2 text-xs text-slate-600 hover:text-slate-900 underline-offset-2 hover:underline min-h-[44px] inline-flex items-center"
              >
                Show all {total} events
              </button>
            )}
            {state.truncated && (
              <p
                data-testid="operational-timeline-sidecar-truncated"
                className="mt-2 text-xs text-slate-500 italic"
              >
                Older events beyond the most recent 200 are hidden by
                design. Filter narrower to surface them.
              </p>
            )}
          </>
        )}
      </div>
    </section>
  );
}
