// AdminAnalytics — Iter146. Operational-insight dashboard for the
// MASCI platform. Admin-only. Pulls from the lightweight usage_events
// telemetry collection (TTL 90d).
//
// Sections:
//   1. Header summary chips — event kinds + viewport split
//   2. Top routes — count, p95 latency, error rate
//   3. Per-portal usage — count + error breakdown
//   4. Sink health — queue depth, total stored, retention
//
// All read-only, no actions. Purpose: surface friction and informed
// targeting for the next optimization iter, NOT employee monitoring.

import React, { useCallback, useEffect, useState } from "react";
import {
  Activity, ChartBar, AlertTriangle, Smartphone, Monitor, Tablet,
  Loader2, RefreshCw, Database, Eye,
} from "lucide-react";
import AdminShell from "@/components/AdminShell";
import OperationalSignalsPanel from "@/components/admin/OperationalSignalsPanel";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

const WINDOW_OPTIONS = [
  { value: 1, label: "Last hour" },
  { value: 24, label: "Last 24h" },
  { value: 24 * 7, label: "Last 7 days" },
  { value: 24 * 30, label: "Last 30 days" },
];

const KIND_LABEL = {
  page_view:      { label: "Page views",       Icon: Eye,       chip: "bg-cyan-50 border-cyan-300 text-cyan-900" },
  form_submit:    { label: "Form submits",     Icon: Activity,  chip: "bg-emerald-50 border-emerald-300 text-emerald-900" },
  export:         { label: "Exports",          Icon: ChartBar,  chip: "bg-indigo-50 border-indigo-300 text-indigo-900" },
  upload_failure: { label: "Upload failures",  Icon: AlertTriangle, chip: "bg-red-50 border-red-300 text-red-900" },
  api_call:       { label: "API calls",        Icon: Activity,  chip: "bg-slate-100 border-slate-300 text-slate-900" },
};

const VIEWPORT_LABEL = {
  mobile:  { Icon: Smartphone, label: "Mobile" },
  tablet:  { Icon: Tablet,     label: "Tablet" },
  desktop: { Icon: Monitor,    label: "Desktop" },
};

const PORTAL_TINT = {
  admin:      "border-slate-300 bg-slate-50",
  safety:     "border-cyan-300 bg-cyan-50",
  hr:         "border-purple-300 bg-purple-50",
  pm:         "border-indigo-300 bg-indigo-50",
  shop:       "border-orange-300 bg-orange-50",
  dispatch:   "border-amber-300 bg-amber-50",
  leadership: "border-red-300 bg-red-50",
  public:     "border-slate-200 bg-white",
  anon:       "border-slate-200 bg-white",
};

export default function AdminAnalytics() {
  const [window, setWindow] = useState(24);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const [summary, setSummary] = useState(null);
  const [routes, setRoutes] = useState([]);
  const [portals, setPortals] = useState([]);
  const [health, setHealth] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const [s, r, p, h] = await Promise.all([
        api.get(`/admin/analytics/summary?window_hours=${window}`),
        api.get(`/admin/analytics/routes?window_hours=${window}&limit=20`),
        api.get(`/admin/analytics/portals?window_hours=${window}`),
        api.get(`/admin/analytics/health`),
      ]);
      setSummary(s.data);
      setRoutes(r.data?.rows || []);
      setPortals(p.data?.rows || []);
      setHealth(h.data);
    } catch (e) {
      // Surface a small inline error chip so the empty-state isn't
      // mistaken for "no data". Page still renders normally — we
      // don't want analytics failures to escalate to UI errors.
      setLoadError(e?.response?.data?.detail || "Failed to load analytics");
    } finally {
      setLoading(false);
    }
  }, [window]);

  useEffect(() => { load(); }, [load]);

  const totalEvents = summary?.kinds?.reduce((acc, k) => acc + k.count, 0) || 0;
  const totalErrors = summary?.kinds?.reduce((acc, k) => acc + (k.errors || 0), 0) || 0;
  const errorRate = totalEvents ? Math.round((totalErrors / totalEvents) * 100) : 0;

  return (
    <AdminShell title="Usage Analytics" kicker="ADMIN · OPERATIONAL INSIGHT">
      {/* ── Header bar ───────────────────────────────────────── */}
      <div className="flex items-center justify-between flex-wrap gap-3 mb-5" data-testid="admin-analytics-header">
        <p className="text-sm text-slate-600 max-w-2xl">
          Lightweight operational telemetry. <strong>No PII, no behavioral scoring</strong> — only routes,
          status codes, and latency. Retained 90 days. Use this to identify friction, slow flows, and
          mobile pain points — not to evaluate individual users.
        </p>
        <div className="flex items-center gap-2">
          <select
            value={window}
            onChange={(e) => setWindow(Number(e.target.value))}
            className="h-9 px-2 border-2 border-slate-300 rounded-md text-xs font-mono bg-white"
            data-testid="analytics-window-select"
          >
            {WINDOW_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
          <Button
            onClick={load}
            disabled={loading}
            variant="outline"
            size="sm"
            className="border-2"
            data-testid="analytics-refresh"
          >
            {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
          </Button>
        </div>
      </div>

      {/* ── Inline error chip if /admin/analytics/* fetch failed ── */}
      {loadError && (
        <div className="mb-4 px-3 py-2 rounded-md border-2 border-amber-300 bg-amber-50 text-amber-900 text-xs flex items-center gap-2" data-testid="analytics-load-error">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span className="font-mono">Analytics load failed: {loadError}. Showing last-known values.</span>
        </div>
      )}

      {/* ── KPI row ──────────────────────────────────────────── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5" data-testid="analytics-kpis">
        <KpiCard label="Events" value={totalEvents.toLocaleString()} hint={`${WINDOW_OPTIONS.find((w) => w.value === window)?.label}`} />
        <KpiCard label="Error rate" value={`${errorRate}%`} hint={`${totalErrors} errors`} tone={errorRate > 5 ? "warn" : "ok"} />
        <KpiCard label="Top route count" value={(routes[0]?.count || 0).toLocaleString()} hint={routes[0]?.route?.slice(0, 28) || "—"} />
        <KpiCard label="Sink depth" value={health?.queue_depth || 0} hint={`${health?.total_stored_events?.toLocaleString() || 0} stored`} />
      </div>

      {/* ── Event-kind & viewport chips ─────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">
        <Panel title="By event kind">
          {(summary?.kinds || []).length === 0 ? (
            <EmptyMini text="No events in window" />
          ) : (
            <ul className="space-y-1.5">
              {summary.kinds.map((k) => {
                const meta = KIND_LABEL[k.kind] || { label: k.kind, Icon: Activity, chip: "bg-slate-50 border-slate-300 text-slate-900" };
                const Icon = meta.Icon;
                return (
                  <li key={k.kind} className={`flex items-center gap-2 px-3 py-2 rounded-md border-2 ${meta.chip}`} data-testid={`analytics-kind-${k.kind}`}>
                    <Icon className="w-4 h-4 shrink-0" />
                    <span className="font-bold text-sm">{meta.label}</span>
                    <span className="ml-auto font-mono text-sm">{k.count.toLocaleString()}</span>
                    {k.errors > 0 && <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-red-100 text-red-800 border border-red-300">{k.errors} err</span>}
                  </li>
                );
              })}
            </ul>
          )}
        </Panel>

        <Panel title="By viewport">
          {(summary?.viewports || []).length === 0 ? (
            <EmptyMini text="No viewport data yet" />
          ) : (
            <ul className="space-y-1.5">
              {summary.viewports.map((v) => {
                const meta = VIEWPORT_LABEL[v.viewport] || { Icon: Activity, label: v.viewport };
                const Icon = meta.Icon;
                return (
                  <li key={v.viewport} className="flex items-center gap-2 px-3 py-2 rounded-md border-2 border-slate-200 bg-slate-50" data-testid={`analytics-viewport-${v.viewport}`}>
                    <Icon className="w-4 h-4 text-slate-700 shrink-0" />
                    <span className="font-bold text-sm text-slate-900">{meta.label}</span>
                    <span className="ml-auto font-mono text-sm text-slate-700">{v.count.toLocaleString()}</span>
                  </li>
                );
              })}
            </ul>
          )}
        </Panel>
      </div>

      {/* ── By portal ────────────────────────────────────────── */}
      <Panel title="By portal" className="mb-5">
        {portals.length === 0 ? (
          <EmptyMini text="No portal events yet" />
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2" data-testid="analytics-portals">
            {portals.map((p) => (
              <div key={p.portal} className={`border-2 rounded-md p-3 ${PORTAL_TINT[p.portal] || PORTAL_TINT.public}`} data-testid={`analytics-portal-${p.portal}`}>
                <div className="font-mono text-[10px] uppercase tracking-[0.2em] font-bold text-slate-700">{p.portal}</div>
                <div className="font-display text-2xl font-black text-slate-900 leading-none mt-1">{p.count.toLocaleString()}</div>
                {p.errors > 0 && (
                  <div className="text-[10px] font-mono mt-1 text-red-700">{p.errors} err</div>
                )}
              </div>
            ))}
          </div>
        )}
      </Panel>

      {/* ── Top routes table ─────────────────────────────────── */}
      <Panel title="Top routes by call count">
        {routes.length === 0 ? (
          <EmptyMini text="No API traffic in window" />
        ) : (
          <div className="overflow-x-auto" data-testid="analytics-routes">
            <table className="w-full text-sm">
              <thead className="bg-slate-100 text-slate-700 text-xs uppercase tracking-[0.15em] font-mono">
                <tr>
                  <th className="text-left px-3 py-2">Route</th>
                  <th className="text-right px-3 py-2">Calls</th>
                  <th className="text-right px-3 py-2">Avg ms</th>
                  <th className="text-right px-3 py-2">Worst ms</th>
                  <th className="text-right px-3 py-2">Errors</th>
                </tr>
              </thead>
              <tbody>
                {routes.map((r, i) => (
                  <tr key={r.route} className="border-t border-slate-100 hover:bg-slate-50" data-testid={`analytics-route-row-${i}`}>
                    <td className="px-3 py-2 font-mono text-xs break-all">{r.route}</td>
                    <td className="px-3 py-2 text-right font-mono">{r.count.toLocaleString()}</td>
                    <td className="px-3 py-2 text-right font-mono">{r.avg_ms || "—"}</td>
                    <td className={`px-3 py-2 text-right font-mono ${r.max_ms > 1000 ? "text-red-700 font-bold" : r.max_ms > 500 ? "text-amber-700" : ""}`}>
                      {r.max_ms || "—"}
                    </td>
                    <td className={`px-3 py-2 text-right font-mono ${r.errors > 0 ? "text-red-700 font-bold" : "text-slate-400"}`}>
                      {r.errors || 0}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>

      {/* ── Sink health ──────────────────────────────────────── */}
      {health && (
        <div className="mt-5 flex items-center gap-3 text-xs text-slate-600 font-mono" data-testid="analytics-sink-health">
          <Database className="w-4 h-4" />
          Sink {health.sink_running ? "running" : "stopped"} · Queue depth {health.queue_depth} ·
          {" "}{health.total_stored_events?.toLocaleString?.() || 0} events stored · {health.retention_days}-day retention
        </div>
      )}

      {/* ── Operational Signals (Iter160) ───────────────────── */}
      <OperationalSignalsPanel />
    </AdminShell>
  );
}

function KpiCard({ label, value, hint, tone }) {
  const toneClass = tone === "warn" ? "border-amber-300 bg-amber-50" : "border-slate-300 bg-white";
  return (
    <div className={`border-2 rounded-md p-3 ${toneClass}`} data-testid={`analytics-kpi-${label.toLowerCase().replace(/\s+/g, "-")}`}>
      <div className="font-mono text-[10px] uppercase tracking-[0.2em] font-bold text-slate-700">{label}</div>
      <div className="font-display text-2xl font-black text-slate-900 leading-none mt-1">{value}</div>
      {hint && <div className="text-[11px] font-mono text-slate-500 mt-1 truncate">{hint}</div>}
    </div>
  );
}

function Panel({ title, children, className = "" }) {
  return (
    <div className={`bg-white border-2 border-slate-300 rounded-md ${className}`}>
      <div className="bg-slate-50 border-b-2 border-slate-200 px-4 py-2 font-mono text-[10px] uppercase tracking-[0.2em] font-bold text-slate-700">
        {title}
      </div>
      <div className="p-3">{children}</div>
    </div>
  );
}

function EmptyMini({ text }) {
  return (
    <div className="text-center text-slate-500 italic text-sm py-4">{text}</div>
  );
}
