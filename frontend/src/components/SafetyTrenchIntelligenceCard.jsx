// TRACK 23.10-D · Safety Portal — Trench & Excavation Intelligence card.
//
// Consumer only. Reads the shared trench facts (Track 23.10-C) + the
// Qualifications Engine registry (Track 23.10-B) through the safety
// portal aggregator wrapper.  Zero new KPI logic.
//
// ABSOLUTE RULES:
//   * NO cost / NO money.
//   * NO fake LIVE. Source classification comes from the backend.
//   * NO auto-fix of missing / ambiguous linkage — read-only cleanup.
//   * Safety / Admin only.
//
// Backend:
//   GET /api/safety/company/trench-safety-kpis?window=30d
//   GET /api/safety/company/trench-safety-cleanup?limit=100
//   GET /api/safety/projects/{project_number}/trench-safety-kpis
import React from "react";
import { Link } from "react-router-dom";
import {
  ShieldAlert, Layers, HardHat, Wrench, ClipboardCheck,
  AlertTriangle, ChevronRight, X, ShieldCheck, Link2Off,
  GraduationCap, RefreshCw,
} from "lucide-react";
import { getSafetyToken } from "@/lib/safetyAuth";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const TRENCH_INTEL_TIMEOUT_MS = 5_000;

function fetchJsonWithTimeout(url, options = {}, timeoutMs = TRENCH_INTEL_TIMEOUT_MS) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  return fetch(url, { ...options, signal: controller.signal })
    .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
    .finally(() => clearTimeout(timer));
}

function trenchErrorMessage(error, fallback) {
  if (error?.name === "AbortError") {
    return `${fallback} timed out. Safety records, incidents, and trench workflows remain available.`;
  }
  return String(error || fallback);
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

const SOURCE_CHIP = {
  LIVE:    "bg-emerald-100 border-emerald-300 text-emerald-900",
  PARTIAL: "bg-amber-100 border-amber-300 text-amber-900",
  MISSING: "bg-slate-100 border-slate-300 text-slate-700",
};

function authHeaders() {
  const h = {};
  const s = typeof getSafetyToken === "function" ? getSafetyToken() : null;
  if (s) h["X-Safety-Token"] = s;
  if (typeof window !== "undefined" && window.localStorage) {
    const admin = window.localStorage.getItem("masci.admin.token");
    if (admin) h["X-Admin-Token"] = admin;
  }
  return h;
}

function chip(cls, label, testid) {
  return (
    <span
      data-testid={testid}
      className={`inline-block px-2 py-0.5 rounded border text-[10px] font-mono uppercase tracking-[0.15em] font-bold ${cls}`}
    >
      {label}
    </span>
  );
}

function MetricCard({ label, value, sub, testid, icon: Icon, tone = "slate" }) {
  const toneCls = {
    slate: "border-slate-200 bg-white",
    amber: "border-amber-200 bg-amber-50",
    rose:  "border-rose-200 bg-rose-50",
    emerald: "border-emerald-200 bg-emerald-50",
  }[tone] || "border-slate-200 bg-white";
  return (
    <div
      data-testid={testid}
      className={`p-3 rounded border-2 ${toneCls}`}
    >
      <div className="flex items-center gap-2 mb-1">
        {Icon ? <Icon className="w-3.5 h-3.5 text-slate-500" /> : null}
        <div className="text-[10px] font-mono uppercase tracking-[0.15em] text-slate-600 font-bold">
          {label}
        </div>
      </div>
      <div className="text-2xl font-bold tabular-nums" data-testid={`${testid}-value`}>
        {value}
      </div>
      {sub ? (
        <div className="text-[11px] text-slate-500 mt-0.5">{sub}</div>
      ) : null}
    </div>
  );
}

function bandForCompany(snap) {
  if (!snap) return "green";
  const t = snap.trench || {};
  if (t.open_holds > 0) return "amber";
  if (snap.certifications?.expired > 0 || snap.certifications?.revoked > 0) return "amber";
  return "green";
}

function bandForProject(row) {
  if (!row) return "green";
  if (row.open_holds > 0) return "amber";
  if (row.unresolved_utility_conflict_count > 0) return "red";
  return "green";
}

function ProjectDrilldown({ pn, onClose }) {
  const [row, setRow] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [err, setErr] = React.useState(null);
  const [retrySeq, setRetrySeq] = React.useState(0);

  React.useEffect(() => {
    let cancelled = false;
    setLoading(true); setErr(null);
    fetchJsonWithTimeout(`${API}/safety/projects/${encodeURIComponent(pn)}/trench-safety-kpis`, {
      headers: authHeaders(),
    })
      .then((d) => { if (!cancelled) { setRow(d); setLoading(false); } })
      .catch((e) => { if (!cancelled) { setErr(trenchErrorMessage(e, `Project trench intelligence for ${pn}`)); setLoading(false); } });
    return () => { cancelled = true; };
  }, [pn, retrySeq]);

  const band = bandForProject(row);

  return (
    <div
      className="border-2 border-slate-300 rounded p-4 bg-white mt-4"
      data-testid="safety-trench-drilldown"
    >
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] font-bold text-slate-600">
            Project drilldown
          </div>
          <div className="text-lg font-bold" data-testid="safety-trench-drilldown-pn">
            {pn}
          </div>
        </div>
        <button
          type="button"
          onClick={onClose}
          data-testid="safety-trench-drilldown-close"
          className="text-slate-500 hover:text-slate-900"
        >
          <X className="w-5 h-5" />
        </button>
      </div>
      {loading ? (
        <div className="p-6 text-center text-slate-400">Loading…</div>
      ) : err ? (
        <div className="p-6 text-center text-rose-600 text-sm" data-testid="safety-trench-drilldown-error">
          <div>{err === "403" ? "Not authorised" : `Error: ${err}`}</div>
          <button
            type="button"
            onClick={() => setRetrySeq((v) => v + 1)}
            className="mt-3 text-[11px] font-mono uppercase tracking-widest font-bold text-rose-700 hover:text-rose-900"
            data-testid="safety-trench-drilldown-retry"
          >
            Retry
          </button>
        </div>
      ) : !row ? null : (
        <>
          <div className={`p-3 rounded border-2 mb-3 ${BAND_STYLES[band]}`}
               data-testid="safety-trench-drilldown-band">
            <div className="text-xs font-mono uppercase tracking-[0.15em] font-bold">
              Trench posture · {band.toUpperCase()}
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mb-3">
            <MetricCard testid="drilldown-exc-days" label="Excavation days" value={row.excavation_days} icon={Layers} />
            <MetricCard testid="drilldown-insps"    label="Inspections"     value={row.inspections}    icon={ClipboardCheck} />
            <MetricCard testid="drilldown-open-holds" label="Open holds"    value={row.open_holds}     icon={AlertTriangle}
                        tone={row.open_holds > 0 ? "amber" : "slate"} />
            <MetricCard testid="drilldown-repairs"  label="Repairs"         value={row.repairs}        icon={Wrench} />
            <MetricCard testid="drilldown-safe-verified" label="Safe-to-use verified" value={row.safe_to_use_verified}
                        icon={ShieldCheck} tone={row.safe_to_use_verified > 0 ? "emerald" : "slate"}
                        sub="B-04: verified_at + reinspection_passed" />
            <MetricCard testid="drilldown-cp-assigns" label="CP assignments" value={row.cp_assignments} icon={HardHat} />
          </div>
          <div className="text-xs text-slate-600">
            <div className="mb-1">
              <strong>Source:</strong>{" "}
              {chip(SOURCE_CHIP[row.source_classification?.trench] || SOURCE_CHIP.MISSING,
                    row.source_classification?.trench || "MISSING", "drilldown-source-trench")}
              {" "}
              {chip(SOURCE_CHIP[row.source_classification?.certifications] || SOURCE_CHIP.MISSING,
                    `Certs · ${row.source_classification?.certifications || "MISSING"}`, "drilldown-source-certs")}
            </div>
            <div className="mb-1">
              <strong>Linkage:</strong> {row.linkage_breakdown?.live ?? 0} LIVE · {row.linkage_breakdown?.partial ?? 0} PARTIAL · {row.linkage_breakdown?.ambiguous ?? 0} AMBIGUOUS · {row.linkage_breakdown?.missing ?? 0} MISSING
            </div>
            {row.cp_snapshot ? (
              <div className="mt-2 p-2 rounded border border-slate-200 bg-slate-50 text-slate-800">
                <div className="text-[10px] font-mono uppercase tracking-[0.15em] font-bold text-slate-500 mb-0.5">
                  Latest Competent Person update
                </div>
                {row.cp_snapshot.person_name_snapshot || row.cp_snapshot.employee_id}
                {" · "}
                {row.cp_snapshot.person_trade_snapshot}
                {" · exp "}{row.cp_snapshot.expires_at_at_selection || "n/a"}
                {row.cp_snapshot.cert_valid_at_report
                  ? chip(SOURCE_CHIP.LIVE, "VALID", "drilldown-cp-valid")
                  : chip(SOURCE_CHIP.PARTIAL, "REVIEW", "drilldown-cp-review")}
              </div>
            ) : (
              <div className="mt-2 p-2 rounded border border-slate-200 bg-slate-50 text-slate-500 text-xs">
                No CP assignment on record for this project yet.
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function CleanupTile({ open, setOpen }) {
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(false);

  const load = React.useCallback(() => {
    setLoading(true);
    fetch(`${API}/safety/company/trench-safety-cleanup?limit=25`, {
      headers: authHeaders(),
    })
      .then((r) => r.ok ? r.json() : null)
      .then((d) => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  React.useEffect(() => { load(); }, [load]);

  const totals = data?.totals || { missing: 0, ambiguous: 0, asset_only: 0 };
  const combined = (totals.missing || 0) + (totals.ambiguous || 0) + (totals.asset_only || 0);
  return (
    <div
      className="border-2 border-slate-300 rounded p-4 bg-white"
      data-testid="safety-trench-cleanup-tile"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Link2Off className="w-4 h-4 text-slate-600" />
          <div>
            <div className="text-[10px] font-mono uppercase tracking-[0.2em] font-bold text-slate-600">
              Trench link cleanup
            </div>
            <div className="text-base font-bold tabular-nums" data-testid="safety-trench-cleanup-total">
              {combined}
            </div>
          </div>
        </div>
        <button
          type="button"
          onClick={load}
          className="text-slate-500 hover:text-slate-900"
          data-testid="safety-trench-cleanup-refresh"
          title="Refresh"
        >
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      </div>
      <div className="grid grid-cols-3 gap-2 text-xs mb-3">
        <div className="p-2 rounded border border-slate-200 bg-slate-50">
          <div className="font-mono text-[9px] uppercase tracking-[0.15em] text-slate-600 font-bold">Missing</div>
          <div className="text-lg font-bold tabular-nums" data-testid="cleanup-count-missing">{totals.missing || 0}</div>
        </div>
        <div className="p-2 rounded border border-slate-200 bg-slate-50">
          <div className="font-mono text-[9px] uppercase tracking-[0.15em] text-slate-600 font-bold">Ambiguous</div>
          <div className="text-lg font-bold tabular-nums" data-testid="cleanup-count-ambiguous">{totals.ambiguous || 0}</div>
        </div>
        <div className="p-2 rounded border border-slate-200 bg-slate-50">
          <div className="font-mono text-[9px] uppercase tracking-[0.15em] text-slate-600 font-bold">Asset-only</div>
          <div className="text-lg font-bold tabular-nums" data-testid="cleanup-count-asset-only">{totals.asset_only || 0}</div>
        </div>
      </div>
      <div className="text-[11px] text-slate-500 mb-3">
        Read-only. No auto-fix. These records cannot be confidently tied to a project — Safety/Admin manual audit required.
      </div>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        data-testid="safety-trench-cleanup-toggle"
        className="text-xs font-mono uppercase tracking-[0.15em] font-bold text-purple-700 hover:text-purple-900"
      >
        {open ? "Hide list" : "View cleanup list"}
        <ChevronRight className={`w-3.5 h-3.5 inline ml-1 transition-transform ${open ? "rotate-90" : ""}`} />
      </button>
      {open && (data?.items || []).length > 0 && (
        <div className="mt-3 overflow-x-auto" data-testid="safety-trench-cleanup-list">
          <table className="w-full text-xs min-w-[720px]">
            <thead className="bg-slate-100 text-slate-700 text-[10px] uppercase tracking-[0.15em] font-mono">
              <tr>
                <th className="text-left px-2 py-1">Type</th>
                <th className="text-left px-2 py-1">Asset</th>
                <th className="text-left px-2 py-1">Date</th>
                <th className="text-left px-2 py-1">Status</th>
                <th className="text-left px-2 py-1">Confidence</th>
                <th className="text-left px-2 py-1">Reason</th>
              </tr>
            </thead>
            <tbody>
              {(data.items || []).map((it) => (
                <tr key={it.fact_id} className="border-t border-slate-100"
                    data-testid={`safety-trench-cleanup-row-${it.fact_id}`}>
                  <td className="px-2 py-1 font-mono">{it.record_type}</td>
                  <td className="px-2 py-1 font-mono">{it.asset_id || "—"}</td>
                  <td className="px-2 py-1 font-mono">{it.date || "—"}</td>
                  <td className="px-2 py-1">{it.current_status || "—"}</td>
                  <td className="px-2 py-1">{it.confidence}</td>
                  <td className="px-2 py-1 text-slate-600">{it.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {open && (data?.items || []).length === 0 && !loading && (
        <div className="mt-3 text-xs text-slate-500 italic">
          Nothing to clean up. All trench facts have confident linkage.
        </div>
      )}
    </div>
  );
}

function CompetentPersonBlock({ certs }) {
  if (!certs) return null;
  return (
    <div
      className="border-2 border-slate-300 rounded p-4 bg-white"
      data-testid="safety-trench-cp-block"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <GraduationCap className="w-4 h-4 text-slate-600" />
          <div className="text-[10px] font-mono uppercase tracking-[0.2em] font-bold text-slate-600">
            Competent Persons · Certification block
          </div>
        </div>
        <Link
          to="/hr/qualifications"
          className="text-[11px] font-mono uppercase tracking-[0.15em] font-bold text-purple-700 hover:text-purple-900"
          data-testid="safety-trench-cp-manage-link"
        >
          Manage
          <ChevronRight className="w-3 h-3 inline ml-0.5" />
        </Link>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        <MetricCard testid="cp-active" label="Active" value={certs.active_competent_persons} tone="emerald" icon={ShieldCheck} />
        <MetricCard testid="cp-expiring" label="Expiring ≤ 30d" value={certs.expiring_soon} tone={certs.expiring_soon > 0 ? "amber" : "slate"} />
        <MetricCard testid="cp-expired" label="Expired" value={certs.expired} tone={certs.expired > 0 ? "amber" : "slate"} />
        <MetricCard testid="cp-suspended-revoked" label="Suspended / revoked"
                    value={(certs.suspended || 0) + (certs.revoked || 0)}
                    tone={((certs.suspended || 0) + (certs.revoked || 0)) > 0 ? "rose" : "slate"} />
      </div>
      <div className="text-[11px] text-slate-500 mt-2">
        Expired · suspended · revoked · pending qualifications are excluded from the active registry — never shown as active.
      </div>
    </div>
  );
}

export default function SafetyTrenchIntelligenceCard({ className = "" }) {
  const [win, setWin] = React.useState("30d");
  const [snap, setSnap] = React.useState(null);
  const [err, setErr] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [selectedPn, setSelectedPn] = React.useState(null);
  const [cleanupOpen, setCleanupOpen] = React.useState(false);
  const [retrySeq, setRetrySeq] = React.useState(0);

  React.useEffect(() => {
    let cancelled = false;
    setLoading(true); setErr(null);
    fetchJsonWithTimeout(`${API}/safety/company/trench-safety-kpis?window=${win}`, {
      headers: authHeaders(),
    })
      .then((d) => { if (!cancelled) { setSnap(d); setLoading(false); } })
      .catch((e) => { if (!cancelled) { setErr(trenchErrorMessage(e, "Company trench intelligence")); setLoading(false); } });
    return () => { cancelled = true; };
  }, [retrySeq, win]);

  const band = bandForCompany(snap);
  const t = snap?.trench || {};
  const c = snap?.certifications;
  const linkage = t.linkage_breakdown || { live: 0, partial: 0, missing: 0, ambiguous: 0 };
  const source = snap?.source_classification || { trench: "MISSING", certifications: "MISSING" };

  return (
    <section
      className={`border-2 border-slate-300 rounded-lg bg-white ${className}`}
      data-testid="safety-trench-intelligence-card"
    >
      {/* Header */}
      <div className="p-4 border-b border-slate-200">
        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-2">
          <div>
            <div className="text-[10px] font-mono uppercase tracking-[0.2em] font-bold text-slate-500">
              Safety Portal
            </div>
            <div className="text-xl font-bold" data-testid="safety-trench-title">
              Trench &amp; Excavation Safety
            </div>
            <div className="text-xs text-slate-600 mt-0.5">
              Company-wide read-only intelligence · consumes the Trench Project Linker + Qualifications Engine.
            </div>
          </div>
          <div className="flex gap-1 flex-wrap" data-testid="safety-trench-window">
            {WINDOWS.map((w) => (
              <button
                key={w.key}
                type="button"
                onClick={() => setWin(w.key)}
                data-testid={`safety-trench-window-${w.key}`}
                className={`px-2 py-1 rounded text-[11px] font-mono uppercase tracking-[0.15em] font-bold border ${
                  win === w.key
                    ? "bg-purple-700 text-white border-purple-800"
                    : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
                }`}
              >
                {w.key.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
      </div>

      {loading ? (
        <div className="p-8 text-center text-slate-400">Loading trench intelligence…</div>
      ) : err ? (
        <div className="p-6" data-testid="safety-trench-error">
          <div className="text-rose-700 text-sm">
            {err === "403" ? "You need Safety or Admin role to view trench intelligence."
                            : `Could not load: ${err}`}
          </div>
          <button
            type="button"
            onClick={() => setRetrySeq((v) => v + 1)}
            className="mt-3 text-[11px] font-mono uppercase tracking-widest font-bold text-rose-700 hover:text-rose-900"
            data-testid="safety-trench-retry"
          >
            Retry
          </button>
        </div>
      ) : !snap ? (
        <div className="p-8 text-center text-slate-400">No data.</div>
      ) : (
        <div className="p-4 space-y-4">
          {/* Status band */}
          <div
            className={`p-3 rounded border-2 flex items-center gap-2 ${BAND_STYLES[band]}`}
            data-testid="safety-trench-band"
          >
            <ShieldAlert className="w-4 h-4" />
            <div className="text-sm font-bold">
              Company trench posture · {band.toUpperCase()}
            </div>
            <div className="text-xs opacity-75 ml-2">
              {t.open_holds || 0} open holds · {t.safe_to_use_verified || 0} safe-to-use verifications · {c?.expiring_soon || 0} CP certs expiring
            </div>
          </div>

          {/* Metric cards */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2"
               data-testid="safety-trench-metrics">
            <MetricCard testid="metric-exc-days" label="Excavation days" value={t.excavation_days || 0} icon={Layers} />
            <MetricCard testid="metric-inspections" label="Inspections" value={t.trench_inspections || 0} icon={ClipboardCheck} />
            <MetricCard testid="metric-open-holds" label="Open holds" value={t.open_holds || 0} icon={AlertTriangle}
                        tone={(t.open_holds || 0) > 0 ? "amber" : "slate"} />
            <MetricCard testid="metric-repairs" label="Repairs" value={t.repairs_total || 0} icon={Wrench}
                        sub={`${t.safe_to_use_verified || 0} safe-to-use verified`} />
            <MetricCard testid="metric-cp-assigns" label="CP assignments" value={t.competent_person_assignments || 0} icon={HardHat} />
            <MetricCard testid="metric-missing-link" label="Missing links (in-window)"
                        value={linkage.missing || 0}
                        tone={(linkage.missing || 0) > 0 ? "amber" : "slate"}
                        icon={Link2Off} />
          </div>

          {/* Source classification strip */}
          <div className="flex flex-wrap gap-2 items-center text-xs"
               data-testid="safety-trench-source-strip">
            <span className="font-mono uppercase tracking-[0.15em] text-slate-500 font-bold text-[10px]">Source:</span>
            {chip(SOURCE_CHIP[source.trench] || SOURCE_CHIP.MISSING,
                  `Trench · ${source.trench}`, "source-chip-trench")}
            {chip(SOURCE_CHIP[source.certifications] || SOURCE_CHIP.MISSING,
                  `Certifications · ${source.certifications}`, "source-chip-certs")}
            <span className="text-slate-500 ml-2">
              {linkage.live} LIVE · {linkage.partial} PARTIAL · {linkage.ambiguous} AMBIGUOUS · {linkage.missing} MISSING
            </span>
          </div>

          {/* Competent Person block */}
          <CompetentPersonBlock certs={c} />

          {/* Top projects */}
          <div
            className="border-2 border-slate-200 rounded overflow-hidden"
            data-testid="safety-trench-top-projects"
          >
            <div className="bg-slate-100 p-2 border-b border-slate-200 font-mono text-[10px] uppercase tracking-[0.2em] font-bold text-slate-700">
              Top projects needing trench attention
            </div>
            {(snap.top_projects || []).length === 0 ? (
              <div className="p-6 text-center text-slate-500 text-sm"
                   data-testid="safety-trench-top-projects-empty">
                No trench activity in this window. Calm state.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm min-w-[720px]">
                  <thead className="bg-slate-50 text-slate-600 text-xs uppercase tracking-[0.15em] font-mono">
                    <tr>
                      <th className="text-left px-3 py-2">Project</th>
                      <th className="text-right px-2 py-2">Exc days</th>
                      <th className="text-right px-2 py-2">Open holds</th>
                      <th className="text-right px-2 py-2">Repairs</th>
                      <th className="text-right px-2 py-2">Verifications</th>
                      <th className="text-center px-2 py-2">CP</th>
                      <th className="text-center px-2 py-2">Source</th>
                      <th className="text-right px-2 py-2">Attention</th>
                      <th className="text-right px-2 py-2">View</th>
                    </tr>
                  </thead>
                  <tbody>
                    {snap.top_projects.map((p) => (
                      <tr key={p.project_number} className="border-t border-slate-100 hover:bg-slate-50"
                          data-testid={`safety-trench-top-row-${p.project_number}`}>
                        <td className="px-3 py-2 font-bold font-mono">{p.project_number}</td>
                        <td className="text-right px-2 py-2 tabular-nums">{p.excavation_days}</td>
                        <td className="text-right px-2 py-2 tabular-nums">{p.open_holds}</td>
                        <td className="text-right px-2 py-2 tabular-nums">{p.repairs}</td>
                        <td className="text-right px-2 py-2 tabular-nums">{p.verifications}</td>
                        <td className="text-center px-2 py-2">
                          {p.cp_coverage === "assigned"
                            ? chip(SOURCE_CHIP.LIVE, "ASSIGNED", `top-cp-${p.project_number}`)
                            : p.cp_coverage === "needed"
                              ? chip(SOURCE_CHIP.PARTIAL, "NEEDED", `top-cp-${p.project_number}`)
                              : chip(SOURCE_CHIP.MISSING, "N/A", `top-cp-${p.project_number}`)}
                        </td>
                        <td className="text-center px-2 py-2">
                          {chip(SOURCE_CHIP[p.link_status] || SOURCE_CHIP.MISSING,
                                p.link_status, `top-link-${p.project_number}`)}
                        </td>
                        <td className="text-right px-2 py-2 tabular-nums font-bold">{p.attention_score}</td>
                        <td className="text-right px-2 py-2">
                          <button
                            type="button"
                            onClick={() => setSelectedPn(p.project_number)}
                            data-testid={`safety-trench-view-${p.project_number}`}
                            className="text-purple-700 hover:text-purple-900"
                          >
                            <ChevronRight className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Cleanup tile */}
          <CleanupTile open={cleanupOpen} setOpen={setCleanupOpen} />

          {/* Drilldown */}
          {selectedPn && (
            <ProjectDrilldown pn={selectedPn} onClose={() => setSelectedPn(null)} />
          )}
        </div>
      )}
    </section>
  );
}
