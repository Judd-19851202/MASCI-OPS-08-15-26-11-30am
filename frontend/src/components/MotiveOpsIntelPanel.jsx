/**
 * MotiveOpsIntelPanel.jsx · OIS-1E · Single-pane Operations Center
 * ───────────────────────────────────────────────────────────────
 * Read-only executive summary of fleet/driver/equipment/safety state
 * sourced from already-classified Motive telematics + events.
 *
 * NO writes, NO automation, NO state transitions. Pure visibility.
 * Source: GET /api/operations/intelligence
 */
import React, { useEffect, useMemo, useState } from "react";
import { Activity, Truck, AlertTriangle, ShieldAlert, MapPin, RefreshCw, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { gpsBand, gpsBandClass } from "@/lib/gpsBand";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

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
  const when = ev.received_at ? formatPlatformTime(ev.received_at) : "—";
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
  const [reliab, setReliab] = useState(null);  // OIS-1 Trust Pill · reliability state
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  const load = async () => {
    setLoading(true);
    setErr("");
    try {
      const [intel, rel] = await Promise.all([
        api.get("/operations/intelligence"),
        api.get("/admin/integrations/motive/reliability-state").catch(() => null),
      ]);
      setData(intel.data);
      setReliab(rel && rel.data ? rel.data : null);
    } catch (e) {
      setErr(e?.response?.data?.detail || "Failed to load operations intelligence");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  // OIS-1 Trust Pill · derive newest last_tick across loops, apply OIS-1F band.
  const trustPill = useMemo(() => {
    if (!reliab) return null;  // gracefully hide when unavailable
    const loops = reliab.loops || {};
    let newest = null;
    for (const k of Object.keys(loops)) {
      const t = loops[k]?.last_tick;
      if (t && (!newest || t > newest)) newest = t;
    }
    // Fall back to started_at if no loop has ticked yet (process just spun up).
    const ref = newest || reliab.started_at || null;
    if (!ref) {
      return { band: "red", label: "Motive status unavailable", source: "no-data" };
    }
    const b = gpsBand(ref);  // reuses OIS-1F universal classifier
    const ageLabel = b.minutes == null
      ? "never"
      : b.minutes < 60
        ? `${b.minutes} min ago`
        : b.minutes < 60 * 24
          ? `${Math.floor(b.minutes / 60)} hr ago`
          : `${Math.floor(b.minutes / (60 * 24))}d ago`;
    const statusWord = b.band === "green" ? "Healthy" : b.band === "amber" ? "Stale" : "Failed";
    const sourceWord = newest ? "synced" : "started";
    return {
      band: b.band,
      label: `Motive ${sourceWord} ${ageLabel} · ${statusWord}`,
      source: newest ? "last_tick" : "started_at",
    };
  }, [reliab]);

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
        <div className="flex items-center gap-2 flex-wrap">
          <Activity className="w-4 h-4 text-emerald-700" />
          <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-emerald-700 font-bold">OIS-1E · Operations Intelligence</span>
          {trustPill ? (
            <span
              className={`inline-flex items-center px-1.5 py-0.5 rounded border text-[10px] font-mono uppercase tracking-[0.15em] font-bold ${gpsBandClass(trustPill.band)}`}
              data-testid="ois-trust-pill"
              title={`Reliability source: ${trustPill.source}`}
            >
              {trustPill.label}
            </span>
          ) : reliab === null && !loading ? (
            <span
              className="inline-flex items-center px-1.5 py-0.5 rounded border text-[10px] font-mono uppercase tracking-[0.15em] font-bold bg-slate-100 text-slate-600 border-slate-300"
              data-testid="ois-trust-pill-missing"
            >
              Motive status unavailable
            </span>
          ) : null}
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

      {/* DSI-1D · Dispatch context strip */}
      {data.dispatch ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mt-4" data-testid="ois-dispatch-strip">
          <StatTile testid="ois-disp-assignments" label="Active assignments" value={data.dispatch.active_assignments} />
          <StatTile testid="ois-disp-drivers" label="Active drivers" value={data.dispatch.active_drivers} />
          <StatTile testid="ois-disp-equipment" label="Active equipment" value={data.dispatch.active_equipment} />
        </div>
      ) : null}

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
