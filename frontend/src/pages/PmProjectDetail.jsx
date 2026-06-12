// PmProjectDetail.jsx — Phase V-Prelude · Wave 1.1.
//
// Calm per-project detail surface that hosts the Operational Timeline
// sidecar. This page is intentionally MINIMAL — its sole job is to
// give the chronology sidecar a high-context home inside the PM portal,
// so real operators can validate timeline usability during the Wave 1
// observation window.
//
// DO NOT add tiles, KPIs, charts, or dashboard widgets here (Wave 1.1
// hard rule: "no dashboard additions"). This is a single-project
// chronology surface.
//
// Track 13.13 (2026-06-12) · Build Queue #4 — Operational Events
// Project-Day Panel. Calm, read-only, text-only. Source: existing
// public endpoint GET /api/operational-events/project-day/{project_number}/{date}.
// NO charts, NO KPIs, NO invented categories, NO fabricated counts.
// Endpoint returns per-asset arrival/departure rows; the panel renders
// exactly that shape (asset · first_seen · last_seen · still_on_site).
// Empty + offline + error states are honest. No new backend, no new
// route, no new permission.

import React from "react";
import { useParams, Link } from "react-router-dom";
import { Briefcase, Activity } from "lucide-react";
import PmShell from "@/components/PmShell";
import OperationalTimelineSidecar from "@/components/operational/OperationalTimelineSidecar";
import TrenchSafetyOnProjectPanel from "@/components/trench/TrenchSafetyOnProjectPanel";

const API = `${process.env.REACT_APP_BACKEND_URL || ""}/api`;

// Render YYYY-MM-DD for the local user's calendar day. Endpoint expects
// a literal YYYY-MM-DD path segment with no timezone qualifier.
function todayYyyyMmDd() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

// Read-only project-day panel. Public endpoint · no auth headers needed.
// State machine:
//   loading  → fetching
//   error    → endpoint failed or returned ok=false
//   empty    → ok=true but assets.length===0 and total_events===0
//   data     → ok=true with assets to render
function ProjectDayEventsPanel({ projectNumber }) {
  const [date, setDate] = React.useState(todayYyyyMmDd());
  const [state, setState] = React.useState({ status: "loading", body: null, err: null });

  React.useEffect(() => {
    if (!projectNumber || !date) return undefined;
    let cancelled = false;
    // Reset to loading via a microtask so we don't call setState
    // synchronously inside the effect body.
    Promise.resolve().then(() => {
      if (!cancelled) setState({ status: "loading", body: null, err: null });
    });
    fetch(`${API}/operational-events/project-day/${encodeURIComponent(projectNumber)}/${encodeURIComponent(date)}`)
      .then(async (r) => {
        if (cancelled) return;
        if (!r.ok) {
          setState({ status: "error", body: null, err: `HTTP ${r.status}` });
          return;
        }
        const body = await r.json().catch(() => null);
        if (!body || body.ok !== true) {
          setState({ status: "error", body, err: "Bad response shape" });
          return;
        }
        setState({ status: "data", body, err: null });
      })
      .catch((e) => {
        if (cancelled) return;
        setState({ status: "error", body: null, err: e.message || "Fetch failed" });
      });
    return () => { cancelled = true; };
  }, [projectNumber, date]);

  const assets = state.body?.assets || [];
  const total = state.body?.total_events ?? 0;

  return (
    <section
      data-testid="pm-project-day-events-panel"
      className="bg-white border border-slate-200 rounded-md p-4 sm:p-6 mt-4"
    >
      <header className="flex items-baseline gap-2 flex-wrap">
        <Activity className="w-4 h-4 text-slate-400 shrink-0" aria-hidden="true" />
        <h2 className="font-display text-base font-bold text-slate-900">
          Project-Day Events
        </h2>
        <span className="text-[11px] text-slate-500 italic">
          Daily operational activity for this project.
        </span>
        <label className="ml-auto inline-flex items-center gap-2 text-[11px] text-slate-600">
          <span className="font-mono uppercase tracking-wide">Day</span>
          <input
            data-testid="pm-project-day-events-date"
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value || todayYyyyMmDd())}
            className="font-mono text-[11px] px-2 py-1 border border-slate-200 rounded bg-slate-50 text-slate-800"
          />
        </label>
      </header>

      <p className="text-[11px] text-slate-500 mt-2">
        Source: <code className="font-mono">/api/operational-events/project-day/{`{project_number}`}/{`{date}`}</code> · per-asset arrival + departure summary for the chosen UTC day.
      </p>

      {state.status === "loading" && (
        <p data-testid="pm-project-day-events-loading" className="text-xs text-slate-500 mt-3">
          Loading project-day events…
        </p>
      )}

      {state.status === "error" && (
        <div
          data-testid="pm-project-day-events-error"
          className="mt-3 text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded px-3 py-2"
        >
          Project-day feed unavailable ({state.err || "unknown"}). No fabricated data is shown. Retry by reselecting the date.
        </div>
      )}

      {state.status === "data" && assets.length === 0 && (
        <div
          data-testid="pm-project-day-events-empty"
          className="mt-3 text-xs text-slate-600 bg-slate-50 border border-slate-200 rounded px-3 py-2"
        >
          No project-day events recorded on {date}. <span className="text-slate-400">total_events = {total}</span>
        </div>
      )}

      {state.status === "data" && assets.length > 0 && (
        <div className="mt-3 overflow-x-auto">
          <div className="text-[11px] text-slate-500 mb-2">
            <span data-testid="pm-project-day-events-count">
              {assets.length} asset(s) · {total} total event(s)
            </span>
          </div>
          <table
            data-testid="pm-project-day-events-table"
            className="w-full text-xs border-collapse"
          >
            <thead>
              <tr className="text-left text-[10px] uppercase tracking-wide text-slate-500 border-b border-slate-200">
                <th className="py-1.5 pr-3 font-mono">Asset</th>
                <th className="py-1.5 pr-3 font-mono">Kind</th>
                <th className="py-1.5 pr-3 font-mono">First seen</th>
                <th className="py-1.5 pr-3 font-mono">Last seen</th>
                <th className="py-1.5 pr-3 font-mono">Status</th>
              </tr>
            </thead>
            <tbody>
              {assets.map((a) => (
                <tr
                  key={a.asset_key}
                  data-testid={`pm-project-day-events-row-${a.asset_key}`}
                  className="border-b border-slate-100 last:border-b-0"
                >
                  <td className="py-1.5 pr-3 font-mono text-slate-800">
                    {a.asset_label || a.asset_key}
                  </td>
                  <td className="py-1.5 pr-3 text-slate-600">
                    {a.asset_kind || "—"}
                  </td>
                  <td className="py-1.5 pr-3 font-mono text-slate-700">
                    {a.first_seen || "—"}
                  </td>
                  <td className="py-1.5 pr-3 font-mono text-slate-700">
                    {a.last_seen || (a.still_on_site ? "—" : "—")}
                  </td>
                  <td className="py-1.5 pr-3">
                    {a.still_on_site ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-bold uppercase tracking-wide">
                        On site
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-slate-50 text-slate-600 border border-slate-200 text-[10px] font-bold uppercase tracking-wide">
                        Departed
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export default function PmProjectDetail() {
  const { projectNumber } = useParams();
  const pn = (projectNumber || "").trim();

  return (
    <PmShell
      title="Project detail"
      section="jobs"
      intro={
        <p className="text-xs text-slate-500">
          Single-project chronology view (read-only).
        </p>
      }
    >
      <div
        data-testid="pm-project-detail-page"
        className="bg-white border border-slate-200 rounded-md p-4 sm:p-6"
      >
        <header className="flex items-baseline gap-2 flex-wrap">
          <Briefcase className="w-4 h-4 text-slate-400 shrink-0" aria-hidden="true" />
          <span
            data-testid="pm-project-detail-number"
            className="font-mono font-bold text-slate-900 text-lg break-all"
          >
            {pn || "—"}
          </span>
          <Link
            to="/pm/jobs"
            data-testid="pm-project-detail-back"
            className="ml-auto text-xs text-slate-500 hover:text-slate-800 underline-offset-2 hover:underline"
          >
            ← All jobs
          </Link>
        </header>
        <p className="text-xs text-slate-500 mt-1">
          Operational chronology for this project. Calm, text-only —
          no charts, no notifications, no editing surface.
        </p>
      </div>

      <OperationalTimelineSidecar projectNumber={pn} />

      {/* Track 13.13 · Build Queue #4 — Operational Events Project-Day
          panel. Read-only · honest empty/error states · no charts ·
          no invented categories. Source: GET /api/operational-events/
          project-day/{project_number}/{date}. */}
      {pn && <ProjectDayEventsPanel projectNumber={pn} />}

      {/* Phase 4A — Trench Safety Operations Integration */}
      <TrenchSafetyOnProjectPanel projectNumber={pn} />
    </PmShell>
  );
}
