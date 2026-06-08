/**
 * DriverCommandProfile.jsx · DCP-1 · Shared driver profile component
 * ──────────────────────────────────────────────────────────────────
 * One component, four portal consumers (Admin, HR, Safety, Dispatch).
 * The backend at `/api/operations/drivers/{driverKey}/profile` shapes
 * the payload by role; this component renders whatever sections the
 * server returns. No client-side privilege checks — server is the
 * source of truth.
 *
 * Usage:
 *   <DriverCommandProfile driverKey={employeeId} />
 */
import React, { useEffect, useState } from "react";
import {
  IdCard, Truck, ShieldCheck, GraduationCap, MapPin, Activity,
  AlertTriangle, RefreshCw, Loader2, CheckCircle2, Clock,
} from "lucide-react";
import { api } from "@/lib/api";

const SEV_PILL = {
  critical: "bg-rose-100 text-rose-900 border-rose-300",
  high:     "bg-amber-100 text-amber-900 border-amber-300",
  medium:   "bg-amber-50 text-amber-800 border-amber-200",
  low:      "bg-slate-100 text-slate-700 border-slate-300",
  info:     "bg-slate-100 text-slate-700 border-slate-300",
};

const MAP_STATUS_LABEL = {
  linked:               { tone: "emerald", label: "Linked" },
  needs_review:         { tone: "amber",   label: "Needs Review" },
  former_employee:      { tone: "slate",   label: "Former Employee" },
  ignored:              { tone: "slate",   label: "Ignored" },
  deactivated_unlinked: { tone: "rose",    label: "Deactivated · Unlinked" },
  unmapped:             { tone: "rose",    label: "Unmapped" },
};

function Section({ title, code, icon: Icon, children, testid, accent = "slate" }) {
  const accentCls = {
    slate:   "border-l-slate-400",
    emerald: "border-l-emerald-700",
    indigo:  "border-l-indigo-700",
    amber:   "border-l-amber-600",
    rose:    "border-l-rose-600",
  }[accent] || "border-l-slate-400";
  return (
    <section className={`bg-white border border-slate-200 border-l-4 ${accentCls} rounded-md p-4`} data-testid={testid}>
      <div className="flex items-center gap-2 mb-2">
        <Icon className="w-4 h-4 text-slate-700" />
        <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-700 font-bold">
          {code}
        </span>
      </div>
      <h3 className="font-display text-lg font-black tracking-tight text-slate-900 mb-3">{title}</h3>
      {children}
    </section>
  );
}

function KV({ label, value, mono = false, testid }) {
  return (
    <div className="text-xs" data-testid={testid}>
      <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-slate-500">{label}</div>
      <div className={`text-slate-900 ${mono ? "font-mono" : ""}`}>{value || <span className="text-slate-400 italic">—</span>}</div>
    </div>
  );
}

function CountTile({ label, value, tone = "slate", testid }) {
  const cls = {
    slate:   "bg-white border-slate-200 text-slate-900",
    rose:    "bg-rose-50 border-rose-200 text-rose-900",
    amber:   "bg-amber-50 border-amber-200 text-amber-900",
    emerald: "bg-emerald-50 border-emerald-200 text-emerald-900",
  }[tone] || "bg-white border-slate-200 text-slate-900";
  return (
    <div className={`rounded-md border-2 ${cls} p-3 text-center`} data-testid={testid}>
      <div className="text-2xl font-black leading-none">{value ?? 0}</div>
      <div className="text-[9px] font-mono uppercase tracking-[0.18em] mt-1 opacity-80">{label}</div>
    </div>
  );
}

function IdentitySection({ identity }) {
  if (!identity) return null;
  const statusCls = identity.is_active === false
    ? "bg-rose-100 text-rose-900 border-rose-300"
    : "bg-emerald-100 text-emerald-900 border-emerald-300";
  return (
    <Section title="Identity" code="DCP-1B · IDENTITY" icon={IdCard} accent="indigo" testid="dcp-section-identity">
      <div className="flex items-start gap-4">
        <div className="shrink-0 w-16 h-16 rounded-md bg-slate-100 border border-slate-200 inline-flex items-center justify-center overflow-hidden">
          {identity.photo_url ? (
            <img src={identity.photo_url} alt={identity.name} className="w-full h-full object-cover" />
          ) : (
            <IdCard className="w-7 h-7 text-slate-400" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h2 className="font-display text-xl font-black text-slate-900 tracking-tight" data-testid="dcp-identity-name">
              {identity.name}
            </h2>
            <span className={`inline-flex items-center px-1.5 py-0.5 rounded border text-[10px] font-mono uppercase tracking-wider font-bold ${statusCls}`}>
              {identity.lifecycle_status || (identity.is_active ? "Active" : "Inactive")}
            </span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3">
            <KV label="Employee #" value={identity.employee_id} mono testid="dcp-id-emp" />
            <KV label="Trade" value={identity.trade} testid="dcp-id-trade" />
            <KV label="Role" value={identity.role} testid="dcp-id-role" />
            <KV label="Crew" value={identity.crew} testid="dcp-id-crew" />
            <KV label="Supervisor" value={identity.supervisor_name} testid="dcp-id-supervisor" />
            <KV label="Email" value={identity.email} testid="dcp-id-email" />
            <KV label="Phone" value={identity.phone} testid="dcp-id-phone" />
            <KV label="Hire Date" value={identity.hire_date ? new Date(identity.hire_date).toLocaleDateString() : ""} testid="dcp-id-hire" />
          </div>
        </div>
      </div>
    </Section>
  );
}

function OperationsSection({ operations }) {
  if (!operations) return null;
  const cur = operations.current_assignment;
  const last = operations.last_assignment;
  const loc = operations.last_known_location;
  return (
    <Section title="Operations" code="DCP-1B · OPERATIONS" icon={Truck} accent="emerald" testid="dcp-section-operations">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <div className="bg-slate-50 border border-slate-200 rounded-md p-3" data-testid="dcp-current-assignment">
          <div className="text-[10px] font-mono uppercase tracking-[0.16em] font-bold text-slate-600 mb-1">Current Assignment</div>
          {cur ? (
            <div className="text-xs space-y-1">
              <div className="font-bold text-slate-900">{cur.project_number || "(no project)"} · {cur.material || ""}</div>
              <div className="text-slate-700">{cur.pickup_location || "—"} → {cur.dropoff_location || "—"}</div>
              <div className="text-[10px] font-mono text-slate-500">State: {cur.current_state || "—"} · Truck {cur.truck_id || "—"}</div>
            </div>
          ) : <div className="text-xs text-slate-500 italic">No active assignment.</div>}
        </div>
        <div className="bg-slate-50 border border-slate-200 rounded-md p-3" data-testid="dcp-last-assignment">
          <div className="text-[10px] font-mono uppercase tracking-[0.16em] font-bold text-slate-600 mb-1">Last Assignment</div>
          {last ? (
            <div className="text-xs space-y-1">
              <div className="font-bold text-slate-900">{last.project_number || "(no project)"} · {last.material || ""}</div>
              <div className="text-slate-700">{last.pickup_location || "—"} → {last.dropoff_location || "—"}</div>
              <div className="text-[10px] font-mono text-slate-500">
                Completed: {last.completed_at ? new Date(last.completed_at).toLocaleString() : "—"} · Truck {last.truck_id || "—"}
              </div>
            </div>
          ) : <div className="text-xs text-slate-500 italic">No prior assignments.</div>}
        </div>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3">
        <KV label="Current Vehicle" value={operations.current_vehicle} mono testid="dcp-ops-cur-veh" />
        <KV label="Last Vehicle" value={operations.last_vehicle} mono testid="dcp-ops-last-veh" />
        <KV
          label="Last Motive Activity"
          value={operations.last_motive_activity
            ? `${operations.last_motive_activity.event_family} · ${new Date(operations.last_motive_activity.received_at).toLocaleString()}`
            : null}
          testid="dcp-ops-last-motive"
        />
        <KV
          label="Last Known Location"
          value={loc ? `${loc.city || ""}${loc.city && loc.state ? ", " : ""}${loc.state || ""}${(!loc.city && !loc.state) ? `${loc.lat?.toFixed(3)}, ${loc.lon?.toFixed(3)}` : ""}` : null}
          testid="dcp-ops-last-loc"
        />
      </div>
    </Section>
  );
}

function SafetySection({ safety }) {
  if (!safety) return null;
  return (
    <Section title="Safety" code="DCP-1B · SAFETY" icon={ShieldCheck} accent="rose" testid="dcp-section-safety">
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 mb-3">
        <CountTile testid="dcp-safe-harsh-30d" label="Harsh · 30d" value={safety.harsh_events_30d} tone={safety.harsh_events_30d > 0 ? "amber" : "slate"} />
        <CountTile testid="dcp-safe-hos-30d" label="HOS · 30d" value={safety.hos_violations_30d} tone={safety.hos_violations_30d > 0 ? "rose" : "slate"} />
        <CountTile testid="dcp-safe-dvir-30d" label="DVIR · 30d" value={safety.dvir_inspections_30d} tone="slate" />
        <CountTile testid="dcp-safe-incidents" label="Incidents · 365d" value={(safety.incidents_365d || []).length} tone={(safety.incidents_365d || []).length > 0 ? "rose" : "slate"} />
        <CountTile testid="dcp-safe-open-ca" label="Open CAs" value={(safety.open_corrective_actions || []).length} tone={(safety.open_corrective_actions || []).length > 0 ? "amber" : "slate"} />
      </div>
      {Array.isArray(safety.incidents_365d) && safety.incidents_365d.length > 0 ? (
        <div className="mb-3">
          <div className="text-[10px] font-mono uppercase tracking-[0.16em] font-bold text-slate-600 mb-1">Recent Incidents</div>
          <ul className="bg-rose-50/40 border border-rose-200 rounded-md px-3 py-1 max-h-40 overflow-auto">
            {safety.incidents_365d.slice(0, 6).map((inc) => (
              <li key={inc.id} className="flex items-center gap-2 py-1.5 border-b border-slate-100 last:border-0 text-xs">
                <AlertTriangle className="w-3.5 h-3.5 text-rose-700 shrink-0" />
                <span className="font-mono text-slate-700 shrink-0">{inc.incident_number || inc.id?.slice(0, 6)}</span>
                <span className="text-slate-700 truncate flex-1">{inc.incident_type || "—"} · {inc.location || ""}</span>
                <span className="text-[10px] font-mono text-slate-500 shrink-0">{inc.incident_date}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {Array.isArray(safety.open_corrective_actions) && safety.open_corrective_actions.length > 0 ? (
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.16em] font-bold text-slate-600 mb-1">Open Corrective Actions</div>
          <ul className="bg-amber-50/40 border border-amber-200 rounded-md px-3 py-1 max-h-40 overflow-auto">
            {safety.open_corrective_actions.slice(0, 6).map((ca) => (
              <li key={ca.id} className="flex items-center gap-2 py-1.5 border-b border-slate-100 last:border-0 text-xs">
                <Clock className="w-3.5 h-3.5 text-amber-700 shrink-0" />
                <span className="text-slate-700 truncate flex-1">{ca.title || "—"}</span>
                <span className={`inline-block px-1.5 py-0.5 rounded border text-[10px] font-mono uppercase tracking-wider font-bold ${SEV_PILL[ca.priority || "info"]}`}>{ca.priority || "—"}</span>
                <span className="text-[10px] font-mono text-slate-500 shrink-0">{ca.due_date || ""}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </Section>
  );
}

function TrainingSection({ training }) {
  if (!training) return null;
  const exp = training.expirations || {};
  return (
    <Section title="Training & Certifications" code="DCP-1B · TRAINING" icon={GraduationCap} accent="amber" testid="dcp-section-training">
      <div className="grid grid-cols-3 gap-2 mb-3">
        <CountTile testid="dcp-train-current" label="Current" value={exp.current} tone="emerald" />
        <CountTile testid="dcp-train-expiring" label="Expiring · 30d" value={exp.expiring_30d} tone={exp.expiring_30d > 0 ? "amber" : "slate"} />
        <CountTile testid="dcp-train-expired" label="Expired" value={exp.expired} tone={exp.expired > 0 ? "rose" : "slate"} />
      </div>
      {Array.isArray(training.documents) && training.documents.length > 0 ? (
        <ul className="bg-slate-50 border border-slate-200 rounded-md px-3 py-1 max-h-48 overflow-auto" data-testid="dcp-train-docs">
          {training.documents.slice(0, 12).map((d) => (
            <li key={d.id} className="flex items-center gap-2 py-1.5 border-b border-slate-100 last:border-0 text-xs">
              <GraduationCap className="w-3.5 h-3.5 text-slate-700 shrink-0" />
              <span className="text-slate-700 truncate flex-1">{d.title || d.document_type || "—"}</span>
              <span className="text-[10px] font-mono text-slate-500 shrink-0">exp {d.expiration_date || "—"}</span>
            </li>
          ))}
        </ul>
      ) : (
        <div className="text-xs text-slate-500 italic">No tracked documents.</div>
      )}
    </Section>
  );
}

function EquipmentSection({ equipment_usage }) {
  if (!equipment_usage) return null;
  return (
    <Section title="Equipment Usage" code="DCP-1B · EQUIPMENT" icon={Truck} accent="slate" testid="dcp-section-equipment">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-3">
        <KV label="Most Used" value={equipment_usage.most_used} mono testid="dcp-eq-most-used" />
        <KV label="Last Operated" value={equipment_usage.last_operated} mono testid="dcp-eq-last" />
        <KV
          label="Last Operated At"
          value={equipment_usage.last_operated_at ? new Date(equipment_usage.last_operated_at).toLocaleString() : null}
          testid="dcp-eq-last-at"
        />
      </div>
      {Array.isArray(equipment_usage.timeline) && equipment_usage.timeline.length > 0 ? (
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.16em] font-bold text-slate-600 mb-1">Recent Assignments</div>
          <ul className="bg-slate-50 border border-slate-200 rounded-md px-3 py-1 max-h-48 overflow-auto" data-testid="dcp-eq-timeline">
            {equipment_usage.timeline.map((t) => (
              <li key={t.id} className="flex items-center gap-2 py-1.5 border-b border-slate-100 last:border-0 text-xs">
                <Truck className="w-3.5 h-3.5 text-slate-700 shrink-0" />
                <span className="font-mono text-slate-700 shrink-0">{t.truck_id || "—"}</span>
                <span className="text-slate-700 truncate flex-1">{t.project_number || ""}</span>
                <span className={`inline-block px-1.5 py-0.5 rounded border text-[10px] font-mono uppercase tracking-wider font-bold ${SEV_PILL.low}`}>{t.current_state || "—"}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </Section>
  );
}

function MotiveSection({ motive }) {
  if (!motive) return null;
  const statusCls = motive.driver_status === "active"
    ? "bg-emerald-100 text-emerald-900 border-emerald-300"
    : motive.driver_status === "deactivated"
      ? "bg-amber-100 text-amber-900 border-amber-300"
      : "bg-slate-100 text-slate-700 border-slate-300";
  return (
    <Section title="Motive Telematics" code="DCP-1B · MOTIVE" icon={Activity} accent="slate" testid="dcp-section-motive">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div data-testid="dcp-motive-status">
          <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-slate-500">Driver Status</div>
          <span className={`inline-block px-1.5 py-0.5 rounded border text-[10px] font-mono uppercase tracking-wider font-bold ${statusCls}`}>{motive.driver_status}</span>
        </div>
        <KV label="Driver ID" value={motive.driver_id} mono testid="dcp-motive-id" />
        <KV label="Last Sync" value={motive.last_sync ? new Date(motive.last_sync).toLocaleString() : null} testid="dcp-motive-sync" />
        <KV label="Last GPS Activity" value={motive.located_at ? new Date(motive.located_at).toLocaleString() : null} testid="dcp-motive-located" />
      </div>
    </Section>
  );
}

function MappingHealthSection({ mapping_health }) {
  if (!mapping_health) return null;
  const meta = MAP_STATUS_LABEL[mapping_health.status] || { tone: "slate", label: mapping_health.status };
  const toneCls = {
    emerald: "bg-emerald-100 text-emerald-900 border-emerald-300",
    amber:   "bg-amber-100 text-amber-900 border-amber-300",
    rose:    "bg-rose-100 text-rose-900 border-rose-300",
    slate:   "bg-slate-100 text-slate-700 border-slate-300",
  }[meta.tone] || "bg-slate-100 text-slate-700 border-slate-300";
  return (
    <Section title="Mapping Health" code="DCP-1B · MAPPING (Admin)" icon={ShieldCheck} accent="amber" testid="dcp-section-mapping">
      <div className="flex items-center gap-3 flex-wrap">
        <span className={`inline-flex items-center px-2 py-1 rounded border text-[11px] font-mono uppercase tracking-wider font-bold ${toneCls}`} data-testid="dcp-map-status">
          {meta.label}
        </span>
        {mapping_health.cleanup_status ? (
          <span className="inline-block px-1.5 py-0.5 rounded border text-[10px] font-mono uppercase tracking-wider font-bold bg-slate-50 text-slate-600 border-slate-300">
            cleanup: {mapping_health.cleanup_status}
          </span>
        ) : null}
        {mapping_health.mapping_notes ? (
          <span className="text-[10px] font-mono text-slate-500">{mapping_health.mapping_notes}</span>
        ) : null}
      </div>
    </Section>
  );
}

export default function DriverCommandProfile({ driverKey, className = "" }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  const load = async () => {
    if (!driverKey) return;
    setLoading(true);
    setErr("");
    try {
      const r = await api.get(`/operations/drivers/${encodeURIComponent(driverKey)}/profile`);
      setData(r.data);
    } catch (e) {
      setErr(e?.response?.data?.detail || "Failed to load driver profile");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [driverKey]);

  if (!driverKey) return null;
  if (loading) return (
    <div className="text-center text-slate-500 py-12" data-testid="dcp-loading">
      <Loader2 className="w-5 h-5 inline animate-spin mr-2" /> Loading driver profile…
    </div>
  );
  if (err) return (
    <div className="bg-rose-50 border-2 border-rose-200 rounded-md p-4 text-sm text-rose-800" data-testid="dcp-error">
      <AlertTriangle className="w-4 h-4 inline -mt-0.5 mr-1" /> {err}
    </div>
  );
  if (!data) return null;

  return (
    <div className={`space-y-3 ${className}`} data-testid="dcp-root">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-indigo-700 font-bold">
            DCP-1 · DRIVER COMMAND PROFILE · {String(data._role || "").toUpperCase()} VIEW
          </div>
        </div>
        <button
          type="button"
          onClick={load}
          className="text-[10px] font-mono uppercase tracking-wider text-slate-500 hover:text-slate-800 inline-flex items-center gap-1"
          data-testid="dcp-refresh"
        >
          <RefreshCw className="w-3 h-3" /> Refresh
        </button>
      </div>
      <IdentitySection identity={data.identity} />
      <OperationsSection operations={data.operations} />
      <EquipmentSection equipment_usage={data.equipment_usage} />
      <SafetySection safety={data.safety} />
      <TrainingSection training={data.training} />
      <MotiveSection motive={data.motive} />
      <MappingHealthSection mapping_health={data.mapping_health} />
    </div>
  );
}
