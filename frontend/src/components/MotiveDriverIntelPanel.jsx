/**
 * MotiveDriverIntelPanel.jsx · OIS-1C · Driver Command Profile
 * ─────────────────────────────────────────────────────────────
 * Read-only panel that surfaces the 30-day Motive operational
 * intelligence for a single driver: HOS violations, harsh-event
 * count, DVIR inspections, and a recent-events feed. Mapping
 * metadata (MASCI ↔ Motive) is rendered up top.
 *
 * Source: GET /api/operations/intelligence/driver/{driverKey}
 *
 * Usage:
 *   <MotiveDriverIntelPanel driverKey="abc123" />
 */
import React, { useEffect, useState } from "react";
import { Truck, AlertTriangle, ShieldAlert, Activity, RefreshCw, Loader2, Clock } from "lucide-react";
import { api } from "@/lib/api";

function CountTile({ label, value, tone, testid }) {
  const toneCls = {
    rose:    "border-rose-200 bg-rose-50 text-rose-900",
    amber:   "border-amber-200 bg-amber-50 text-amber-900",
    emerald: "border-emerald-200 bg-emerald-50 text-emerald-900",
    slate:   "border-slate-200 bg-white text-slate-900",
  }[tone] || "border-slate-200 bg-white text-slate-900";
  return (
    <div className={`rounded-md border-2 ${toneCls} p-3 text-center`} data-testid={testid}>
      <div className="text-2xl font-black leading-none">{value ?? 0}</div>
      <div className="text-[9px] font-mono uppercase tracking-[0.18em] mt-1 opacity-80">{label}</div>
    </div>
  );
}

export default function MotiveDriverIntelPanel({ driverKey, className = "" }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  const load = async () => {
    if (!driverKey) return;
    setLoading(true);
    setErr("");
    try {
      const r = await api.get(`/operations/intelligence/driver/${encodeURIComponent(driverKey)}`);
      setData(r.data);
    } catch (e) {
      setErr(e?.response?.data?.detail || "Failed to load driver intelligence");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [driverKey]);

  if (!driverKey) return null;
  if (loading) return (
    <div className={`bg-white border border-slate-200 rounded-md p-4 ${className}`} data-testid="ois-driver-loading">
      <div className="inline-flex items-center text-slate-500 text-sm"><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Loading driver intel…</div>
    </div>
  );
  if (err) return (
    <div className={`bg-rose-50 border-2 border-rose-200 rounded-md p-4 text-sm text-rose-800 ${className}`} data-testid="ois-driver-error">
      <AlertTriangle className="w-4 h-4 inline -mt-0.5 mr-1" /> {err}
    </div>
  );
  if (!data) return null;

  const mapping = data.mapping;
  const motive = (mapping && mapping.motive) || {};
  const c30 = data.counts_30d || {};
  const c24 = data.counts_24h || {};

  return (
    <section className={`bg-white border border-slate-200 border-l-4 border-l-indigo-700 rounded-md p-5 ${className}`} data-testid="ois-driver-intel-panel">
      <div className="flex items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <Truck className="w-4 h-4 text-indigo-700" />
          <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-indigo-700 font-bold">OIS-1C · Driver Command Profile</span>
        </div>
        <button
          type="button"
          onClick={load}
          className="text-[10px] font-mono uppercase tracking-wider text-slate-500 hover:text-slate-800 inline-flex items-center gap-1"
          data-testid="ois-driver-refresh"
        >
          <RefreshCw className="w-3 h-3" /> Refresh
        </button>
      </div>

      <h3 className="font-display text-xl font-black tracking-tight text-slate-900 leading-tight" data-testid="ois-driver-name">
        {mapping?.masci_employee_name || motive.driver_name || motive.full_name || data.driver_key || "Unknown driver"}
      </h3>
      <div className="text-xs text-slate-500 mt-0.5" data-testid="ois-driver-meta">
        {mapping?.masci_employee_trade ? <span className="font-mono mr-2">{mapping.masci_employee_trade}</span> : null}
        {motive.user_id || data.motive_user_id ? <span className="font-mono">Motive user · {motive.user_id || data.motive_user_id}</span> : <span className="text-slate-400 italic">Unmapped to Motive</span>}
      </div>

      {/* 30-day counts */}
      <div className="grid grid-cols-3 gap-2 mt-4">
        <CountTile testid="ois-driver-hos-30d" label="HOS Violations · 30d" value={c30.hours_of_service || c30.hos_violations} tone={c30.hos_violations > 0 ? "rose" : "slate"} />
        <CountTile testid="ois-driver-harsh-30d" label="Harsh Events · 30d" value={c30.harsh_events} tone={c30.harsh_events > 0 ? "amber" : "slate"} />
        <CountTile testid="ois-driver-dvir-30d" label="DVIR Inspections · 30d" value={c30.dvir_inspections} tone="slate" />
      </div>

      {/* 24h watch */}
      <div className="grid grid-cols-2 gap-2 mt-2">
        <CountTile testid="ois-driver-hos-24h" label="HOS · last 24h" value={c24.hos_violations} tone={c24.hos_violations > 0 ? "rose" : "slate"} />
        <CountTile testid="ois-driver-harsh-24h" label="High Harsh · last 24h" value={c24.harsh_events_high} tone={c24.harsh_events_high > 0 ? "rose" : "slate"} />
      </div>

      {/* Recent events */}
      <div className="mt-4">
        <div className="flex items-center gap-2 mb-2">
          <Activity className="w-3.5 h-3.5 text-slate-700" />
          <div className="text-[10px] font-mono uppercase tracking-[0.18em] font-bold text-slate-700">Recent Motive Events</div>
        </div>
        {Array.isArray(data.recent_events) && data.recent_events.length > 0 ? (
          <ul className="bg-slate-50 border border-slate-200 rounded-md px-3 py-1 max-h-60 overflow-auto" data-testid="ois-driver-events">
            {data.recent_events.map((ev, idx) => {
              const sev = ev.severity || ev.priority || "info";
              const sevCls = sev === "critical"
                ? "bg-rose-100 text-rose-900 border-rose-300"
                : sev === "high"
                  ? "bg-amber-100 text-amber-900 border-amber-300"
                  : "bg-slate-100 text-slate-700 border-slate-300";
              const when = ev.received_at ? new Date(ev.received_at).toLocaleString() : "—";
              return (
                <li key={`${ev.event_family}-${ev.received_at}-${idx}`} className="flex items-start gap-2 py-1.5 border-b border-slate-100 last:border-0 text-xs">
                  <span className={`inline-block px-1.5 py-0.5 rounded border text-[10px] font-mono uppercase tracking-wider font-bold ${sevCls}`}>
                    {String(ev.event_family || "").replace(/_/g, " ")}
                  </span>
                  <span className="text-slate-700 truncate flex-1">{ev.headline || (ev.vehicle_id ? `Veh ${ev.vehicle_id}` : "—")}</span>
                  <span className="text-[10px] font-mono text-slate-500 shrink-0">{when}</span>
                </li>
              );
            })}
          </ul>
        ) : (
          <div className="text-xs text-slate-500 italic py-2" data-testid="ois-driver-events-empty">
            {data.motive_user_id ? "No Motive events recorded in last 30 days." : "Driver not linked to Motive — no telematics intel."}
          </div>
        )}
      </div>

      <div className="mt-3 text-[10px] font-mono text-slate-400 uppercase tracking-[0.16em]">
        Source: classified motive_events · employee_mappings · read-only
      </div>
    </section>
  );
}
