// Unified Asset Profile — read-only aggregator across the company master,
// integrations, dispatch, safety, and operations event log.
import React, { useEffect, useState, useMemo, useCallback } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft, Truck, MapPin, Wrench, ShieldAlert, Activity, Clipboard,
  AlertTriangle, CheckCircle2, Loader2, RefreshCcw, ShieldCheck,
  Pencil, Save, X as XIcon, FileText,
} from "lucide-react";
import AdminShell from "@/components/AdminShell";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toast } from "sonner";
import AssetDocumentsTab from "@/components/asset/AssetDocumentsTab";
import { formatEmployeeIdentity } from "@/lib/identity";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

const STATUS_PILL = {
  Available:         "bg-emerald-100 text-emerald-900 border-emerald-300",
  Assigned:          "bg-blue-100 text-blue-900 border-blue-300",
  "In Transit":      "bg-violet-100 text-violet-900 border-violet-300",
  "Pending Transfer":"bg-cyan-100 text-cyan-900 border-cyan-300",
  "Safety Hold":     "bg-red-100 text-red-900 border-red-300",
  "Maintenance Hold":"bg-amber-100 text-amber-900 border-amber-300",
  Down:              "bg-slate-300 text-slate-900 border-slate-400",
  Unknown:           "bg-slate-200 text-slate-700 border-slate-300",
};

export default function AssetProfile() {
  const { assetId } = useParams();
  const nav = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("overview");

  const load = async () => {
    setLoading(true);
    try {
      const r = await api.get(`/operations/assets/${assetId}/profile`);
      setData(r.data);
    } catch (e) {
      setData({ error: e?.response?.data?.detail || "Failed to load asset" });
    } finally { setLoading(false); }
  };
  useEffect(() => { load();   }, [assetId]);

  if (loading) return (
    <AdminShell title="Asset Profile">
      <div className="text-center text-slate-500 py-12"><Loader2 className="w-6 h-6 animate-spin mx-auto" /></div>
    </AdminShell>
  );
  if (!data || data.error) return (
    <AdminShell title="Asset Profile">
      <div className="text-center text-red-700 py-12">{data?.error || "Asset not found"}</div>
    </AdminShell>
  );

  const overview = data.overview || {};
  const statusCls = STATUS_PILL[data.current_status] || STATUS_PILL.Unknown;

  return (
    <AdminShell title="Asset Profile">
      <div className="max-w-6xl mx-auto" data-testid="asset-profile-page">
        <div className="flex items-center justify-between gap-3 mb-4">
          <Button variant="outline" size="sm" onClick={() => nav(-1)} data-testid="asset-profile-back">
            <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Back
          </Button>
          <Button variant="outline" size="sm" onClick={load}>
            <RefreshCcw className="w-3.5 h-3.5 mr-1" /> Refresh
          </Button>
        </div>

        {/* Hero */}
        <div className="bg-white border border-slate-200 rounded-md p-5 mb-4">
          <div className="flex items-start gap-4 flex-wrap">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-md bg-slate-900 text-white shrink-0">
              <Truck className="w-7 h-7" />
            </div>
            <div className="flex-1 min-w-0">
              <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">
                Unified asset profile · iter124
              </span>
              <h1 className="font-display text-2xl sm:text-3xl font-black tracking-tight" data-testid="asset-profile-name">
                {overview.unit_number || "—"} <span className="text-slate-500 font-normal">— {overview.name || "(unnamed)"}</span>
              </h1>
              <div className="text-sm text-slate-700 mt-1">
                {overview.equipment_type || "—"} · {overview.make || ""} {overview.model || ""}{overview.year ? ` · ${overview.year}` : ""}
              </div>
            </div>
            <span
              className={`px-3 py-1.5 rounded-md border-2 font-mono text-xs uppercase tracking-[0.18em] font-bold ${statusCls}`}
              data-testid="asset-profile-status"
            >
              {data.current_status}
            </span>
          </div>
        </div>

        <Tabs value={tab} onValueChange={setTab}>
          <TabsList className="flex-wrap h-auto">
            <TabsTrigger value="overview" data-testid="ap-tab-overview"><Clipboard className="w-3.5 h-3.5 mr-1" /> Overview</TabsTrigger>
            <TabsTrigger value="dispatch" data-testid="ap-tab-dispatch"><Truck className="w-3.5 h-3.5 mr-1" /> Dispatch</TabsTrigger>
            <TabsTrigger value="motive" data-testid="ap-tab-motive"><MapPin className="w-3.5 h-3.5 mr-1" /> Motive</TabsTrigger>
            <TabsTrigger value="maintainx" data-testid="ap-tab-maintainx"><Wrench className="w-3.5 h-3.5 mr-1" /> MaintainX</TabsTrigger>
            <TabsTrigger value="safety" data-testid="ap-tab-safety"><ShieldAlert className="w-3.5 h-3.5 mr-1" /> Safety</TabsTrigger>
            <TabsTrigger value="field" data-testid="ap-tab-field"><Clipboard className="w-3.5 h-3.5 mr-1" /> Field Ops</TabsTrigger>
            <TabsTrigger value="events" data-testid="ap-tab-events"><Activity className="w-3.5 h-3.5 mr-1" /> Events</TabsTrigger>
            <TabsTrigger value="admin" data-testid="ap-tab-admin"><ShieldCheck className="w-3.5 h-3.5 mr-1" /> Admin</TabsTrigger>
            <TabsTrigger value="documents" data-testid="ap-tab-documents"><FileText className="w-3.5 h-3.5 mr-1" /> Documents</TabsTrigger>
          </TabsList>

          <TabsContent value="overview"><OverviewSection overview={overview} /></TabsContent>
          <TabsContent value="dispatch"><DispatchSection data={data} /></TabsContent>
          <TabsContent value="motive"><MotiveLiveTab live={data.motive_live} mapping={data.mapping} operator={data.current_operator} /></TabsContent>
          <TabsContent value="maintainx"><MaintainXPlaceholder mapping={data.mapping} /></TabsContent>
          <TabsContent value="safety"><SafetySection data={data} /></TabsContent>
          <TabsContent value="field"><FieldOpsSection data={data} /></TabsContent>
          <TabsContent value="events"><EventsSection data={data} /></TabsContent>
          <TabsContent value="admin"><AdminSection assetId={assetId} /></TabsContent>
          <TabsContent value="documents">
            <AssetDocumentsTab assetId={assetId} unitNumber={data.unit_number || data.display_label} />
          </TabsContent>
        </Tabs>
      </div>
    </AdminShell>
  );
}

function Field({ label, value }) {
  return (
    <div>
      <div className="font-mono text-[9px] uppercase tracking-[0.18em] text-slate-500 font-bold">{label}</div>
      <div className="text-sm font-bold text-slate-900 mt-0.5 break-words">{value || <span className="text-slate-400 font-normal">—</span>}</div>
    </div>
  );
}

function OverviewSection({ overview }) {
  return (
    <div className="bg-white border border-slate-200 rounded-md p-5 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4" data-testid="ap-overview">
      <Field label="Asset ID"      value={overview.id} />
      <Field label="Unit #"        value={overview.unit_number} />
      <Field label="Name"          value={overview.name} />
      <Field label="Type"          value={overview.equipment_type} />
      <Field label="Make"          value={overview.make} />
      <Field label="Model"         value={overview.model} />
      <Field label="Year"          value={overview.year} />
      <Field label="VIN"           value={overview.vin} />
      <Field label="Serial #"      value={overview.serial_number} />
      <Field label="License Plate" value={overview.license_plate} />
      <Field label="Department"    value={overview.department} />
      <Field label="Active"        value={overview.active === false ? "No" : "Yes"} />
    </div>
  );
}

function DispatchSection({ data }) {
  const a = data.active_assignment;
  const p = data.pending_transfer;
  const t = data.in_transit;
  const transfers = data.transfers || [];
  return (
    <div className="space-y-4" data-testid="ap-dispatch">
      <div className="bg-white border border-slate-200 rounded-md p-5">
        <h3 className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold mb-2">Current Assignment</h3>
        {a ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3">
            <Field label="Project #"        value={a.project_number} />
            <Field label="Project Name"     value={a.project_name} />
            <Field label="Operator"         value={formatEmployeeIdentity(a) || a.operator_name} />
            <Field label="Started"          value={(a.started_at || "").slice(0,16).replace("T"," ")} />
            <Field label="Expected return"  value={a.expected_return_date} />
            <Field label="Notes"            value={a.dispatch_notes} />
          </div>
        ) : <p className="text-sm text-slate-500 italic">No active assignment.</p>}
      </div>
      {(p || t) && (
        <div className="bg-cyan-50 border-2 border-cyan-300 rounded-md p-5">
          <h3 className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-900 font-bold mb-2">{t ? "In Transit" : "Pending Transfer"}</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3">
            <Field label="From" value={(t || p).from_project_number} />
            <Field label="To"   value={(t || p).to_project_number} />
            <Field label="Need" value={(t || p).need_date} />
            <Field label="Status" value={(t || p).status} />
          </div>
        </div>
      )}
      <div className="bg-white border border-slate-200 rounded-md p-5">
        <h3 className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold mb-2">Transfer history</h3>
        {transfers.length === 0 ? <p className="text-sm text-slate-500 italic">No transfers recorded.</p> : (
          <ul className="divide-y divide-slate-100 text-xs" data-testid="ap-transfer-history">
            {transfers.map((x) => (
              <li key={x.id} className="py-2 flex items-center gap-3 flex-wrap">
                <span className="font-mono text-slate-500 w-32 shrink-0">{(x.created_at || "").slice(0,16).replace("T"," ")}</span>
                <span className="font-mono text-slate-700 w-24 shrink-0">{x.status}</span>
                <span className="text-slate-700">{x.from_project_number || "—"} → {x.to_project_number || "—"}</span>
                <span className="text-slate-500 ml-auto truncate max-w-xs">{x.reason || ""}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function PlaceholderCard({ icon: Icon, title, sub, fields }) {
  return (
    <div className="bg-white border-2 border-dashed border-slate-300 rounded-md p-5">
      <div className="flex items-start gap-3 mb-3">
        <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-slate-200 text-slate-700 shrink-0">
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">{sub}</div>
          <h3 className="font-display text-lg font-black mt-0.5 leading-tight">{title}</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-md">
            Awaiting integration. This section will populate once Admin connects the provider in the Integration Center.
          </p>
        </div>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-x-8 gap-y-4 text-xs">
        {fields.map((f) => (<div key={f}><div className="font-mono text-[9px] uppercase tracking-[0.18em] text-slate-400 font-bold">{f}</div><div className="text-slate-400 italic">—</div></div>))}
      </div>
    </div>
  );
}

function MotiveLiveTab({ live, mapping, operator }) {
  // P1-D · Replaces the legacy "Awaiting integration" placeholder
  // with the real telemetry data already in `asset_mappings.motive.*`.
  // P1-C · Renders source-attributed current operator.
  if (!live || live.status === "not_mapped") {
    return (
      <div className="space-y-3" data-testid="ap-motive">
        <div className="bg-amber-50 border border-amber-300 rounded-md p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-700 shrink-0" />
          <div>
            <div className="font-display font-black text-sm text-amber-900">No Motive mapping</div>
            <p className="text-xs text-amber-800 mt-1">This company equipment record is not yet linked to a Motive vehicle or Asset Gateway unit. Use Admin → Integration Center → Auto-Link or Mappings to connect it.</p>
          </div>
        </div>
      </div>
    );
  }

  const isLive = live.status === "live";
  const sb = live.staleness?.bucket || "offline";
  // OIS-1F · Universal GPS health colors (Green = Reporting, Amber = Stale, Red = Not Reporting)
  const STALE_PILL = {
    fresh:   "bg-emerald-100 text-emerald-900 border-emerald-300",
    stale:   "bg-amber-100 text-amber-900 border-amber-300",
    offline: "bg-rose-100 text-rose-900 border-rose-300",
  };
  const STALE_LABEL = {
    fresh: "Reporting",
    stale: "Stale",
    offline: "Not Reporting",
  };
  const cls = STALE_PILL[sb] || STALE_PILL.offline;
  const mins = live.staleness?.minutes;
  const sinceLabel = mins == null ? "never" : (mins < 60 ? `${mins} min ago` : `${Math.round(mins/60)} h ago`);

  return (
    <div className="space-y-3" data-testid="ap-motive">
      {/* Header banner */}
      <div className="bg-white border-2 border-slate-700 rounded-md p-4 flex items-start gap-3">
        <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-slate-900 text-white shrink-0">
          <MapPin className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">Motive · Live Telematics</span>
            <span className={`px-1.5 py-0.5 rounded border text-[10px] font-mono uppercase tracking-[0.15em] font-bold ${cls}`} data-testid="ap-motive-stale-badge">
              {STALE_LABEL[sb] || STALE_LABEL.offline} · {sinceLabel}
            </span>
            {!live.gps_enabled && (
              <span className="px-1.5 py-0.5 rounded bg-slate-200 text-slate-700 border border-slate-300 text-[10px] font-mono uppercase tracking-[0.15em] font-bold">No GPS</span>
            )}
          </div>
          <h3 className="font-display text-lg font-black mt-0.5 leading-tight" data-testid="ap-motive-title">
            {live.fleet_number || live.vehicle_id || live.asset_id}
          </h3>
          <div className="text-xs text-slate-500 mt-0.5">
            {[live.year, live.make, live.model].filter(Boolean).join(" ").trim() || "—"}
            {live.vin ? <> · <span className="font-mono">VIN {live.vin}</span></> : null}
          </div>
        </div>
      </div>

      {/* Operator card */}
      <OperatorCard operator={operator} />

      {/* Live telemetry grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3" data-testid="ap-motive-grid">
        <Tile label="Last GPS" testid="ap-motive-gps" value={
          live.lat != null && live.lon != null
            ? <span className="font-mono">{live.lat.toFixed(5)}, {live.lon.toFixed(5)}</span>
            : null
        } />
        <Tile label="City / State" testid="ap-motive-city" value={[live.city, live.state].filter(Boolean).join(", ")} />
        <Tile label="Last Seen" testid="ap-motive-located" value={live.located_at ? formatPlatformTime(live.located_at) : null} />
        <Tile label="Speed" testid="ap-motive-speed" value={
          live.speed_mph != null
            ? `${live.speed_mph} mph${live.moving ? " · Moving" : " · Parked"}`
            : (live.speed_kph != null ? `${Math.round(live.speed_kph)} kph` : null)
        } />
        <Tile label="External Type" testid="ap-motive-kind" value={live.external_kind === "vehicle" ? "Vehicle (ELD)" : "Asset Gateway"} />
        <Tile label="Motive ID" testid="ap-motive-id" value={<span className="font-mono">{live.vehicle_id || live.asset_id}</span>} />
        <Tile label="GPS Enabled" testid="ap-motive-gpsflag" value={live.gps_enabled ? "Yes" : "No"} />
        <Tile label="Dashcam" testid="ap-motive-dashcam" value={live.dashcam_enabled ? "Yes" : "No"} />
        <Tile label="Mapping" testid="ap-motive-mapped" value={mapping?.masci_equipment_id ? "Linked" : "Unlinked"} />
      </div>

      {/* Source footer */}
      <div className="text-[10px] font-mono text-slate-400 uppercase tracking-[0.18em]">
        Source: Motive sync · `asset_mappings.motive.*` · live polling + signed webhooks
      </div>
    </div>
  );
}

function OperatorCard({ operator }) {
  const has = operator && operator.name;
  return (
    <div className="bg-white border border-slate-200 rounded-md p-4 flex items-start gap-3" data-testid="ap-motive-operator">
      <div className="inline-flex items-center justify-center w-9 h-9 rounded-md bg-slate-100 text-slate-700 shrink-0">
        <Truck className="w-4 h-4" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">Current Driver / Operator</div>
        <div className="font-display text-base font-black mt-0.5" data-testid="ap-motive-operator-name">{has ? operator.name : <span className="text-slate-400 font-normal">Unknown</span>}</div>
        {has && (
          <div className="text-[11px] text-slate-500 mt-0.5">
            <span className="font-mono uppercase tracking-[0.15em]">Source:</span> {operator.source_label || operator.source}
            {operator.as_of ? <> · <span className="font-mono">{formatPlatformTime(operator.as_of)}</span></> : null}
          </div>
        )}
      </div>
    </div>
  );
}

function Tile({ label, value, testid }) {
  return (
    <div className="bg-white border border-slate-200 rounded-md p-3" data-testid={testid}>
      <div className="font-mono text-[9px] uppercase tracking-[0.18em] text-slate-500 font-bold">{label}</div>
      <div className="text-sm font-bold text-slate-900 mt-0.5 break-words">
        {value || <span className="text-slate-400 font-normal italic">—</span>}
      </div>
    </div>
  );
}

function MotivePlaceholder({ mapping }) {
  const ext = mapping?.motive?.vehicle_id;
  return (
    <div className="space-y-3" data-testid="ap-motive">
      {ext && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-md p-3 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-700" />
          <span className="font-mono">Mapped to Motive Vehicle ID: <strong>{ext}</strong></span>
        </div>
      )}
      <PlaceholderCard
        icon={MapPin}
        sub="Motive · Telematics & telemetry"
        title="Awaiting Motive integration"
        fields={["Vehicle ID", "Last GPS", "Last seen", "Driver", "Ignition", "Idle time", "Movement", "Odometer", "Engine hours"]}
      />
    </div>
  );
}

function MaintainXPlaceholder({ mapping }) {
  const ext = mapping?.maintainx?.asset_id;
  return (
    <div className="space-y-3" data-testid="ap-maintainx">
      {ext && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-md p-3 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-700" />
          <span className="font-mono">Mapped to MaintainX Asset ID: <strong>{ext}</strong></span>
        </div>
      )}
      <PlaceholderCard
        icon={Wrench}
        sub="MaintainX · Maintenance & repairs"
        title="Awaiting MaintainX integration"
        fields={["Asset ID", "Open WOs", "Closed WOs", "PM schedule", "Overdue PMs", "Technician", "Repair notes", "Downtime", "Status"]}
      />
    </div>
  );
}

function SafetySection({ data }) {
  const holds = (data.active_holds || []).filter((h) => h.kind === "safety");
  const cas = data.safety_corrective_actions || [];
  return (
    <div className="space-y-4" data-testid="ap-safety">
      <div className="bg-white border border-slate-200 rounded-md p-5">
        <h3 className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold mb-2">Active safety holds</h3>
        {holds.length === 0 ? <p className="text-sm text-slate-500 italic">No active safety holds.</p> : (
          <ul className="divide-y divide-slate-100 text-xs">
            {holds.map((h) => (
              <li key={h.id} className="py-2"><strong>{h.reason}</strong> <span className="text-slate-500">· {(h.created_at || "").slice(0,10)} · severity {h.severity}</span></li>
            ))}
          </ul>
        )}
      </div>
      <div className="bg-white border border-slate-200 rounded-md p-5">
        <h3 className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold mb-2">Linked corrective actions</h3>
        {cas.length === 0 ? <p className="text-sm text-slate-500 italic">No corrective actions linked to this asset.</p> : (
          <ul className="divide-y divide-slate-100 text-xs">
            {cas.map((c) => (<li key={c.id || c.action_id} className="py-2">{c.title || c.summary || c.id}</li>))}
          </ul>
        )}
      </div>
    </div>
  );
}

function FieldOpsSection({ data }) {
  const preops = data.recent_preops || [];
  return (
    <div className="bg-white border border-slate-200 rounded-md p-5" data-testid="ap-field">
      <h3 className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold mb-2">Recent pre-ops / inspections</h3>
      {preops.length === 0 ? <p className="text-sm text-slate-500 italic">No pre-op records linked.</p> : (
        <ul className="divide-y divide-slate-100 text-xs">
          {preops.map((p, i) => (
            <li key={p.id || i} className="py-2 flex items-center gap-3 flex-wrap">
              <span className="font-mono text-slate-500 w-32 shrink-0">{(p.created_at || p.date || "").slice(0,16).replace("T"," ")}</span>
              <span className="text-slate-700">{p.status || p.result || "—"}</span>
              <span className="text-slate-500 truncate max-w-xs">{p.notes || ""}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function EventsSection({ data }) {
  const events = data.events || [];
  const motiveEvents = data.motive_events || [];
  return (
    <div className="space-y-4" data-testid="ap-events">
      {/* P1.5-H · Motive event timeline (read-only) */}
      <div className="bg-white border border-slate-200 rounded-md p-5" data-testid="ap-motive-events">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">Motive event timeline</h3>
          <span className="text-xs text-slate-500">Last {motiveEvents.length} signed events</span>
        </div>
        {motiveEvents.length === 0 ? (
          <p className="text-sm text-slate-500 italic">No Motive events recorded for this asset.</p>
        ) : (
          <ul className="divide-y divide-slate-100 text-xs" data-testid="ap-motive-events-list">
            {motiveEvents.map((e) => (
              <li key={e.id} className="py-2 flex items-start gap-3" data-testid={`ap-motive-event-${e.id}`}>
                <span className="font-mono text-slate-500 w-32 shrink-0">{(e.event_at || e.received_at || "").slice(0, 16).replace("T", " ")}</span>
                <MotiveFamilyChip family={e.event_family} severity={e.severity} />
                <span className="font-bold text-slate-900 truncate flex-1">{motiveSummary(e)}</span>
                {e.source === "webhook" && <span className="text-[9px] uppercase tracking-[0.15em] font-mono font-bold text-emerald-700 px-1.5 py-0.5 bg-emerald-50 border border-emerald-200 rounded">Live</span>}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="bg-white border border-slate-200 rounded-md p-5">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">Operations events</h3>
          <span className="text-xs text-slate-500">Showing {events.length} of {data.events_total_for_asset}</span>
        </div>
        {events.length === 0 ? <p className="text-sm text-slate-500 italic">No events recorded for this asset.</p> : (
          <ul className="divide-y divide-slate-100 text-xs">
            {events.map((e) => (
              <li key={e.id} className="py-2 flex items-start gap-3" data-testid={`ap-event-row-${e.id}`}>
                <span className="font-mono text-slate-500 w-32 shrink-0">{(e.created_at || "").slice(0, 16).replace("T", " ")}</span>
                <span className="font-mono text-slate-700 w-44 shrink-0 truncate">{e.event_type}</span>
                <span className="font-bold text-slate-900 truncate">{e.event_title}</span>
                <span className="ml-auto text-[9px] uppercase tracking-[0.15em] font-mono font-bold text-slate-500">{e.severity} · {e.status}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function motiveSummary(e) {
  // Fall back to a constructed sentence if the backend `summary` field
  // isn't populated for an older row.
  if (e.summary) return e.summary;
  const fam = e.event_family || e.event_kind || "event";
  const unit = e.unit_number || e.vehicle_id || "vehicle";
  if (fam === "geofence_enter") return `${unit} arrived at ${e.geofence?.name || "geofence"}`;
  if (fam === "geofence_exit") return `${unit} departed ${e.geofence?.name || "geofence"}`;
  if (fam === "harsh_event") return `${(e.harsh?.subtype || "Harsh event").replace(/_/g, " ")} on ${unit}`;
  if (fam === "fault_code") return `Fault ${e.fault?.dtc_code || ""} on ${unit}`;
  if (fam === "dvir") return e.dvir?.out_of_service ? `OUT OF SERVICE: ${unit}` : `DVIR: ${unit}`;
  return `${fam} · ${unit}`;
}

const FAMILY_PILL = {
  harsh_event:           "bg-red-100 text-red-900 border-red-300",
  fault_code:            "bg-amber-100 text-amber-900 border-amber-300",
  fault_code_closed:     "bg-emerald-100 text-emerald-900 border-emerald-300",
  dvir:                  "bg-purple-100 text-purple-900 border-purple-300",
  geofence_enter:        "bg-emerald-100 text-emerald-900 border-emerald-300",
  geofence_exit:         "bg-blue-100 text-blue-900 border-blue-300",
  asset_geofence_enter:  "bg-teal-100 text-teal-900 border-teal-300",
  asset_geofence_exit:   "bg-cyan-100 text-cyan-900 border-cyan-300",
  hos_violation:         "bg-red-200 text-red-950 border-red-400",
  gateway_disconnected:  "bg-orange-100 text-orange-900 border-orange-300",
  gateway_reconnected:   "bg-slate-100 text-slate-700 border-slate-300",
  ai_coach_recap:        "bg-indigo-100 text-indigo-900 border-indigo-300",
  vehicle_gps:           "bg-slate-100 text-slate-700 border-slate-300",
};
const FAMILY_LABEL = {
  harsh_event:          "SAFETY",
  fault_code:           "SHOP",
  fault_code_closed:    "RESOLVED",
  dvir:                 "DVIR",
  geofence_enter:       "ARRIVED",
  geofence_exit:        "DEPARTED",
  asset_geofence_enter: "ASSET IN",
  asset_geofence_exit:  "ASSET OUT",
  hos_violation:        "HOS",
  gateway_disconnected: "OFFLINE",
  gateway_reconnected:  "RESTORED",
  ai_coach_recap:       "AI COACH",
  vehicle_gps:          "GPS",
};

function MotiveFamilyChip({ family, severity }) {
  const cls = FAMILY_PILL[family] || "bg-slate-100 text-slate-700 border-slate-300";
  const lbl = FAMILY_LABEL[family] || (family || "event").toUpperCase();
  return (
    <span className={`px-1.5 py-0.5 rounded border font-mono text-[9px] uppercase tracking-[0.15em] font-bold w-24 text-center shrink-0 ${cls}`} data-testid={`ap-motive-chip-${family}`}>
      {lbl}{severity && severity !== "info" ? ` · ${severity.toUpperCase()}` : ""}
    </span>
  );
}


// ─────────────────────────────────────────────────────────────────────
// Track 13.31B Day-2 · Asset Administration tab
//
// Reads the canonical record from /api/asset-spine/assets/{id}, hydrates
// the closed-set taxonomy from /api/asset-spine/taxonomy, and exposes
// edit-and-save for the 13 administrative fields + canonical taxonomy.
// PATCH lands on /api/asset-spine/assets/{id} (admin-gated). Read works
// for any portal token.
// ─────────────────────────────────────────────────────────────────────

const LIFECYCLE_OPTIONS = [
  "active", "inactive", "pending_delivery", "sold", "retired", "disposed",
];

const TITLE_OPTIONS = [
  "owned_clear", "owned_lien", "leased", "rented", "loaned", "in_transit",
];

function LifecyclePill({ value }) {
  if (!value) return <span className="text-slate-400 font-normal italic">—</span>;
  const cls = {
    active:            "bg-emerald-100 text-emerald-900 border-emerald-300",
    inactive:          "bg-slate-200 text-slate-800 border-slate-300",
    pending_delivery:  "bg-amber-100 text-amber-900 border-amber-300",
    sold:              "bg-violet-100 text-violet-900 border-violet-300",
    retired:           "bg-slate-300 text-slate-900 border-slate-400",
    disposed:          "bg-red-100 text-red-900 border-red-300",
  }[value] || "bg-slate-100 text-slate-700 border-slate-300";
  return (
    <span className={`px-1.5 py-0.5 rounded border font-mono text-[10px] uppercase tracking-[0.15em] font-bold ${cls}`}>
      {String(value).replace(/_/g, " ")}
    </span>
  );
}

function TaxonomyChip({ verified, source }) {
  const isVerified = verified === true;
  const cls = isVerified
    ? "bg-emerald-100 text-emerald-900 border-emerald-300"
    : "bg-amber-100 text-amber-900 border-amber-300";
  const lbl = isVerified
    ? `VERIFIED · ${(source || "manual").toUpperCase()}`
    : `NEEDS REVIEW${source ? ` · ${source.toUpperCase()}` : ""}`;
  return (
    <span
      className={`px-1.5 py-0.5 rounded border font-mono text-[10px] uppercase tracking-[0.15em] font-bold ${cls}`}
      data-testid="ap-admin-taxonomy-chip"
    >
      {lbl}
    </span>
  );
}

function AdminSection({ assetId }) {
  const [asset, setAsset] = useState(null);
  const [taxonomy, setTaxonomy] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({});
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setErr(null);
    try {
      const [a, t] = await Promise.all([
        api.get(`/asset-spine/assets/${assetId}`),
        api.get(`/asset-spine/taxonomy`),
      ]);
      setAsset(a.data);
      setTaxonomy(t.data);
    } catch (e) {
      setErr(e?.response?.data?.detail || e?.message || "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [assetId]);

  // Initial fetch — inline to satisfy react-hooks/set-state-in-effect.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [a, t] = await Promise.all([
          api.get(`/asset-spine/assets/${assetId}`),
          api.get(`/asset-spine/taxonomy`),
        ]);
        if (cancelled) return;
        setAsset(a.data);
        setTaxonomy(t.data);
      } catch (e) {
        if (cancelled) return;
        setErr(e?.response?.data?.detail || e?.message || "Failed to load");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [assetId]);

  const startEdit = () => {
    if (!asset) return;
    setForm({
      // Canonical taxonomy
      asset_class: asset.asset_class || "",
      asset_type:  asset.asset_type  || "",
      asset_subtype: asset.asset_subtype || "",
      taxonomy_verified: asset.taxonomy_verified === true,
      // Lifecycle & ownership
      lifecycle_status: asset.lifecycle_status || "",
      title_status:     asset.title_status || "",
      warranty_expiration: asset.warranty_expiration || "",
      // Registration
      registration_number:     asset.registration_number || "",
      registration_state:      asset.registration_state || "",
      registration_expiration: asset.registration_expiration || "",
      // Insurance
      insurance_carrier:        asset.insurance_carrier || "",
      insurance_policy_number:  asset.insurance_policy_number || "",
      insurance_expiration:     asset.insurance_expiration || "",
      // Org
      division:           asset.division || "",
      region:             asset.region || "",
      supervisor_id:      asset.supervisor_id || "",
      normalized_company: asset.normalized_company || "",
      // Devices / external IDs
      vin:                  asset.vin || "",
      license_plate:        asset.license_plate || "",
      gps_device_id:        asset.gps_device_id || "",
      motive_vehicle_id:    asset.motive_vehicle_id || "",
      maintainx_asset_id:   asset.maintainx_asset_id || "",
      fleetwatcher_asset_id: asset.fleetwatcher_asset_id || "",
    });
    setEditing(true);
  };

  const cancelEdit = () => { setEditing(false); setForm({}); };

  const save = async () => {
    setSaving(true);
    try {
      const payload = {};
      Object.entries(form).forEach(([k, v]) => {
        if (v === "" || v === null || v === undefined) return;
        payload[k] = v;
      });
      // Force boolean
      payload.taxonomy_verified = !!form.taxonomy_verified;
      // If admin manually verifies, mark source manual.
      if (payload.taxonomy_verified && !payload.taxonomy_source) {
        payload.taxonomy_source = "manual";
      }
      const r = await api.patch(`/asset-spine/assets/${assetId}`, payload);
      setAsset(r.data);
      setEditing(false);
      toast.success("Asset administration saved");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Save failed");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center text-slate-500 py-12" data-testid="ap-admin-loading">
        <Loader2 className="w-6 h-6 animate-spin mx-auto" />
      </div>
    );
  }
  if (err) {
    return (
      <div className="px-4 py-3 rounded border-2 border-red-300 bg-red-50 text-sm text-red-900 font-semibold" data-testid="ap-admin-err">
        {err}
      </div>
    );
  }
  if (!asset) return null;

  const validTypes = taxonomy?.asset_types_by_class?.[editing ? form.asset_class : asset.asset_class] || [];
  const behavior = (taxonomy?.behaviors || {})[editing ? form.asset_type : asset.asset_type] || null;

  return (
    <div className="space-y-4" data-testid="ap-admin">
      {/* Action bar */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2 flex-wrap">
          <TaxonomyChip verified={asset.taxonomy_verified} source={asset.taxonomy_source} />
          <LifecyclePill value={asset.lifecycle_status} />
          {asset.asset_category_version && (
            <span className="px-1.5 py-0.5 rounded border bg-slate-100 text-slate-700 border-slate-300 font-mono text-[10px] uppercase tracking-[0.15em] font-bold">
              spine v{asset.asset_category_version}
            </span>
          )}
        </div>
        {!editing ? (
          <Button
            size="sm"
            onClick={startEdit}
            data-testid="ap-admin-edit"
            className="bg-slate-900 hover:bg-black text-white"
          >
            <Pencil className="w-3.5 h-3.5 mr-1" /> Edit
          </Button>
        ) : (
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={cancelEdit} disabled={saving} data-testid="ap-admin-cancel">
              <XIcon className="w-3.5 h-3.5 mr-1" /> Cancel
            </Button>
            <Button
              size="sm"
              onClick={save}
              disabled={saving}
              data-testid="ap-admin-save"
              className="bg-red-700 hover:bg-red-800 text-white"
            >
              {saving ? <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" /> : <Save className="w-3.5 h-3.5 mr-1" />}
              Save
            </Button>
          </div>
        )}
      </div>

      {/* Canonical Taxonomy */}
      <AdminCard title="Canonical Taxonomy" subtitle="Single source of truth · spine v1.0.0">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <SelectOrField
            label="Asset Class"
            editing={editing}
            value={editing ? form.asset_class : asset.asset_class}
            options={taxonomy?.asset_classes || []}
            onChange={(v) => setForm((f) => ({ ...f, asset_class: v, asset_type: "" }))}
            testid="ap-admin-asset-class"
          />
          <SelectOrField
            label="Asset Type"
            editing={editing}
            value={editing ? form.asset_type : asset.asset_type}
            options={validTypes}
            onChange={(v) => setForm((f) => ({ ...f, asset_type: v }))}
            testid="ap-admin-asset-type"
            disabled={editing && !form.asset_class}
          />
          <InputOrField
            label="Asset Subtype (optional)"
            editing={editing}
            value={editing ? form.asset_subtype : asset.asset_subtype}
            onChange={(v) => setForm((f) => ({ ...f, asset_subtype: v }))}
            testid="ap-admin-asset-subtype"
          />
        </div>
        {editing && (
          <label className="flex items-center gap-2 mt-3 text-sm text-slate-700" data-testid="ap-admin-verified-row">
            <input
              type="checkbox"
              checked={!!form.taxonomy_verified}
              onChange={(e) => setForm((f) => ({ ...f, taxonomy_verified: e.target.checked }))}
              className="rounded border-slate-300"
              data-testid="ap-admin-verified-checkbox"
            />
            <span>Mark canonical taxonomy as <strong>verified</strong> (source: manual)</span>
          </label>
        )}
        {behavior && (
          <div className="mt-3 pt-3 border-t border-slate-100" data-testid="ap-admin-behavior">
            <div className="font-mono text-[9px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-1.5">Inherited behavior</div>
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(behavior)
                .filter(([, v]) => v === true)
                .map(([k]) => (
                  <span key={k} className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200 font-mono text-[10px] uppercase tracking-[0.15em] font-bold">
                    {k.replace(/_/g, " ")}
                  </span>
                ))}
            </div>
          </div>
        )}
        {(asset.legacy_category || asset.legacy_type || asset.legacy_preop_equipment_type) && (
          <div className="mt-3 pt-3 border-t border-slate-100 text-xs text-slate-500 font-mono" data-testid="ap-admin-legacy">
            legacy · category=&quot;{asset.legacy_category || "—"}&quot; · type=&quot;{asset.legacy_type || "—"}&quot; · preop=&quot;{asset.legacy_preop_equipment_type || "—"}&quot;
          </div>
        )}
      </AdminCard>

      {/* Lifecycle & Title */}
      <AdminCard title="Lifecycle & Title">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <SelectOrField
            label="Lifecycle Status"
            editing={editing}
            value={editing ? form.lifecycle_status : asset.lifecycle_status}
            options={LIFECYCLE_OPTIONS}
            onChange={(v) => setForm((f) => ({ ...f, lifecycle_status: v }))}
            testid="ap-admin-lifecycle"
          />
          <SelectOrField
            label="Title Status"
            editing={editing}
            value={editing ? form.title_status : asset.title_status}
            options={TITLE_OPTIONS}
            onChange={(v) => setForm((f) => ({ ...f, title_status: v }))}
            testid="ap-admin-title"
          />
          <InputOrField
            label="Warranty Expiration"
            editing={editing}
            value={editing ? form.warranty_expiration : asset.warranty_expiration}
            type="date"
            onChange={(v) => setForm((f) => ({ ...f, warranty_expiration: v }))}
            testid="ap-admin-warranty"
          />
        </div>
      </AdminCard>

      {/* Registration */}
      <AdminCard title="Registration">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <InputOrField
            label="Registration #"
            editing={editing}
            value={editing ? form.registration_number : asset.registration_number}
            onChange={(v) => setForm((f) => ({ ...f, registration_number: v }))}
            testid="ap-admin-reg-number"
          />
          <InputOrField
            label="State"
            editing={editing}
            value={editing ? form.registration_state : asset.registration_state}
            onChange={(v) => setForm((f) => ({ ...f, registration_state: v }))}
            testid="ap-admin-reg-state"
          />
          <InputOrField
            label="Expiration"
            editing={editing}
            value={editing ? form.registration_expiration : asset.registration_expiration}
            type="date"
            onChange={(v) => setForm((f) => ({ ...f, registration_expiration: v }))}
            testid="ap-admin-reg-exp"
          />
        </div>
      </AdminCard>

      {/* Insurance */}
      <AdminCard title="Insurance">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <InputOrField
            label="Carrier"
            editing={editing}
            value={editing ? form.insurance_carrier : asset.insurance_carrier}
            onChange={(v) => setForm((f) => ({ ...f, insurance_carrier: v }))}
            testid="ap-admin-ins-carrier"
          />
          <InputOrField
            label="Policy #"
            editing={editing}
            value={editing ? form.insurance_policy_number : asset.insurance_policy_number}
            onChange={(v) => setForm((f) => ({ ...f, insurance_policy_number: v }))}
            testid="ap-admin-ins-policy"
          />
          <InputOrField
            label="Expiration"
            editing={editing}
            value={editing ? form.insurance_expiration : asset.insurance_expiration}
            type="date"
            onChange={(v) => setForm((f) => ({ ...f, insurance_expiration: v }))}
            testid="ap-admin-ins-exp"
          />
        </div>
      </AdminCard>

      {/* Organization */}
      <AdminCard title="Organization">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <InputOrField
            label="Division"
            editing={editing}
            value={editing ? form.division : asset.division}
            onChange={(v) => setForm((f) => ({ ...f, division: v }))}
            testid="ap-admin-division"
          />
          <InputOrField
            label="Region"
            editing={editing}
            value={editing ? form.region : asset.region}
            onChange={(v) => setForm((f) => ({ ...f, region: v }))}
            testid="ap-admin-region"
          />
          <SelectOrField
            label="Normalized Company"
            editing={editing}
            value={editing ? form.normalized_company : asset.normalized_company}
            options={taxonomy?.canonical_companies || []}
            onChange={(v) => setForm((f) => ({ ...f, normalized_company: v }))}
            testid="ap-admin-company"
          />
          <InputOrField
            label="Supervisor (employee id)"
            editing={editing}
            value={editing ? form.supervisor_id : asset.supervisor_id}
            onChange={(v) => setForm((f) => ({ ...f, supervisor_id: v }))}
            testid="ap-admin-supervisor"
          />
        </div>
      </AdminCard>

      {/* Identifiers / Devices */}
      <AdminCard title="Identifiers & Devices">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <InputOrField
            label="VIN"
            editing={editing}
            value={editing ? form.vin : asset.vin}
            onChange={(v) => setForm((f) => ({ ...f, vin: v }))}
            testid="ap-admin-vin"
          />
          <InputOrField
            label="License Plate"
            editing={editing}
            value={editing ? form.license_plate : asset.license_plate}
            onChange={(v) => setForm((f) => ({ ...f, license_plate: v }))}
            testid="ap-admin-plate"
          />
          <InputOrField
            label="GPS Device ID"
            editing={editing}
            value={editing ? form.gps_device_id : asset.gps_device_id}
            onChange={(v) => setForm((f) => ({ ...f, gps_device_id: v }))}
            testid="ap-admin-gps"
          />
          <InputOrField
            label="Motive Vehicle ID"
            editing={editing}
            value={editing ? form.motive_vehicle_id : asset.motive_vehicle_id}
            onChange={(v) => setForm((f) => ({ ...f, motive_vehicle_id: v }))}
            testid="ap-admin-motive"
          />
          <InputOrField
            label="MaintainX Asset ID"
            editing={editing}
            value={editing ? form.maintainx_asset_id : asset.maintainx_asset_id}
            onChange={(v) => setForm((f) => ({ ...f, maintainx_asset_id: v }))}
            testid="ap-admin-maintainx"
          />
          <InputOrField
            label="FleetWatcher Asset ID"
            editing={editing}
            value={editing ? form.fleetwatcher_asset_id : asset.fleetwatcher_asset_id}
            onChange={(v) => setForm((f) => ({ ...f, fleetwatcher_asset_id: v }))}
            testid="ap-admin-fleetwatcher"
          />
        </div>
      </AdminCard>

      <div className="text-[10px] font-mono text-slate-400 uppercase tracking-[0.18em]">
        Source: equipment_master · spine v{asset.asset_category_version || "1.0.0"} · one asset · one record
      </div>
    </div>
  );
}

function AdminCard({ title, subtitle, children }) {
  return (
    <div className="bg-white border border-slate-200 rounded-md p-5" data-testid={`ap-admin-card-${title.toLowerCase().replace(/\s+/g, "-").replace(/&/g, "and")}`}>
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold mb-3 flex items-center justify-between gap-2">
        <span>{title}</span>
        {subtitle && <span className="text-slate-400 font-normal normal-case tracking-normal">{subtitle}</span>}
      </div>
      {children}
    </div>
  );
}

function InputOrField({ label, editing, value, onChange, testid, type = "text" }) {
  if (!editing) return <Field label={label} value={value} />;
  return (
    <div>
      <label className="font-mono text-[9px] uppercase tracking-[0.18em] text-slate-500 font-bold block mb-1">
        {label}
      </label>
      <input
        type={type}
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        className="w-full text-sm border border-slate-300 rounded px-2 py-1.5 bg-white"
        data-testid={testid}
      />
    </div>
  );
}

function SelectOrField({ label, editing, value, options, onChange, testid, disabled = false }) {
  if (!editing) {
    return (
      <div>
        <div className="font-mono text-[9px] uppercase tracking-[0.18em] text-slate-500 font-bold">{label}</div>
        <div className="text-sm font-bold text-slate-900 mt-0.5 break-words">
          {value ? String(value).replace(/_/g, " ") : <span className="text-slate-400 font-normal">—</span>}
        </div>
      </div>
    );
  }
  return (
    <div>
      <label className="font-mono text-[9px] uppercase tracking-[0.18em] text-slate-500 font-bold block mb-1">
        {label}
      </label>
      <select
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="w-full text-sm border border-slate-300 rounded px-2 py-1.5 bg-white disabled:bg-slate-50"
        data-testid={testid}
      >
        <option value="">— select —</option>
        {options.map((o) => (
          <option key={o} value={o}>{String(o).replace(/_/g, " ")}</option>
        ))}
      </select>
    </div>
  );
}
