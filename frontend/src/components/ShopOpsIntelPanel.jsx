/**
 * ShopOpsIntelPanel.jsx · OIS-1D · Shop Operations Intelligence
 * ─────────────────────────────────────────────────────────────
 * Read-only panel for ShopHub that aggregates the equipment-side
 * Motive signals operators must see at-a-glance without opening
 * Motive's UI: critical faults, gateway offline, DVIR defects,
 * recent fault closures, and assets not reporting GPS for >24h.
 *
 * Powered by: GET /api/operations/intelligence/shop
 */
import React, { useEffect, useState } from "react";
import { AlertOctagon, AlertTriangle, WifiOff, CheckCircle2, MapPinOff, RefreshCw, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { gpsBandClass } from "@/lib/gpsBand";

function StatPill({ label, value, tone, testid }) {
  const toneCls = {
    rose:    "bg-rose-50 border-rose-200 text-rose-900",
    amber:   "bg-amber-50 border-amber-200 text-amber-900",
    emerald: "bg-emerald-50 border-emerald-200 text-emerald-900",
    slate:   "bg-white border-slate-200 text-slate-800",
  }[tone] || "bg-white border-slate-200 text-slate-800";
  return (
    <div className={`rounded-md border-2 ${toneCls} p-3 text-center`} data-testid={testid}>
      <div className="text-2xl font-black leading-none">{value ?? 0}</div>
      <div className="text-[9px] font-mono uppercase tracking-[0.18em] mt-1 opacity-80">{label}</div>
    </div>
  );
}

function EventRow({ ev, icon: Icon, tone }) {
  const when = ev.received_at ? new Date(ev.received_at).toLocaleString() : "—";
  const veh = ev.vehicle_id || ev.asset_id || "—";
  return (
    <li className="flex items-center gap-2 py-1.5 border-b border-slate-100 last:border-0 text-xs">
      <Icon className={`w-3.5 h-3.5 shrink-0 ${tone}`} />
      <span className="font-mono text-slate-700 shrink-0">veh {veh}</span>
      <span className="text-slate-600 truncate flex-1">{ev.headline || ev.decorated_label || ev.event_family}</span>
      <span className="text-[10px] font-mono text-slate-500 shrink-0">{when}</span>
    </li>
  );
}

export default function ShopOpsIntelPanel({ className = "" }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  const load = async () => {
    setLoading(true);
    setErr("");
    try {
      const r = await api.get("/operations/intelligence/shop");
      setData(r.data);
    } catch (e) {
      setErr(e?.response?.data?.detail || "Failed to load shop intelligence");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  if (loading) return (
    <div className={`bg-white border border-slate-200 rounded-md p-4 ${className}`} data-testid="ois-shop-panel-loading">
      <div className="inline-flex items-center text-slate-500 text-sm"><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Loading shop intelligence…</div>
    </div>
  );
  if (err) return (
    <div className={`bg-rose-50 border-2 border-rose-200 rounded-md p-4 text-sm text-rose-800 ${className}`} data-testid="ois-shop-panel-error">
      <AlertTriangle className="w-4 h-4 inline -mt-0.5 mr-1" /> {err}
    </div>
  );
  if (!data) return null;
  const c = data.counts || {};

  return (
    <section className={`bg-white border border-slate-200 border-l-4 border-l-amber-500 rounded-md p-5 ${className}`} data-testid="ois-shop-intel-panel">
      <div className="flex items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <AlertOctagon className="w-4 h-4 text-amber-700" />
          <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-amber-700 font-bold">OIS-1D · Motive Equipment Intel</span>
        </div>
        <button
          type="button"
          onClick={load}
          className="text-[10px] font-mono uppercase tracking-wider text-slate-500 hover:text-slate-800 inline-flex items-center gap-1"
          data-testid="ois-shop-refresh"
        >
          <RefreshCw className="w-3 h-3" /> Refresh
        </button>
      </div>
      <h3 className="font-display text-lg font-black tracking-tight text-slate-900 mb-3">Equipment Down · Faults · GPS Health</h3>

      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 mb-4">
        <StatPill testid="ois-shop-crit-faults" label="Critical Faults" value={c.critical_faults_open} tone="rose" />
        <StatPill testid="ois-shop-gw-offline" label="Gateway Offline" value={c.gateway_offline} tone="amber" />
        <StatPill testid="ois-shop-dvir" label="DVIR Defects" value={c.dvir_defects} tone="amber" />
        <StatPill testid="ois-shop-fault-closed" label="Fault Closed 30d" value={c.recent_fault_closures} tone="emerald" />
        <StatPill testid="ois-shop-not-reporting" label="GPS Not Reporting" value={c.equipment_not_reporting} tone="rose" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Critical faults */}
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.18em] font-bold text-slate-700 mb-1">Critical Faults · Open</div>
          {Array.isArray(data.critical_faults_open) && data.critical_faults_open.length > 0 ? (
            <ul className="bg-rose-50/50 border border-rose-200 rounded-md px-3 py-1 max-h-48 overflow-auto" data-testid="ois-shop-crit-list">
              {data.critical_faults_open.slice(0, 8).map((ev, i) => (
                <EventRow key={`cf-${i}`} ev={ev} icon={AlertOctagon} tone="text-rose-700" />
              ))}
            </ul>
          ) : (
            <div className="text-xs text-slate-500 italic py-2" data-testid="ois-shop-crit-empty">No open critical faults in last 30 days.</div>
          )}
        </div>
        {/* Gateway offline */}
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.18em] font-bold text-slate-700 mb-1">Gateway Disconnected</div>
          {Array.isArray(data.gateway_offline) && data.gateway_offline.length > 0 ? (
            <ul className="bg-amber-50/50 border border-amber-200 rounded-md px-3 py-1 max-h-48 overflow-auto" data-testid="ois-shop-gw-list">
              {data.gateway_offline.slice(0, 8).map((ev, i) => (
                <EventRow key={`gw-${i}`} ev={ev} icon={WifiOff} tone="text-amber-700" />
              ))}
            </ul>
          ) : (
            <div className="text-xs text-slate-500 italic py-2" data-testid="ois-shop-gw-empty">No gateway-offline events in last 30 days.</div>
          )}
        </div>
        {/* DVIR defects */}
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.18em] font-bold text-slate-700 mb-1">DVIR Defects (High / Critical)</div>
          {Array.isArray(data.dvir_defects) && data.dvir_defects.length > 0 ? (
            <ul className="bg-amber-50/50 border border-amber-200 rounded-md px-3 py-1 max-h-48 overflow-auto" data-testid="ois-shop-dvir-list">
              {data.dvir_defects.slice(0, 8).map((ev, i) => (
                <EventRow key={`dv-${i}`} ev={ev} icon={AlertTriangle} tone="text-amber-700" />
              ))}
            </ul>
          ) : (
            <div className="text-xs text-slate-500 italic py-2" data-testid="ois-shop-dvir-empty">No high/critical DVIR defects in last 30 days.</div>
          )}
        </div>
        {/* Equipment not reporting */}
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.18em] font-bold text-slate-700 mb-1">GPS Not Reporting (&gt; 24h)</div>
          {Array.isArray(data.equipment_not_reporting) && data.equipment_not_reporting.length > 0 ? (
            <ul className="bg-rose-50/50 border border-rose-200 rounded-md px-3 py-1 max-h-48 overflow-auto" data-testid="ois-shop-nr-list">
              {data.equipment_not_reporting.slice(0, 12).map((eq, i) => {
                const last = eq.last_seen ? new Date(eq.last_seen).toLocaleDateString() : "never";
                return (
                  <li key={`nr-${i}`} className="flex items-center gap-2 py-1.5 border-b border-slate-100 last:border-0 text-xs">
                    <MapPinOff className="w-3.5 h-3.5 shrink-0 text-rose-700" />
                    <span className="font-mono text-slate-700 shrink-0">{eq.unit_number || "—"}</span>
                    <span className={`inline-block px-1.5 py-0.5 rounded border text-[10px] font-mono uppercase tracking-wider font-bold ${gpsBandClass(eq.band || "red")}`}>
                      {eq.band === "red" ? "Not Reporting" : eq.band === "amber" ? "Stale" : "Reporting"}
                    </span>
                    <span className="text-[10px] font-mono text-slate-500 shrink-0 ml-auto">Last: {last}</span>
                  </li>
                );
              })}
            </ul>
          ) : (
            <div className="text-xs text-slate-500 italic py-2" data-testid="ois-shop-nr-empty">All GPS-enabled equipment reporting within 24h.</div>
          )}
        </div>
      </div>

      <div className="mt-3 text-[10px] font-mono text-slate-400 uppercase tracking-[0.16em]">
        Source: classified motive_events · asset_mappings · read-only · refresh-on-demand
      </div>
    </section>
  );
}
