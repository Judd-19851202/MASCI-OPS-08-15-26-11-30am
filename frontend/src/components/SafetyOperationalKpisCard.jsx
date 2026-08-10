// TRACK 23.8 · Safety Portal — company-wide safety KPI card.
//
// Consumes the shared Track 23.7 operational KPI spine with a
// safety-first framing:
//    * Top: company-wide safety posture (totals + status band)
//    * Middle: window selector (7d / 30d / MTD / PTD)
//    * Bottom-1: project ranking table (top projects by attention)
//    * Bottom-2: per-project drilldown card (fetches
//      `/api/safety/projects/{pn}/safety-kpis`)
//    * Sources coverage strip (LIVE / PARTIAL / MISSING · FUTURE
//      aggregated across all active projects)
//
// ABSOLUTE RULE: NO cost / NO dollars / NO rates. Operational
// production intelligence only.
//
// Backend: GET /api/safety/company/safety-kpis · GET
// /api/safety/projects/{pn}/safety-kpis
// Auth: safety token OR admin token (never PM-assignment restricted).
import React from "react";
import { ShieldAlert, ChevronRight, X } from "lucide-react";
import { api } from "@/lib/api";
import { HelpTip } from "@/components/ui/HelpTip";
import { buildKpiHelpContent } from "@/lib/kpiMetadata";

const SAFETY_KPI_TIMEOUT_MS = 5_000;

function describeSafetyKpiError(error, subject) {
  if (error?.code === "ECONNABORTED" || /timeout/i.test(String(error?.message || ""))) {
    return `${subject} timed out. Safety records, incidents, meetings, and trench workflows remain available.`;
  }
  return error?.response?.data?.detail || error?.message || `Unable to load ${subject.toLowerCase()}`;
}

const WINDOWS = [
  { key: "7d", label: "Last 7 days" },
  { key: "30d", label: "Last 30 days" },
  { key: "mtd", label: "Month to date" },
  { key: "ptd", label: "Project to date" },
];

const BAND_STYLES = {
  green: "bg-emerald-50 border-emerald-300 text-emerald-900",
  amber: "bg-amber-50 border-amber-300 text-amber-900",
  red:   "bg-rose-50 border-rose-300 text-rose-900",
};

function InlineKpiHelp({ metadata, fallbackLabel, testId }) {
  const help = buildKpiHelpContent(metadata, fallbackLabel);
  if (!help) return null;
  return <HelpTip label={help.label} body={help.body} testId={testId} />;
}

export default function SafetyOperationalKpisCard({ className = "" }) {
  const [window, setWindow] = React.useState("30d");
  const [snap, setSnap] = React.useState(null);
  const [err, setErr] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [selectedPn, setSelectedPn] = React.useState(null);
  const [retrySeq, setRetrySeq] = React.useState(0);

  React.useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setErr(null);
    api.get(`/safety/company/safety-kpis?window=${window}`, {
      signal: controller.signal,
      timeout: SAFETY_KPI_TIMEOUT_MS,
    })
      .then((r) => { if (!controller.signal.aborted) setSnap(r.data); })
      .catch((e) => {
        if (!controller.signal.aborted) setErr(describeSafetyKpiError(e, "Company safety rollup"));
      })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [retrySeq, window]);

  return (
    <section
      className={`rounded-md border border-slate-200 bg-white p-4 sm:p-6 ${className}`}
      data-testid="safety-operational-kpis"
    >
      <header className="flex flex-wrap items-baseline gap-3">
        <ShieldAlert className="w-5 h-5 text-slate-500" aria-hidden />
        <h2 className="inline-flex items-center gap-1.5 font-display text-lg font-black text-slate-900" data-testid="safety-kpis-title">
          <span>Company Safety Posture</span>
          <InlineKpiHelp metadata={snap?.kpi_metadata?.page} fallbackLabel="Company Safety Posture" testId="safety-kpis-title-help" />
        </h2>
        <span className="text-xs text-slate-500">Built from the same field records used across the project team, with a safety-first view.</span>
        <div className="ml-auto flex flex-wrap gap-1" role="tablist" aria-label="Window">
          {WINDOWS.map((w) => (
            <button
              key={w.key}
              type="button"
              onClick={() => setWindow(w.key)}
              data-testid={`safety-kpis-window-${w.key}`}
              aria-pressed={window === w.key}
              className={`text-[11px] font-mono uppercase tracking-widest px-2.5 py-1 rounded ${
                window === w.key
                  ? "bg-slate-900 text-white"
                  : "bg-white text-slate-700 border border-slate-300 hover:border-slate-500"
              }`}
            >{w.label}</button>
          ))}
        </div>
      </header>

      {loading && <div className="mt-3 text-sm text-slate-500" data-testid="safety-kpis-loading">Loading company safety rollup…</div>}
      {err && (
        <div className="mt-3 flex items-center justify-between gap-3 text-sm text-rose-700" data-testid="safety-kpis-error">
          <span>{err}</span>
          <button
            type="button"
            onClick={() => setRetrySeq((v) => v + 1)}
            className="text-[11px] font-mono uppercase tracking-widest font-bold text-rose-700 hover:text-rose-900"
            data-testid="safety-kpis-retry"
          >
            Retry
          </button>
        </div>
      )}
      {!loading && !err && snap && (
        <>
          <div
            className={`mt-4 rounded-md border-2 ${BAND_STYLES[snap.status_band] || BAND_STYLES.amber} px-4 py-3`}
            data-testid="safety-kpis-band"
          >
            <div className="flex items-baseline gap-3 flex-wrap">
              <span className="inline-flex items-center gap-1.5 font-mono text-xs uppercase tracking-widest">
                <span>Company band</span>
                <InlineKpiHelp metadata={snap.kpi_metadata?.status_band} fallbackLabel="Company Safety Band" testId="safety-kpis-band-help" />
              </span>
              <span className="font-display text-2xl font-black uppercase" data-testid="safety-kpis-band-value">{snap.status_band}</span>
              <span className="text-xs">
                {snap.active_project_count} active projects · {snap.projects_with_safety_signal} with safety signal
              </span>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3">
            <Totals label="Safety events" value={snap.totals.safety_event_count} sub={`${snap.totals.daily_report_safety_events} DR · ${snap.totals.incident_count} incidents`} testid="safety-kpi-total-events" metadata={snap.kpi_metadata?.totals?.safety_event_count} />
            <Totals label="Injuries / Accidents" value={`${snap.totals.injuries_reported} / ${snap.totals.accident_count}`} sub={`${snap.totals.utility_strike_count} utility strike${snap.totals.utility_strike_count === 1 ? "" : "s"}`} testid="safety-kpi-total-injuries" metadata={snap.kpi_metadata?.cards?.injuries_accidents} />
            <Totals label="Near-miss" value={snap.totals.near_miss_count} sub={`${snap.totals.open_incidents} incident${snap.totals.open_incidents === 1 ? "" : "s"} open`} testid="safety-kpi-total-nearmiss" metadata={snap.kpi_metadata?.cards?.near_miss_open_incidents} />
            <Totals label="Meetings / JHAs / Inspections" value={`${snap.totals.safety_meetings_count} / ${snap.totals.jha_count} / ${snap.totals.safety_inspection_count}`} sub={`${snap.totals.trench_inspection_count} trench · ${snap.totals.safety_photo_count} photos`} testid="safety-kpi-total-inspections" metadata={snap.kpi_metadata?.cards?.meetings_jhas_inspections} />
          </div>

          {snap.totals.escalation_gap_count > 0 && (
            <div
              className="mt-3 rounded border border-rose-200 bg-rose-50 text-rose-800 px-3 py-2 text-xs"
              data-testid="safety-kpi-escalation-gap"
            >
              <b>{snap.totals.escalation_gap_count} escalation gap{snap.totals.escalation_gap_count === 1 ? "" : "s"}</b> — safety events without safety-contact confirmation.
            </div>
          )}

          <ProjectRanking
            projects={snap.top_projects}
            onSelect={setSelectedPn}
            selectedPn={selectedPn}
          />

          <SourceStatusStrip summary={snap.source_status_summary} activeCount={snap.active_project_count} />
        </>
      )}

      {selectedPn && (
        <ProjectDrilldown
          projectNumber={selectedPn}
          window={window}
          onClose={() => setSelectedPn(null)}
        />
      )}
    </section>
  );
}

function Totals({ label, value, sub, testid, metadata }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white px-3 py-2" data-testid={testid}>
      <div className="inline-flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-widest text-slate-500">
        <span>{label}</span>
        <InlineKpiHelp metadata={metadata} fallbackLabel={label} testId={`${testid}-help`} />
      </div>
      <div className="mt-1 font-display text-2xl font-black text-slate-900">{value}</div>
      {sub && <p className="text-[11px] text-slate-500 mt-0.5">{sub}</p>}
    </div>
  );
}

function ProjectRanking({ projects, onSelect, selectedPn }) {
  if (!projects || projects.length === 0) {
    return (
      <div className="mt-4 text-sm text-slate-500 italic" data-testid="safety-kpis-empty">
        No active projects with recorded safety data in this window.
      </div>
    );
  }
  return (
    <div className="mt-4 rounded-md border border-slate-200 overflow-hidden" data-testid="safety-kpis-project-ranking">
      <div className="bg-slate-50 border-b border-slate-200 px-3 py-2 flex items-center gap-2">
        <span className="font-mono text-[10px] uppercase tracking-widest text-slate-600">Projects · sorted by attention</span>
        <span className="text-[10px] text-slate-500 ml-auto">{projects.length} listed</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-white text-slate-500">
            <tr>
              <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-widest">Project</th>
              <th className="text-right px-3 py-2 font-mono text-[10px] uppercase tracking-widest">Events</th>
              <th className="text-right px-3 py-2 font-mono text-[10px] uppercase tracking-widest">Near-miss</th>
              <th className="text-right px-3 py-2 font-mono text-[10px] uppercase tracking-widest">Gaps</th>
              <th className="text-right px-3 py-2 font-mono text-[10px] uppercase tracking-widest">Meetings</th>
              <th className="text-right px-3 py-2 font-mono text-[10px] uppercase tracking-widest">JHAs</th>
              <th className="text-right px-3 py-2 font-mono text-[10px] uppercase tracking-widest">Insp.</th>
              <th className="text-right px-3 py-2 font-mono text-[10px] uppercase tracking-widest">Attention</th>
              <th className="text-right px-3 py-2 font-mono text-[10px] uppercase tracking-widest"> </th>
            </tr>
          </thead>
          <tbody>
            {projects.slice(0, 40).map((r) => (
              <tr
                key={r.project_number}
                data-testid={`safety-kpis-row-${r.project_number}`}
                className={`border-t border-slate-100 hover:bg-slate-50 ${selectedPn === r.project_number ? "bg-amber-50" : ""}`}
              >
                <td className="px-3 py-2">
                  <div className="font-medium text-slate-900">{r.project_number}</div>
                  {r.project_name && <div className="text-[11px] text-slate-500">{r.project_name}</div>}
                </td>
                <td className="px-3 py-2 text-right font-mono">{r.safety_event_count}</td>
                <td className="px-3 py-2 text-right font-mono">{r.near_miss_count}</td>
                <td className="px-3 py-2 text-right font-mono">
                  {r.escalation_gap_count > 0 ? (
                    <span className="inline-block rounded-full bg-rose-100 text-rose-800 px-1.5 py-0 text-[10px] font-bold">{r.escalation_gap_count}</span>
                  ) : (
                    <span className="text-slate-400">—</span>
                  )}
                </td>
                <td className="px-3 py-2 text-right font-mono">{r.safety_meetings_count}</td>
                <td className="px-3 py-2 text-right font-mono">{r.jha_count}</td>
                <td className="px-3 py-2 text-right font-mono">{r.safety_inspection_count}</td>
                <td className="px-3 py-2 text-right font-mono font-bold">{r.attention_score}</td>
                <td className="px-3 py-2 text-right">
                  <button
                    type="button"
                    onClick={() => onSelect(r.project_number)}
                    data-testid={`safety-kpis-open-${r.project_number}`}
                    className="inline-flex items-center gap-1 text-xs text-blue-700 hover:underline"
                  >
                    View <ChevronRight className="w-3 h-3" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SourceStatusStrip({ summary, activeCount }) {
  const LABEL = {
    daily_report_safety_events: "Daily Report events",
    incidents: "Incidents",
    safety_meetings: "Meetings",
    jha_records: "JHAs",
    safety_inspections: "Inspections",
    trench_excavations: "Trench excavations",
    equipment_dvir: "Equipment DVIR",
    trench_holds: "Trench holds",
    near_miss_reports: "Near-miss reports",
  };
  const STATUS_COLOR = {
    LIVE: "bg-emerald-100 text-emerald-800",
    PARTIAL: "bg-amber-100 text-amber-800",
    "MISSING · FUTURE": "bg-slate-100 text-slate-500",
  };
  return (
    <div className="mt-4 rounded-md border border-dashed border-slate-300 bg-slate-50/60 p-3" data-testid="safety-kpis-source-status">
      <div className="font-mono text-[10px] uppercase tracking-widest text-slate-600">Safety Sources · Company Coverage</div>
      <div className="mt-2 space-y-1">
        {Object.entries(summary || {}).map(([k, buckets]) => (
          <div key={k} className="flex items-center gap-2 text-[11px]" data-testid={`safety-source-${k}`}>
            <span className="w-40 truncate text-slate-700">{LABEL[k] || k}</span>
            {Object.entries(buckets).map(([status, n]) => (
              <span
                key={status}
                className={`inline-flex items-center gap-1 text-[10px] font-mono uppercase tracking-widest px-1.5 py-0.5 rounded ${STATUS_COLOR[status] || STATUS_COLOR.PARTIAL}`}
              >
                {status} · {n}/{activeCount}
              </span>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

function ProjectDrilldown({ projectNumber, window, onClose }) {
  const [data, setData] = React.useState(null);
  const [err, setErr] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [retrySeq, setRetrySeq] = React.useState(0);

  React.useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setErr(null);
    api.get(`/safety/projects/${encodeURIComponent(projectNumber)}/safety-kpis?window=${window}`, {
      signal: controller.signal,
      timeout: SAFETY_KPI_TIMEOUT_MS,
    })
      .then((r) => { if (!controller.signal.aborted) setData(r.data); })
      .catch((e) => {
        if (!controller.signal.aborted) setErr(describeSafetyKpiError(e, `Project safety drilldown for ${projectNumber}`));
      })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [projectNumber, retrySeq, window]);

  return (
    <div
      className="fixed inset-0 z-40 bg-black/40 flex items-stretch justify-end"
      onClick={onClose}
      data-testid="safety-kpis-drilldown-backdrop"
    >
      <div
        role="dialog"
        aria-label={`Safety KPIs · ${projectNumber}`}
        className="w-full max-w-2xl bg-white h-full overflow-y-auto shadow-2xl"
        onClick={(e) => e.stopPropagation()}
        data-testid="safety-kpis-drilldown"
      >
        <div className="sticky top-0 bg-white border-b border-slate-200 px-5 py-4 flex items-center gap-3">
          <div className="min-w-0 flex-1">
            <h4 className="inline-flex items-center gap-1.5 font-display text-lg font-black">
              <span>{projectNumber}</span>
              <InlineKpiHelp metadata={data?.kpi_metadata?.page} fallbackLabel={`Project Safety KPIs ${projectNumber}`} testId="safety-kpis-drilldown-title-help" />
            </h4>
            <p className="text-xs text-slate-500 mt-0.5">
              Safety subset of the shared operational spine.
            </p>
          </div>
          <button
            type="button"
            className="rounded-md p-1.5 hover:bg-slate-100"
            onClick={onClose}
            aria-label="Close"
            data-testid="safety-kpis-drilldown-close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="p-5 space-y-4">
          {loading && <div className="text-sm text-slate-500">Loading project safety…</div>}
          {err && (
            <div className="flex items-center justify-between gap-3 text-sm text-rose-700" data-testid="safety-kpis-drilldown-error">
              <span>{err}</span>
              <button
                type="button"
                onClick={() => setRetrySeq((v) => v + 1)}
                className="text-[11px] font-mono uppercase tracking-widest font-bold text-rose-700 hover:text-rose-900"
                data-testid="safety-kpis-drilldown-retry"
              >
                Retry
              </button>
            </div>
          )}
          {!loading && !err && data && (
            <>
              <div className="text-xs text-slate-500">
                {data.date_from ? `${data.date_from} → ${data.date_to}` : `Project to date · ends ${data.date_to}`}
              </div>
              <div className="grid grid-cols-2 gap-3">
                <Totals label="Safety events" value={data.safety.safety_event_count} sub={`${data.safety.daily_report_safety_events} DR · ${data.safety.incident_count} incidents`} testid="safety-drilldown-events" metadata={data.kpi_metadata?.cards?.safety_event_count} />
                <Totals label="Near-miss / Injuries" value={`${data.safety.near_miss_count} / ${data.safety.injuries_reported}`} sub={`${data.safety.utility_strike_count} utility · ${data.safety.escalation_gap_count} gap${data.safety.escalation_gap_count === 1 ? "" : "s"}`} testid="safety-drilldown-nearmiss" metadata={data.kpi_metadata?.cards?.near_miss_and_injuries} />
                <Totals label="Meetings / JHAs" value={`${data.safety.safety_meetings_count} / ${data.safety.jha_count}`} sub={`${data.safety.safety_inspection_count} inspections`} testid="safety-drilldown-meetings" metadata={data.kpi_metadata?.cards?.meetings_and_jhas} />
                <Totals label="Trench / Photos" value={`${data.safety.trench_inspection_count} / ${data.safety.safety_photo_count}`} sub="" testid="safety-drilldown-trench" metadata={data.kpi_metadata?.cards?.trench_and_photos} />
              </div>
              <div className="rounded-md border border-dashed border-slate-300 bg-slate-50/60 p-3">
                <div className="inline-flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-widest text-slate-600">Sources · this project <InlineKpiHelp metadata={data.kpi_metadata?.sections?.safety_sources} fallbackLabel="Project Safety Sources" testId="safety-kpis-drilldown-sources-help" /></div>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {Object.entries(data.safety_sources || {}).map(([k, v]) => (
                    <span
                      key={k}
                      title={v.note || v.source}
                      className={`inline-flex items-center gap-1 text-[10px] font-mono uppercase tracking-widest px-2 py-0.5 rounded border ${
                        v.status === "LIVE"
                          ? "bg-emerald-50 border-emerald-200 text-emerald-800"
                          : v.status === "PARTIAL"
                            ? "bg-amber-50 border-amber-200 text-amber-800"
                            : "bg-slate-100 border-slate-200 text-slate-500"
                      }`}
                    >
                      {k}
                      <span className="opacity-70">· {v.status}</span>
                      {typeof v.count === "number" && <span className="opacity-80">({v.count})</span>}
                    </span>
                  ))}
                </div>
              </div>
              <div className="text-xs text-slate-500">
                Activity context · {data.activity_context.total_man_hours} man-hours · {data.activity_context.unique_employee_count} unique employees · {data.activity_context.delay_hours_impact} delay hrs.
                <span className="ml-1 inline-flex align-middle"><InlineKpiHelp metadata={data.kpi_metadata?.sections?.activity_context} fallbackLabel="Project Safety Activity Context" testId="safety-kpis-drilldown-activity-help" /></span>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
