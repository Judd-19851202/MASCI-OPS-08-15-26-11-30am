// TRACK 23.7 · PM Operational KPIs — production-intelligence card.
//
// Renders 8 KPI groups per project (Labor · Equipment · Materials ·
// Production · Delays · Safety · Intelligence · Scheduling
// Readiness) from the shared aggregator spine.
//
// ABSOLUTE RULE: NO cost, NO dollars, NO rates, NO budget labels
// anywhere in this component. Operational production intelligence
// only.
//
// Backend: GET /api/pm/projects/{project_number}/operational-kpis
// Auth: PM portal (existing session).
// Consumer: PmProjectDetail.
import React from "react";
import {
  Users, Wrench, Truck, Package, Clock, ShieldAlert, Sparkles, Calendar,
} from "lucide-react";
import { sanitizeOperatorCopy } from "@/lib/operatorLanguage";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const WINDOWS = [
  { key: "7d", label: "Last 7 days" },
  { key: "30d", label: "Last 30 days" },
  { key: "mtd", label: "Month to date" },
  { key: "ptd", label: "Project to date" },
];

export default function PmOperationalKPIs({ projectNumber }) {
  const [window, setWindow] = React.useState("7d");
  const [data, setData] = React.useState(null);
  const [err, setErr] = React.useState(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    if (!projectNumber) return;
    let cancelled = false;
    setLoading(true); setErr(null);
    fetch(`${API}/pm/projects/${encodeURIComponent(projectNumber)}/operational-kpis?window=${window}`, {
      credentials: "include",
    })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((d) => { if (!cancelled) setData(d); })
      .catch((e) => { if (!cancelled) setErr(e.message || String(e)); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [projectNumber, window]);

  if (!projectNumber) return null;

  return (
    <section
      className="mt-4 bg-white border border-slate-200 rounded-md p-4 sm:p-6"
      data-testid="pm-operational-kpis"
    >
      <header className="flex flex-wrap items-baseline gap-3">
        <h2 className="font-display text-lg font-black text-slate-900" data-testid="pm-operational-kpis-title">
          Project Performance
        </h2>
        <span className="text-xs text-slate-500">Labor · Equipment · Materials · Production · Delays · Safety · Photo findings — budget details stay on the budget page.</span>
        <div className="ml-auto flex flex-wrap gap-1" role="tablist" aria-label="Window">
          {WINDOWS.map((w) => (
            <button
              key={w.key}
              type="button"
              onClick={() => setWindow(w.key)}
              data-testid={`pm-operational-kpis-window-${w.key}`}
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

      {loading && <div className="mt-3 text-sm text-slate-500" data-testid="pm-operational-kpis-loading">Loading project totals…</div>}
      {err && <div className="mt-3 text-sm text-rose-700" data-testid="pm-operational-kpis-error">Unable to load project measures ({err})</div>}
      {!loading && !err && data && (
        <>
          <p className="mt-2 text-[11px] font-mono uppercase tracking-widest text-slate-500" data-testid="pm-operational-kpis-range">
            {data.date_from ? `${data.date_from} → ${data.date_to}` : `Project to date · ends ${data.date_to}`}
          </p>

          {/* Row 1 · headline metrics */}
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <KpiCard
              title="Man-hours"
              icon={Users}
              testid="pm-kpi-labor"
              value={data.labor.total_man_hours}
              unit="hrs"
              subs={[
                `${data.labor.unique_employee_count} unique employees`,
                `${data.labor.verified_employee_count} HR-verified`,
              ]}
              empty={data.labor.total_man_hours === 0}
              emptyText="No labor logged in this window."
              distribution={data.labor.by_trade.slice(0, 4)}
              distributionKey="key"
              distributionValueKey="hours"
              distributionUnit="hrs"
            />
            <KpiCard
              title="Equipment Run / Idle"
              icon={Wrench}
              testid="pm-kpi-equipment"
              value={`${data.equipment.total_run_hours} / ${data.equipment.total_idle_hours}`}
              unit="hrs"
              subs={[
                `Utilization ${data.equipment.utilization_percent}%`,
                `${data.equipment.equipment_count} units · ${data.equipment.issue_count} issue${data.equipment.issue_count === 1 ? "" : "s"}`,
              ]}
              empty={data.equipment.equipment_count === 0}
              emptyText="No equipment activity logged."
              distribution={data.equipment.by_equipment.slice(0, 4)}
              distributionKey="equipment"
              distributionValueKey="run"
              distributionUnit="run hrs"
            />
            <KpiCard
              title="Materials In / Out"
              icon={Truck}
              testid="pm-kpi-materials"
              value={`${data.materials.inbound_by_material_unit.length} / ${data.materials.outbound_by_material_unit.length}`}
              unit="kinds"
              subs={[
                `${data.materials.load_count} load${data.materials.load_count === 1 ? "" : "s"}`,
                `${data.materials.carriers.length} carrier${data.materials.carriers.length === 1 ? "" : "s"}`,
              ]}
              empty={data.materials.load_count === 0}
              emptyText="No material tickets in this window."
              distribution={data.materials.inbound_by_material_unit.slice(0, 4)}
              distributionKey="material"
              distributionValueKey="quantity"
              distributionUnitAlias="unit"
            />
            <KpiCard
              title="Delay Impact"
              icon={Clock}
              testid="pm-kpi-delays"
              value={data.delays.total_hours_impact}
              unit="hrs"
              subs={[
                `${data.delays.delay_count} event${data.delays.delay_count === 1 ? "" : "s"}`,
                data.delays.unresolved_follow_ups > 0
                  ? `${data.delays.unresolved_follow_ups} needing follow-up`
                  : "No open follow-ups",
              ]}
              empty={data.delays.delay_count === 0}
              emptyText="No delays logged."
              distribution={data.delays.by_category.slice(0, 4)}
              distributionKey="category"
              distributionValueKey="hours"
              distributionUnit="hrs"
            />
          </div>

          {/* Row 2 · production + safety + photo + summary */}
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <KpiCard
              title="Production"
              icon={Package}
              testid="pm-kpi-production"
              value={data.production.row_count}
              unit="entries"
              subs={[
                `${data.production.by_activity_unit.length} activit${data.production.by_activity_unit.length === 1 ? "y" : "ies"}`,
                `${data.production.station_coverage.length} stationed`,
              ]}
              empty={data.production.row_count === 0}
              emptyText="No production quantities logged."
              distribution={data.production.by_activity_unit.slice(0, 4)}
              distributionKey="activity"
              distributionValueKey="quantity"
              distributionUnitAlias="unit"
            />
            <KpiCard
              title="Safety"
              icon={ShieldAlert}
              testid="pm-kpi-safety"
              value={data.safety.safety_event_count}
              unit="events"
              subs={[
                `${data.safety.incident_count} incident${data.safety.incident_count === 1 ? "" : "s"} · ${data.safety.near_miss_count} near-miss${data.safety.near_miss_count === 1 ? "" : "es"}`,
                `${data.safety.safety_meetings_count} meetings · ${data.safety.jha_count} JHAs · ${data.safety.safety_inspection_count} inspections`,
              ]}
              empty={data.safety.safety_event_count === 0 && data.safety.safety_meetings_count === 0 && data.safety.jha_count === 0}
              emptyText="No safety activity in this window."
              distribution={data.safety.by_daily_safety_type.slice(0, 4)}
              distributionKey="type"
              distributionValueKey="count"
              distributionUnit=""
              flagCritical={data.safety.escalation_gap_count > 0 ? `${data.safety.escalation_gap_count} escalation gap` : null}
            />
            <KpiCard
              title="Photo Findings"
              icon={Sparkles}
              testid="pm-kpi-photos"
              value={data.intelligence.photo_observation_count}
              unit="photos"
              subs={[
                `${data.intelligence.top_photo_tags.length} tag categor${data.intelligence.top_photo_tags.length === 1 ? "y" : "ies"}`,
              ]}
              empty={data.intelligence.photo_observation_count === 0}
              emptyText="No photo evidence in this window."
              distribution={data.intelligence.top_photo_tags.slice(0, 4)}
              distributionKey="tag"
              distributionValueKey="count"
              distributionUnit=""
            />
            <LatestSummaryCard latest={data.intelligence.latest_summary} count={data.intelligence.accepted_summaries_count} />
          </div>

          {/* Scheduling Readiness — future-facing manifest */}
          <SchedulingReadinessStrip readiness={data.scheduling_readiness} />

          {/* Safety Sources classification — honest surface */}
          <SafetySourcesStrip sources={data.safety_sources} />
        </>
      )}
    </section>
  );
}

function KpiCard({
  title, icon: Icon, testid, value, unit, subs = [], empty, emptyText,
  distribution = [], distributionKey, distributionValueKey,
  distributionUnit = "", distributionUnitAlias, flagCritical,
}) {
  return (
    <div
      className={`rounded-md border ${empty ? "border-slate-200 bg-slate-50/60" : "border-slate-200 bg-white"} p-3`}
      data-testid={testid}
    >
      <div className="flex items-center gap-2">
        <Icon className="w-4 h-4 text-slate-500" aria-hidden />
        <span className="font-mono text-[10px] uppercase tracking-widest text-slate-600">{title}</span>
        {flagCritical && (
          <span className="ml-auto text-[9px] font-bold uppercase tracking-widest text-rose-700 bg-rose-50 border border-rose-200 rounded px-1.5 py-0.5" data-testid={`${testid}-flag`}>
            {flagCritical}
          </span>
        )}
      </div>
      <div className="mt-1 flex items-baseline gap-1.5" data-testid={`${testid}-value`}>
        <span className="font-display text-2xl font-black text-slate-900">{value}</span>
        {unit && <span className="text-xs text-slate-500">{unit}</span>}
      </div>
      {empty ? (
        <p className="mt-1 text-[11px] text-slate-400">{emptyText}</p>
      ) : (
        <>
          {subs.map((s, i) => (
            <p key={i} className="text-[11px] text-slate-600 mt-0.5">{s}</p>
          ))}
          {distribution.length > 0 && (
            <ul className="mt-2 space-y-0.5" data-testid={`${testid}-distribution`}>
              {distribution.map((row, idx) => {
                const key = String(row[distributionKey] ?? "").slice(0, 24);
                const val = row[distributionValueKey];
                const unitLabel = distributionUnitAlias ? row[distributionUnitAlias] : distributionUnit;
                return (
                  <li key={idx} className="flex items-baseline gap-2 text-[11px]">
                    <span className="truncate text-slate-600 flex-1" title={row[distributionKey]}>{key}</span>
                    <span className="font-mono font-bold text-slate-900">{val}</span>
                    {unitLabel && <span className="text-slate-400 text-[10px]">{unitLabel}</span>}
                  </li>
                );
              })}
            </ul>
          )}
        </>
      )}
    </div>
  );
}

function LatestSummaryCard({ latest, count }) {
  const empty = !latest;
  return (
    <div
      className={`rounded-md border ${empty ? "border-slate-200 bg-slate-50/60" : "border-slate-200 bg-white"} p-3`}
      data-testid="pm-kpi-latest-summary"
    >
      <div className="flex items-center gap-2">
        <Sparkles className="w-4 h-4 text-slate-500" aria-hidden />
        <span className="font-mono text-[10px] uppercase tracking-widest text-slate-600">Latest Approved Shift Story</span>
      </div>
      <div className="mt-1 flex items-baseline gap-1.5">
        <span className="font-display text-2xl font-black text-slate-900">{count}</span>
        <span className="text-xs text-slate-500">approved</span>
      </div>
      {empty ? (
        <p className="mt-1 text-[11px] text-slate-400">No approved shift story in this window.</p>
      ) : (
        <div className="mt-1 text-[11px] text-slate-600">
          <div>{latest.date} · {latest.audience || "project team"}</div>
          <div className="text-slate-400 text-[10px]">Supervisor-ready daily summary</div>
        </div>
      )}
    </div>
  );
}

function SchedulingReadinessStrip({ readiness }) {
  const rows = [
    ["Labor signal",        readiness.labor_signal_available],
    ["Equipment signal",    readiness.equipment_signal_available],
    ["Material signal",     readiness.material_signal_available],
    ["Production signal",   readiness.production_signal_available],
    ["Delay signal",        readiness.delay_signal_available],
    ["Safety signal",       readiness.safety_signal_available],
    ["Weather signal",      readiness.weather_signal_available],
    ["Readiness signal",    readiness.readiness_signal_available],
    ["Tomorrow-plan",       readiness.tomorrow_plan_available],
  ];
  return (
    <div className="mt-5 rounded-md border border-dashed border-slate-300 bg-slate-50/60 p-3" data-testid="pm-kpi-scheduling-readiness">
      <div className="flex items-center gap-2">
        <Calendar className="w-4 h-4 text-slate-500" aria-hidden />
        <span className="font-mono text-[10px] uppercase tracking-widest text-slate-600">Planning Readiness · next-week planning</span>
      </div>
      <p className="mt-1 text-[11px] text-slate-500">{sanitizeOperatorCopy(readiness.notes, "Planning follow-up may still be needed.")}</p>
      <div className="mt-2 flex flex-wrap gap-1.5">
        {rows.map(([label, ok]) => (
          <span
            key={label}
            className={`inline-flex items-center gap-1 text-[10px] font-mono uppercase tracking-widest px-2 py-0.5 rounded ${
              ok
                ? "bg-emerald-50 border border-emerald-200 text-emerald-800"
                : "bg-slate-100 border border-slate-200 text-slate-500"
            }`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${ok ? "bg-emerald-500" : "bg-slate-300"}`} />
            {label}{ok ? " · ready" : " · needs follow-up"}
          </span>
        ))}
      </div>
    </div>
  );
}

function SafetySourcesStrip({ sources }) {
  const STATUS_STYLES = {
    LIVE:               "bg-emerald-50 border-emerald-200 text-emerald-800",
    PARTIAL:            "bg-amber-50 border-amber-200 text-amber-800",
    "MISSING · FUTURE": "bg-slate-100 border-slate-200 text-slate-500",
  };
  const LABELS = {
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
  return (
    <div className="mt-3 rounded-md border border-dashed border-slate-300 bg-slate-50/60 p-3" data-testid="pm-kpi-safety-sources">
      <div className="flex items-center gap-2">
        <ShieldAlert className="w-4 h-4 text-slate-500" aria-hidden />
        <span className="font-mono text-[10px] uppercase tracking-widest text-slate-600">Safety Sources · classification</span>
      </div>
      <div className="mt-2 flex flex-wrap gap-1.5">
        {Object.entries(sources).map(([k, v]) => (
          <span
            key={k}
            title={v.note || v.source}
            className={`inline-flex items-center gap-1 text-[10px] font-mono uppercase tracking-widest px-2 py-0.5 rounded border ${STATUS_STYLES[v.status] || STATUS_STYLES.PARTIAL}`}
            data-testid={`pm-kpi-safety-source-${k}`}
          >
            {LABELS[k] || k}
            <span className="opacity-70">· {v.status}</span>
            {typeof v.count === "number" && <span className="opacity-80">({v.count})</span>}
          </span>
        ))}
      </div>
    </div>
  );
}
