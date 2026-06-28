/**
 * TRACK 16.10 · MASCI Transportation Command Queue + Automation Health
 *
 * Three native admin surfaces (no design drift, reuses PortalShell,
 * shared adminHeaders, api client):
 *   - Morning Command Queue (Blocking / Urgent / Action Required / Due Soon / Needs Configuration)
 *   - Automation Health (last run, scheduler, route status)
 *   - Compliance Forecast (next 30 days)
 */
import React, { useEffect, useState, useCallback } from "react";
import { NavLink, Routes, Route } from "react-router-dom";
import {
  ListChecks, ShieldAlert, AlertTriangle, Clock, ShieldCheck,
  Activity, CalendarRange, RefreshCw, PlayCircle, Eye, FileWarning,
  CheckCircle2, X,
} from "lucide-react";
import { api } from "@/lib/api";
import { adminHeaders, Chip, PageHeader, EmptyState, useTxPathPrefix } from "./_shared";

const SUB_TABS = [
  { to: "", label: "Morning Queue", end: true, testid: "tx-cq-tab-queue" },
  { to: "health", label: "Automation Health", testid: "tx-cq-tab-health" },
  { to: "forecast", label: "30-day Forecast", testid: "tx-cq-tab-forecast" },
];

export function CommandQueueCenter() {
  const prefix = useTxPathPrefix();
  return (
    <div data-testid="tx-command-queue-center" className="space-y-4">
      <PageHeader
        title="Command Queue"
        subtitle="Proactive transportation operating system · daily automation"
        testid="tx-cq-header"
      />
      <nav className="flex flex-wrap gap-1 border-b border-slate-200 pb-2 mb-4" data-testid="tx-cq-subtabs">
        {SUB_TABS.map((t) => (
          <NavLink
            key={t.label}
            to={`${prefix}/command-queue/${t.to}`}
            end={t.end}
            data-testid={t.testid}
            className={({ isActive }) =>
              `inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-colors ${
                isActive ? "bg-amber-700 text-white" : "text-slate-700 hover:bg-slate-100"
              }`
            }
          >
            {t.label}
          </NavLink>
        ))}
      </nav>
      <Routes>
        <Route index element={<MorningQueue />} />
        <Route path="health" element={<AutomationHealth />} />
        <Route path="forecast" element={<ComplianceForecast />} />
      </Routes>
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────
function MorningQueue() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(null);
  const load = useCallback(async () => {
    try {
      const r = await api.get("/admin/transportation/automation/actions?status=open",
        { headers: adminHeaders() });
      setData(r.data);
    } catch (e) {
      setErr(e.response?.data?.detail || e.message);
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  const patch = async (aid, status) => {
    setBusy(aid);
    try {
      await api.patch(`/admin/transportation/automation/actions/${aid}`,
        { status }, { headers: adminHeaders() });
      await load();
    } catch (e) {
      alert(e.response?.data?.detail || e.message);
    } finally {
      setBusy(null);
    }
  };

  if (err) return <EmptyState title="Command queue unavailable" hint={err} testid="tx-cq-err" />;
  if (!data) return <div data-testid="tx-cq-loading" className="text-slate-500 text-sm">Loading…</div>;

  if (data.count === 0) {
    return (
      <div data-testid="tx-cq-empty" className="bg-emerald-50 border border-emerald-200 rounded-lg p-6 text-center">
        <CheckCircle2 className="h-10 w-10 mx-auto text-emerald-700" />
        <h3 className="mt-2 font-semibold text-emerald-900">All clear</h3>
        <p className="text-sm text-emerald-700">No open transportation action items right now.</p>
      </div>
    );
  }

  const SECTIONS = [
    { key: "blocking", label: "Blocking", icon: ShieldAlert, tone: "bg-red-50 border-red-200 text-red-900", testid: "tx-cq-section-blocking" },
    { key: "urgent", label: "Urgent", icon: AlertTriangle, tone: "bg-orange-50 border-orange-200 text-orange-900", testid: "tx-cq-section-urgent" },
    { key: "action_required", label: "Action Required", icon: Clock, tone: "bg-amber-50 border-amber-200 text-amber-900", testid: "tx-cq-section-action_required" },
    { key: "advisory", label: "Due Soon", icon: Eye, tone: "bg-sky-50 border-sky-200 text-sky-900", testid: "tx-cq-section-advisory" },
    { key: "info", label: "Informational", icon: ListChecks, tone: "bg-slate-50 border-slate-200 text-slate-700", testid: "tx-cq-section-info" },
  ];

  return (
    <div data-testid="tx-cq-morning" className="space-y-4">
      {SECTIONS.map((s) => {
        const rows = data.buckets[s.key] || [];
        if (rows.length === 0) return null;
        const Icon = s.icon;
        return (
          <section key={s.key} data-testid={s.testid} className={`rounded-lg border ${s.tone}`}>
            <header className="px-4 py-2 border-b border-current/20 flex items-center gap-2">
              <Icon className="h-4 w-4" />
              <h3 className="font-semibold">{s.label}</h3>
              <span className="text-xs opacity-70">· {rows.length}</span>
            </header>
            <ul className="divide-y divide-current/10">
              {rows.map((it) => (
                <li key={it.id} data-testid={`tx-cq-item-${it.id}`} className="px-4 py-3 flex items-start gap-3">
                  <div className="flex-1">
                    <div className="font-medium text-sm">{it.title}</div>
                    <div className="text-xs opacity-80 mt-0.5">{it.description}</div>
                    <div className="text-xs opacity-70 mt-1 flex gap-3">
                      <span>Due: {(it.due_date || "").slice(0, 10) || "—"}</span>
                      <span>Owner: {it.assigned_role || "—"}</span>
                      <span>Entity: {it.entity_type} · {(it.entity_id || "").slice(0, 12)}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      data-testid={`tx-cq-resolve-${it.id}`}
                      disabled={busy === it.id}
                      onClick={() => patch(it.id, "resolved")}
                      className="text-xs px-2 py-1 rounded bg-emerald-700 hover:bg-emerald-800 text-white disabled:opacity-50"
                    >
                      Resolved
                    </button>
                    <button
                      data-testid={`tx-cq-dismiss-${it.id}`}
                      disabled={busy === it.id}
                      onClick={() => patch(it.id, "dismissed")}
                      className="text-xs px-2 py-1 rounded bg-slate-200 hover:bg-slate-300 text-slate-800 disabled:opacity-50"
                    >
                      Dismiss
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        );
      })}
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────
function AutomationHealth() {
  return (
    <div className="space-y-4">
      <AutomationHealthCore />
      <HrSyncHealthCard />
      <DigestCard />
    </div>
  );
}

function AutomationHealthCore() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [running, setRunning] = useState(false);
  const [runResult, setRunResult] = useState(null);
  const load = useCallback(async () => {
    try {
      const r = await api.get("/admin/transportation/automation/health",
        { headers: adminHeaders() });
      setData(r.data);
    } catch (e) {
      setErr(e.response?.data?.detail || e.message);
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  const run = async (dry) => {
    setRunning(true);
    setRunResult(null);
    try {
      const ep = dry ? "/admin/transportation/automation/dry-run"
                     : "/admin/transportation/automation/run";
      const r = await api.post(ep, { triggered_by: dry ? "admin-dryrun" : "admin" },
        { headers: adminHeaders() });
      setRunResult(r.data);
      await load();
    } catch (e) {
      setRunResult({ ok: false, error: e.response?.data?.detail || e.message });
    } finally {
      setRunning(false);
    }
  };

  if (err) return <EmptyState title="Health unavailable" hint={err} testid="tx-cq-health-err" />;
  if (!data) return <div data-testid="tx-cq-health-loading" className="text-slate-500 text-sm">Loading…</div>;
  const last = data.last_run;
  return (
    <div data-testid="tx-cq-health" className="space-y-4">
      <section className="bg-white border border-slate-200 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-3">
          <Activity className="h-4 w-4 text-amber-700" />
          <h3 className="font-semibold">Last automation run</h3>
        </div>
        {last ? (
          <dl className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm" data-testid="tx-cq-health-last">
            <Row label="Started" value={(last.started_at || "").slice(0, 19).replace("T", " ")} />
            <Row label="Completed" value={(last.completed_at || "").slice(0, 19).replace("T", " ")} />
            <Row label="Triggered by" value={last.triggered_by || "—"} />
            <Row label="Dry-run" value={last.dry_run ? "Yes" : "No"} />
            <Row label="Items scanned" value={last.counts?.items_scanned ?? 0} />
            <Row label="Actions created" value={last.counts?.actions_created ?? 0} />
            <Row label="Emails attempted" value={last.counts?.emails_attempted ?? 0} />
            <Row label="Emails sent" value={last.counts?.emails_sent ?? 0} />
            <Row label="Needs configuration" value={last.counts?.emails_needs_configuration ?? 0} />
            <Row label="Eligibility updates" value={last.counts?.eligibility_updates ?? 0} />
            <Row label="Errors" value={last.counts?.errors ?? 0} />
          </dl>
        ) : (
          <div className="text-sm text-slate-500">No run recorded yet.</div>
        )}
        {data.stale ? (
          <div data-testid="tx-cq-health-stale" className="mt-3 text-xs bg-amber-50 border border-amber-200 rounded p-2 text-amber-900">
            ⚠ Advisory: no automation run in the last {data.stale_threshold_hours}h.
          </div>
        ) : null}
      </section>

      <section className="bg-white border border-slate-200 rounded-lg p-4" data-testid="tx-cq-health-routes">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-amber-700" />
            <h3 className="font-semibold">Email route status</h3>
          </div>
          <div className="text-xs text-slate-500">
            Scheduler: {data.scheduler_enabled ? <span className="text-emerald-700 font-medium">enabled</span> : <span className="text-amber-700 font-medium">disabled (preview)</span>}
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div data-testid="tx-cq-routes-live">
            <div className="text-emerald-700 font-medium mb-1">Live ({data.routes_live.length})</div>
            <ul className="space-y-0.5 font-mono text-[11px]">
              {data.routes_live.map((k) => <li key={k}>{k}</li>)}
            </ul>
          </div>
          <div data-testid="tx-cq-routes-dryrun">
            <div className="text-slate-700 font-medium mb-1">Dry-run ({data.routes_dry_run.length})</div>
            <ul className="space-y-0.5 font-mono text-[11px] max-h-48 overflow-y-auto">
              {data.routes_dry_run.map((k) => <li key={k}>{k}</li>)}
            </ul>
          </div>
        </div>
      </section>

      <section className="bg-white border border-slate-200 rounded-lg p-4" data-testid="tx-cq-health-controls">
        <div className="flex items-center gap-2 mb-3">
          <PlayCircle className="h-4 w-4 text-amber-700" />
          <h3 className="font-semibold">Manual run</h3>
        </div>
        <div className="flex gap-2">
          <button
            data-testid="tx-cq-run-live"
            disabled={running}
            onClick={() => run(false)}
            className="bg-amber-700 hover:bg-amber-800 disabled:opacity-50 text-white text-sm px-4 py-2 rounded inline-flex items-center gap-2"
          >
            <PlayCircle className="h-4 w-4" /> {running ? "Running…" : "Run automation"}
          </button>
          <button
            data-testid="tx-cq-run-dry"
            disabled={running}
            onClick={() => run(true)}
            className="bg-slate-200 hover:bg-slate-300 disabled:opacity-50 text-slate-800 text-sm px-4 py-2 rounded inline-flex items-center gap-2"
          >
            <Eye className="h-4 w-4" /> Dry-run
          </button>
        </div>
        {runResult ? (
          <pre data-testid="tx-cq-run-result" className="mt-3 text-xs bg-slate-50 border border-slate-200 rounded p-2 max-h-64 overflow-y-auto">
            {JSON.stringify(runResult.counts || runResult, null, 2)}
          </pre>
        ) : null}
      </section>
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div>
      <dt className="text-xs text-slate-500">{label}</dt>
      <dd className="text-sm text-slate-900 font-medium">{value}</dd>
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────
function ComplianceForecast() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  useEffect(() => {
    api.get("/admin/transportation/automation/forecast",
      { headers: adminHeaders() })
      .then(r => setData(r.data))
      .catch(e => setErr(e.response?.data?.detail || e.message));
  }, []);
  if (err) return <EmptyState title="Forecast unavailable" hint={err} testid="tx-cq-forecast-err" />;
  if (!data) return <div data-testid="tx-cq-forecast-loading" className="text-slate-500 text-sm">Loading…</div>;
  const sections = [
    { key: "inspections_due", label: "Truck inspections due", icon: ShieldCheck },
    { key: "orientations_expiring", label: "Orientations expiring", icon: AlertTriangle },
    { key: "driver_documents_expiring", label: "Driver documents expiring", icon: FileWarning },
    { key: "carrier_documents_expiring", label: "Carrier documents expiring", icon: FileWarning },
    { key: "packets_pending", label: "Packets pending too long", icon: Clock },
    { key: "overrides", label: "Active overrides", icon: ShieldAlert },
  ];
  return (
    <div data-testid="tx-cq-forecast" className="space-y-4">
      <div className="text-sm text-slate-600">Next {data.horizon_days} days. Reads live data; nothing is persisted by this view.</div>
      {sections.map((s) => {
        const rows = data.data[s.key] || [];
        const Icon = s.icon;
        return (
          <section key={s.key} className="bg-white border border-slate-200 rounded-lg overflow-hidden" data-testid={`tx-cq-forecast-${s.key}`}>
            <header className="px-3 py-2 border-b border-slate-200 flex items-center gap-2">
              <Icon className="h-4 w-4 text-amber-700" />
              <h3 className="font-semibold text-sm">{s.label}</h3>
              <span className="text-xs text-slate-500">· {rows.length}</span>
            </header>
            {rows.length === 0 ? (
              <div className="p-3 text-xs text-slate-400">Nothing scheduled in the next 30 days.</div>
            ) : (
              <table className="w-full text-xs">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="text-left px-3 py-1.5">Due</th>
                    <th className="text-left px-3 py-1.5">Entity</th>
                    <th className="text-left px-3 py-1.5">Kind</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, i) => (
                    <tr key={i} className="border-b border-slate-100" data-testid={`tx-cq-forecast-row-${s.key}-${i}`}>
                      <td className="px-3 py-1.5 font-mono">{(row.due_date || "").slice(0, 10)}</td>
                      <td className="px-3 py-1.5">{row.entity_label || row.entity_id}</td>
                      <td className="px-3 py-1.5">{row.item_kind}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        );
      })}
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────
// TRACK 16.11A · HR ↔ Transportation Sync Health card
// ────────────────────────────────────────────────────────────────────
function HrSyncHealthCard() {
  const [data, setData] = useState(null);
  const [report, setReport] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const [showReport, setShowReport] = useState(false);

  const load = useCallback(async () => {
    try {
      const r = await api.get("/admin/transportation/hr-sync", { headers: adminHeaders() });
      setData(r.data);
    } catch (e) {
      setErr(e.response?.data?.detail || e.message);
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  const runScan = async () => {
    setBusy(true);
    try {
      const r = await api.get("/admin/transportation/hr-sync/report?run=true",
        { headers: adminHeaders() });
      setReport(r.data);
      setShowReport(true);
      await load();
    } catch (e) {
      alert(e.response?.data?.detail || e.message);
    } finally {
      setBusy(false);
    }
  };

  if (err) {
    return (
      <section className="bg-white border border-slate-200 rounded-lg p-4" data-testid="tx-cq-hr-sync-card">
        <div className="text-sm text-red-700">{err}</div>
      </section>
    );
  }

  const counts = data?.counts || {};
  const healthChip = {
    healthy: "bg-emerald-100 text-emerald-800 border-emerald-300",
    warning: "bg-amber-100 text-amber-800 border-amber-300",
    critical: "bg-rose-100 text-rose-800 border-rose-300",
    unknown: "bg-slate-100 text-slate-600 border-slate-300",
  }[data?.health || "unknown"];

  return (
    <section className="bg-white border border-slate-200 rounded-lg p-4" data-testid="tx-cq-hr-sync-card">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-emerald-700" />
          <h3 className="font-semibold">HR Synchronization Health (Track 16.11A)</h3>
        </div>
        <span
          data-testid="tx-cq-hr-sync-chip"
          className={`text-[11px] px-2 py-0.5 rounded-full border ${healthChip}`}
        >
          {data?.health || "unknown"}
        </span>
      </div>
      <dl className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm mb-3" data-testid="tx-cq-hr-sync-stats">
        <Row label="Mismatches" value={counts.sync_mismatches ?? 0} />
        <Row label="Projection failures" value={counts.projection_failures ?? 0} />
        <Row label="Dispatch risks" value={counts.dispatch_risks ?? 0} />
        <Row label="Unknown identities" value={counts.unknown_identities ?? 0} />
        <Row label="Drivers checked" value={counts.drivers_checked ?? 0} />
        <Row label="Employees checked" value={counts.employees_checked ?? 0} />
        <Row label="Avg sync age (d)" value={data?.average_sync_age_days ?? "—"} />
        <Row label="Oldest sync age (d)" value={data?.oldest_sync_age_days ?? "—"} />
      </dl>
      <div className="flex items-center gap-2 text-xs">
        <button
          data-testid="tx-cq-hr-sync-run"
          disabled={busy}
          onClick={runScan}
          className="px-2 py-1 rounded bg-emerald-600 hover:bg-emerald-700 text-white disabled:opacity-50"
        >
          {busy ? "Scanning…" : "View synchronization report"}
        </button>
        <span className="text-slate-500">
          Last run: {data?.last_run_at ? data.last_run_at.slice(0, 19).replace("T", " ") : "—"}
        </span>
      </div>
      {showReport && report && (
        <div className="mt-3 border-t border-slate-200 pt-3 text-xs" data-testid="tx-cq-hr-sync-report">
          <div className="flex items-center justify-between mb-2">
            <div className="font-semibold text-slate-700">Mismatch detail ({(report.mismatches || []).length})</div>
            <button onClick={() => setShowReport(false)} className="text-slate-500 hover:text-slate-800">close</button>
          </div>
          {(report.mismatches || []).length === 0 ? (
            <div className="text-emerald-700">HR ↔ Transportation are fully synchronized.</div>
          ) : (
            <ul className="space-y-1.5 max-h-80 overflow-y-auto">
              {(report.mismatches || []).slice(0, 100).map((m, i) => (
                <li key={i} data-testid={`tx-cq-hr-sync-mismatch-${i}`}
                    className={`rounded px-2 py-1 border ${
                      m.severity === "critical" ? "border-rose-300 bg-rose-50" :
                      m.severity === "block" ? "border-amber-300 bg-amber-50" :
                      "border-slate-200 bg-slate-50"}`}>
                  <div className="font-medium text-slate-800">{m.reason}</div>
                  <div className="text-[11px] text-slate-500">
                    {m.code} · {m.severity}
                    {m.employee_id ? ` · emp ${m.employee_id}` : ""}
                  </div>
                  {m.recommended_action && (
                    <div className="text-[11px] text-slate-600 mt-0.5">{m.recommended_action}</div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}


// ────────────────────────────────────────────────────────────────────
// TRACK 16.10A · Weekly Command Digest status card + admin controls
// ────────────────────────────────────────────────────────────────────
function DigestCard() {
  const [preview, setPreview] = useState(null);
  const [history, setHistory] = useState([]);
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const load = useCallback(async () => {
    try {
      const r1 = await api.get("/admin/transportation/automation/digest/preview",
        { headers: adminHeaders() });
      setPreview(r1.data);
      const r2 = await api.get("/admin/transportation/automation/digest/runs?limit=5",
        { headers: adminHeaders() });
      setHistory(r2.data.items || []);
    } catch (e) {
      setErr(e.response?.data?.detail || e.message);
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  const fire = async (which) => {
    setBusy(which);
    try {
      const url = which === "dry"
        ? "/admin/transportation/automation/digest/dry-run"
        : "/admin/transportation/automation/digest/send-now";
      await api.post(url, {}, { headers: adminHeaders() });
      await load();
    } catch (e) {
      alert(e.response?.data?.detail || e.message);
    } finally {
      setBusy(null);
    }
  };

  if (err) return (
    <section className="bg-white border border-slate-200 rounded-lg p-4" data-testid="tx-cq-digest-card">
      <div className="text-sm text-red-700">{err}</div>
    </section>
  );

  const lastRun = history[0];
  return (
    <section className="bg-white border border-slate-200 rounded-lg p-4" data-testid="tx-cq-digest-card">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <CalendarRange className="h-4 w-4 text-amber-700" />
          <h3 className="font-semibold">Weekly Command Digest (Track 16.10A)</h3>
        </div>
        <div className="text-xs text-slate-500" data-testid="tx-cq-digest-week">
          {preview?.week_key || "—"}
        </div>
      </div>

      {lastRun ? (
        <dl className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm mb-3" data-testid="tx-cq-digest-last">
          <Row label="Last run" value={(lastRun.ts || "").slice(0, 19).replace("T", " ")} />
          <Row label="Status" value={lastRun.status} />
          <Row label="Dry-run" value={lastRun.dry_run ? "Yes" : "No"} />
          <Row label="Recipients" value={lastRun.recipients_count ?? 0} />
        </dl>
      ) : (
        <div className="text-sm text-slate-500 mb-3">No digest run recorded yet.</div>
      )}

      {preview ? (
        <dl className="grid grid-cols-3 sm:grid-cols-6 gap-2 text-xs mb-3 bg-slate-50 border border-slate-200 rounded p-2" data-testid="tx-cq-digest-summary">
          <SmallStat label="Open" value={preview.summary.open_total} />
          <SmallStat label="Blocking" value={preview.summary.blocking} tone="text-red-700" />
          <SmallStat label="Urgent" value={preview.summary.urgent} tone="text-orange-700" />
          <SmallStat label="Action" value={preview.summary.action_required} tone="text-amber-700" />
          <SmallStat label="Due 7d" value={preview.summary.due_this_week} tone="text-sky-700" />
          <SmallStat label="Overdue" value={preview.summary.overdue} tone="text-red-700" />
        </dl>
      ) : null}

      <div className="flex gap-2">
        <button
          data-testid="tx-cq-digest-dry"
          disabled={busy !== null}
          onClick={() => fire("dry")}
          className="bg-slate-200 hover:bg-slate-300 disabled:opacity-50 text-slate-800 text-sm px-3 py-1.5 rounded inline-flex items-center gap-1"
        >
          <Eye className="h-3.5 w-3.5" /> Dry-run digest
        </button>
        <button
          data-testid="tx-cq-digest-send"
          disabled={busy !== null}
          onClick={() => fire("send")}
          className="bg-amber-700 hover:bg-amber-800 disabled:opacity-50 text-white text-sm px-3 py-1.5 rounded inline-flex items-center gap-1"
        >
          <PlayCircle className="h-3.5 w-3.5" /> Send digest now
        </button>
        <button
          data-testid="tx-cq-digest-preview-toggle"
          onClick={() => setShowPreview((v) => !v)}
          className="bg-slate-100 hover:bg-slate-200 text-slate-800 text-sm px-3 py-1.5 rounded inline-flex items-center gap-1"
        >
          {showPreview ? "Hide preview" : "Preview email"}
        </button>
      </div>

      {showPreview && preview ? (
        <div className="mt-3 border border-slate-200 rounded" data-testid="tx-cq-digest-preview-body">
          <div className="px-3 py-2 border-b border-slate-200 text-xs text-slate-600 font-mono">{preview.subject}</div>
          <div className="p-2 max-h-96 overflow-y-auto" dangerouslySetInnerHTML={{ __html: preview.body_html }} />
        </div>
      ) : null}
    </section>
  );
}

function SmallStat({ label, value, tone = "text-slate-900" }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`font-semibold ${tone}`}>{value}</div>
    </div>
  );
}
