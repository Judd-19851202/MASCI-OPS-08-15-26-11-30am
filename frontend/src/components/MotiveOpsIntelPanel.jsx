/**
 * MotiveOpsIntelPanel.jsx · OIS-1E · Single-pane Operations Center
 * ───────────────────────────────────────────────────────────────
 * Read-only executive summary of fleet/driver/equipment/safety state
 * sourced from already-classified Motive telematics + events.
 *
 * NO writes, NO automation, NO state transitions. Pure visibility.
 * Source: GET /api/operations/intelligence
 */
import React, { useEffect, useState } from "react";
import { Activity, Truck, AlertTriangle, ShieldAlert, MapPin, RefreshCw, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { gpsBandClass } from "@/lib/gpsBand";

function StatTile({ label, value, sublabel, testid, tone = "slate" }) {
  const toneCls = {
    slate:   "border-slate-200 bg-white",
    emerald: "border-emerald-200 bg-emerald-50",
    amber:   "border-amber-200 bg-amber-50",
    rose:    "border-rose-200 bg-rose-50",
  }[tone] || "border-slate-200 bg-white";
  return (
    <div className={`rounded-md border-2 ${toneCls} p-3`} data-testid={testid}>
      <div className="text-[10px] font-mono uppercase tracking-[0.16em] font-bold text-slate-600">{label}</div>
      <div className="text-2xl font-black leading-none mt-1 text-slate-900">{value}</div>
      {sublabel ? <div className="text-[10px] font-mono text-slate-500 mt-1">{sublabel}</div> : null}
    </div>
  );
}

function FleetStrip({ fleet }) {
  if (!fleet) return null;
  const total = fleet.gps_total || 0;
  const movePct = total ? Math.round((fleet.moving / total) * 100) : 0;
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3" data-testid="ois-fleet-strip">
      <StatTile testid="ois-fleet-total" label="GPS-enabled assets" value={total} />
      <StatTile testid="ois-fleet-moving" label="Moving (last 30 min)" value={fleet.moving || 0} sublabel={`${movePct}% of fleet`} tone="emerald" />
      <StatTile testid="ois-fleet-idle" label="Idle (last 30 min)" value={fleet.idle || 0} tone="amber" />
      <StatTile testid="ois-fleet-not-reporting" label="Not reporting (>24h)" value={fleet.not_reporting || 0} tone="rose" />
    </div>
  );
}

function EventBadge({ ev }) {
  const sev = ev.severity || ev.priority || "info";
  const cls = sev === "critical"
    ? "bg-rose-100 text-rose-900 border-rose-300"
    : sev === "high"
      ? "bg-amber-100 text-amber-900 border-amber-300"
      : "bg-slate-100 text-slate-700 border-slate-300";
  const when = ev.received_at ? new Date(ev.received_at).toLocaleString() : "—";
  return (
    <li className="flex items-start gap-2 py-1.5 border-b border-slate-100 last:border-0" data-testid={`ois-event-${ev.event_family}`}>
      <span className={`inline-block px-1.5 py-0.5 rounded border text-[10px] font-mono uppercase tracking-wider font-bold ${cls}`}>
        {String(ev.event_family || "").replace(/_/g, " ")}
      </span>
      <span className="text-xs text-slate-700 truncate flex-1">
        {ev.vehicle_id ? <span className="font-mono">veh {ev.vehicle_id}</span> : <span className="text-slate-400">—</span>}
      </span>
      <span className="text-[10px] font-mono text-slate-500 shrink-0">{when}</span>
    </li>
  );
}

export default function MotiveOpsIntelPanel({ className = "" }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  const load = async () => {
    setLoading(true);
    setErr("");
    try {
      const r = await api.get("/operations/intelligence");
      setData(r.data);
    } catch (e) {
      setErr(e?.response?.data?.detail || "Failed to load operations intelligence");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  if (loading) return (
    <div className={`bg-white border border-slate-200 rounded-md p-4 ${className}`} data-testid="ois-panel-loading">
      <div className="inline-flex items-center text-slate-500 text-sm"><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Loading operations intelligence…</div>
    </div>
  );
  if (err) return (
    <div className={`bg-rose-50 border-2 border-rose-200 rounded-md p-4 text-sm text-rose-800 ${className}`} data-testid="ois-panel-error">
      <AlertTriangle className="w-4 h-4 inline -mt-0.5 mr-1" /> {err}
    </div>
  );
  if (!data) return null;

  return (
    <section className={`bg-white border border-slate-200 border-l-4 border-l-emerald-700 rounded-md p-5 ${className}`} data-testid="ois-ops-intel-panel">
      <div className="flex items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-emerald-700" />
          <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-emerald-700 font-bold">OIS-1E · Operations Intelligence</span>
        </div>
        <button
          type="button"
          onClick={load}
          className="text-[10px] font-mono uppercase tracking-wider text-slate-500 hover:text-slate-800 inline-flex items-center gap-1"
          data-testid="ois-panel-refresh"
        >
          <RefreshCw className="w-3 h-3" /> Refresh
        </button>
      </div>
      <h3 className="font-display text-xl font-black tracking-tight text-slate-900 mb-3">Live Operations Snapshot</h3>

      <FleetStrip fleet={data.fleet} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mt-4">
        {/* Drivers */}
        <div className="bg-slate-50 border border-slate-200 rounded-md p-3" data-testid="ois-drivers-card">
          <div className="flex items-center gap-2 mb-2">
            <Truck className="w-3.5 h-3.5 text-slate-700" />
            <div className="text-[10px] font-mono uppercase tracking-[0.18em] font-bold text-slate-700">Drivers (Motive)</div>
          </div>
          <div className="grid grid-cols-3 gap-2 text-center">
            <div><div className="text-2xl font-black">{data.drivers?.active ?? 0}</div><div className="text-[9px] font-mono text-slate-500 uppercase">Active</div></div>
            <div><div className="text-2xl font-black text-amber-700">{data.drivers?.deactivated_in_motive ?? 0}</div><div className="text-[9px] font-mono text-slate-500 uppercase">Deactivated</div></div>
            <div><div className="text-2xl font-black text-rose-700">{data.drivers?.hos_violations_24h ?? 0}</div><div className="text-[9px] font-mono text-slate-500 uppercase">HOS 24h</div></div>
          </div>
        </div>
        {/* Equipment */}
        <div className="bg-slate-50 border border-slate-200 rounded-md p-3" data-testid="ois-equipment-card">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-3.5 h-3.5 text-slate-700" />
            <div className="text-[10px] font-mono uppercase tracking-[0.18em] font-bold text-slate-700">Equipment Health · 24h</div>
          </div>
          <div className="grid grid-cols-3 gap-2 text-center">
            <div><div className="text-2xl font-black text-rose-700">{data.equipment?.critical_faults_open_24h ?? 0}</div><div className="text-[9px] font-mono text-slate-500 uppercase">Critical Faults</div></div>
            <div><div className="text-2xl font-black text-amber-700">{data.equipment?.gateways_offline_24h ?? 0}</div><div className="text-[9px] font-mono text-slate-500 uppercase">Gw Offline</div></div>
            <div><div className="text-2xl font-black text-rose-700">{data.equipment?.dvir_critical_24h ?? 0}</div><div className="text-[9px] font-mono text-slate-500 uppercase">DVIR Crit</div></div>
          </div>
        </div>
        {/* Safety + Geofence */}
        <div className="bg-slate-50 border border-slate-200 rounded-md p-3" data-testid="ois-safety-card">
          <div className="flex items-center gap-2 mb-2">
            <ShieldAlert className="w-3.5 h-3.5 text-slate-700" />
            <div className="text-[10px] font-mono uppercase tracking-[0.18em] font-bold text-slate-700">Safety & Geofences</div>
          </div>
          <div className="grid grid-cols-3 gap-2 text-center">
            <div><div className="text-2xl font-black text-amber-700">{data.safety?.high_severity_events_24h ?? 0}</div><div className="text-[9px] font-mono text-slate-500 uppercase">Harsh 24h</div></div>
            <div><div className="text-2xl font-black">{data.geofences?.enters_7d ?? 0}</div><div className="text-[9px] font-mono text-slate-500 uppercase">Enter 7d</div></div>
            <div><div className="text-2xl font-black">{data.geofences?.exits_7d ?? 0}</div><div className="text-[9px] font-mono text-slate-500 uppercase">Exit 7d</div></div>
          </div>
        </div>
      </div>

      {/* Recent high-priority feed */}
      <div className="mt-4">
        <div className="flex items-center gap-2 mb-2">
          <MapPin className="w-3.5 h-3.5 text-slate-700" />
          <div className="text-[10px] font-mono uppercase tracking-[0.18em] font-bold text-slate-700">Recent High-Priority Events</div>
        </div>
        {Array.isArray(data.recent_high_priority) && data.recent_high_priority.length > 0 ? (
          <ul className="bg-white border border-slate-200 rounded-md px-3 py-1" data-testid="ois-recent-events">
            {data.recent_high_priority.map((ev, idx) => (
              <EventBadge key={`${ev.event_family}-${ev.received_at}-${idx}`} ev={ev} />
            ))}
          </ul>
        ) : (
          <div className="text-xs text-slate-500 italic py-2" data-testid="ois-recent-events-empty">No high-priority events in last 7 days.</div>
        )}
      </div>

      <div className="mt-3 text-[10px] font-mono text-slate-400 uppercase tracking-[0.16em]">
        Source: Motive sync · classified events · single-pane read-only · GPS bands: green &lt;30m · amber &lt;24h · red ≥24h
      </div>
    </section>
  );
}
