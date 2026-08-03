// Trench Safety · Phase 9A · Reporting & Analytics Command Center
// ─────────────────────────────────────────────────────────────────────
// Single page, 9 collapsible reports, global filter bar, CSV export.
// Reads from /api/trench-safety/reports/* — no new collections, no
// new analytics engine. Mobile-first table layouts (no fancy charts).
import React, { useEffect, useMemo, useState } from "react";
import {
  Loader2, Download, FileBarChart, AlertTriangle, ChevronDown, ChevronRight,
  Boxes, ClipboardCheck, Wrench, ShieldAlert, Activity, FileQuestion,
  MapPin, History, Layers, Mail,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";
import TrenchSafetyShell from "@/pages/trench_safety/TrenchSafetyShell";
import { ASSET_TYPES } from "@/pages/trench_safety/TrenchSafetyActions";
import { SubscriptionManagerDialog, LeadershipDigestButton } from "@/pages/trench_safety/TrenchSafetyReportDistribution";

const REPORTS = [
  { id: "executive",             icon: FileBarChart,    title: "Executive Asset Health" },
  { id: "road-plate",            icon: Layers,          title: "Road Plate Command" },
  { id: "inspection-compliance", icon: ClipboardCheck,  title: "Inspection Compliance" },
  { id: "repair-backlog",        icon: Wrench,          title: "Repair Backlog" },
  { id: "holds",                 icon: ShieldAlert,     title: "Hold Management" },
  { id: "utilization",           icon: Boxes,           title: "Asset Utilization" },
  { id: "missing-data",          icon: FileQuestion,    title: "Missing Data" },
  { id: "project-assets",        icon: MapPin,          title: "Project Asset" },
  { id: "activity",              icon: Activity,        title: "Activity & History" },
];

const STATUSES = [
  "Available", "Assigned", "In Transport",
  "Safety Hold", "Inspection Hold", "Maintenance Hold",
  "Certification Hold", "Retired",
];
const CONDITIONS = ["Excellent", "Good", "Fair", "Poor", "Out Of Service"];

function Pct({ value }) {
  const v = Number.isFinite(value) ? value : 0;
  const color = v >= 90 ? "text-emerald-700" : v >= 75 ? "text-blue-700" : v >= 60 ? "text-amber-700" : "text-red-700";
  return <span className={"font-mono font-black text-2xl " + color}>{v}<span className="text-base opacity-60">%</span></span>;
}

function StatCard({ label, value, tone = "default", testId }) {
  const toneClass = {
    default: "bg-white border-slate-200 text-slate-900",
    info: "bg-cyan-50 border-cyan-300 text-cyan-900",
    warn: "bg-amber-50 border-amber-300 text-amber-900",
    danger: "bg-red-50 border-red-300 text-red-900",
    ok: "bg-emerald-50 border-emerald-300 text-emerald-900",
  }[tone] || "bg-white border-slate-200 text-slate-900";
  return (
    <div className={"border rounded-md px-3 py-2 " + toneClass} data-testid={testId}>
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] opacity-70">{label}</div>
      <div className="font-display text-2xl sm:text-3xl font-black leading-none mt-1">{value}</div>
    </div>
  );
}

function MiniTable({ headers, rows, testId }) {
  if (!rows || rows.length === 0) {
    return (
      <div className="text-xs italic text-slate-500 px-2 py-3" data-testid={testId}>
        — no rows —
      </div>
    );
  }
  return (
    <div className="border border-slate-200 rounded overflow-hidden" data-testid={testId}>
      <table className="w-full text-xs">
        <thead className="bg-slate-50 text-left font-mono uppercase tracking-[0.12em] text-slate-600">
          <tr>{headers.map((h) => <th key={h} className="px-2 py-1.5">{h}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className={i % 2 ? "bg-slate-50/40" : ""}>
              {row.map((cell, j) => (
                <td key={j} className="px-2 py-1.5 font-mono text-slate-800 align-top">{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────
// Filter bar
// ─────────────────────────────────────────────────────────────────────
function GlobalFilterBar({ filters, onChange }) {
  const { t } = useT();
  const set = (k, v) => onChange({ ...filters, [k]: v || undefined });
  return (
    <div className="bg-white border border-slate-200 rounded-md p-3" data-testid="reports-filter-bar">
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold mb-2">
        {t("Global Filters")}
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
        <div>
          <Label className="text-[10px] uppercase font-bold tracking-[0.12em]">{t("Date From")}</Label>
          <Input type="date" value={filters.date_from || ""} onChange={(e) => set("date_from", e.target.value)} data-testid="filter-date-from" />
        </div>
        <div>
          <Label className="text-[10px] uppercase font-bold tracking-[0.12em]">{t("Date To")}</Label>
          <Input type="date" value={filters.date_to || ""} onChange={(e) => set("date_to", e.target.value)} data-testid="filter-date-to" />
        </div>
        <div>
          <Label className="text-[10px] uppercase font-bold tracking-[0.12em]">{t("Asset Type")}</Label>
          <Select value={filters.asset_type || "__all"} onValueChange={(v) => set("asset_type", v === "__all" ? "" : v)}>
            <SelectTrigger data-testid="filter-asset-type"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="__all">{t("All Types")}</SelectItem>
              {ASSET_TYPES.map((x) => <SelectItem key={x} value={x}>{t(x)}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label className="text-[10px] uppercase font-bold tracking-[0.12em]">{t("Status")}</Label>
          <Select value={filters.status || "__all"} onValueChange={(v) => set("status", v === "__all" ? "" : v)}>
            <SelectTrigger data-testid="filter-status"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="__all">{t("All")}</SelectItem>
              {STATUSES.map((x) => <SelectItem key={x} value={x}>{t(x)}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label className="text-[10px] uppercase font-bold tracking-[0.12em]">{t("Condition")}</Label>
          <Select value={filters.condition || "__all"} onValueChange={(v) => set("condition", v === "__all" ? "" : v)}>
            <SelectTrigger data-testid="filter-condition"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="__all">{t("All")}</SelectItem>
              {CONDITIONS.map((x) => <SelectItem key={x} value={x}>{t(x)}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label className="text-[10px] uppercase font-bold tracking-[0.12em]">{t("Location")}</Label>
          <Input placeholder={t("e.g., MASCI Yard")} value={filters.location || ""} onChange={(e) => set("location", e.target.value)} data-testid="filter-location" />
        </div>
      </div>
      <div className="mt-2 flex justify-end">
        <Button variant="outline" size="sm" onClick={() => onChange({})} data-testid="filter-reset">{t("Reset Filters")}</Button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────
// Report renderers
// ─────────────────────────────────────────────────────────────────────
function ReportExecutive({ data }) {
  const { t } = useT();
  const tt = data?.totals || {};
  const ra = data?.ratios || {};
  return (
    <div className="space-y-3" data-testid="report-executive">
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
        <StatCard label={t("Total Assets")}    value={tt.total_assets ?? 0}    testId="exec-total" />
        <StatCard label={t("Available")}       value={tt.available ?? 0}      tone="ok"   testId="exec-available" />
        <StatCard label={t("Assigned")}        value={tt.assigned ?? 0}       tone="info" testId="exec-assigned" />
        <StatCard label={t("In Transport")}    value={tt.in_transport ?? 0}   tone="info" testId="exec-intransport" />
        <StatCard label={t("On Hold")}         value={tt.on_hold ?? 0}        tone={tt.on_hold ? "danger" : "default"} testId="exec-onhold" />
        <StatCard label={t("Retired")}         value={tt.retired ?? 0}        testId="exec-retired" />
        <StatCard label={t("Active Assets")}   value={tt.active_assets ?? 0}  testId="exec-active" />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-2">
        <div className="border rounded p-3 bg-white"><div className="text-[10px] uppercase font-mono tracking-[0.18em] text-slate-500">{t("Asset Availability")}</div><Pct value={ra.asset_availability_pct} /></div>
        <div className="border rounded p-3 bg-white"><div className="text-[10px] uppercase font-mono tracking-[0.18em] text-slate-500">{t("Inspection Compliance")}</div><Pct value={ra.inspection_compliance_pct} /></div>
        <div className="border rounded p-3 bg-white"><div className="text-[10px] uppercase font-mono tracking-[0.18em] text-slate-500">{t("Repair Backlog")}</div><Pct value={ra.repair_backlog_pct} /></div>
        <div className="border rounded p-3 bg-white"><div className="text-[10px] uppercase font-mono tracking-[0.18em] text-slate-500">{t("Operational Health")}</div><Pct value={data?.health_score} /><div className="text-xs font-bold text-slate-700">{t(data?.health_rating || "—")}</div></div>
      </div>
      <MiniTable
        headers={[t("Window"), t("Activity Count")]}
        rows={Object.entries(data?.activity_trends || {}).map(([k, v]) => [k.replace("last_", "").toUpperCase(), v])}
        testId="exec-trend-table"
      />
    </div>
  );
}

function ReportRoadPlate({ data }) {
  const { t } = useT();
  const tt = data?.totals || {};
  const ra = data?.ratios || {};
  const cap = data?.capacity_inventory || {};
  const tr = data?.trend_30d || {};
  return (
    <div className="space-y-3" data-testid="report-road-plate">
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
        <StatCard label={t("Total Road Plates")} value={tt.total ?? 0}        testId="rp-total" />
        <StatCard label={t("Available")}         value={tt.available ?? 0}   tone="ok"   testId="rp-available" />
        <StatCard label={t("Assigned")}          value={tt.assigned ?? 0}    tone="info" testId="rp-assigned" />
        <StatCard label={t("In Transport")}      value={tt.in_transport ?? 0} tone="info" testId="rp-intransport" />
        <StatCard label={t("On Hold")}           value={tt.on_hold ?? 0}     tone={tt.on_hold ? "danger" : "default"} testId="rp-onhold" />
        <StatCard label={t("Open Repairs")}      value={tt.open_repairs ?? 0} tone={tt.open_repairs ? "warn" : "default"} testId="rp-repairs" />
        <StatCard label={t("Missing Capacity")}  value={tt.missing_capacity_data ?? 0} tone={tt.missing_capacity_data ? "warn" : "default"} testId="rp-missing-cap" />
        <StatCard label={t("Missing Serial")}    value={tt.missing_serial_numbers ?? 0} tone={tt.missing_serial_numbers ? "warn" : "default"} testId="rp-missing-serial" />
        <StatCard label={t("Missing Photos")}    value={tt.missing_photos ?? 0} testId="rp-missing-photos" />
      </div>
      <div className="grid grid-cols-2 gap-2">
        <div className="border rounded p-3 bg-white"><div className="text-[10px] uppercase font-mono tracking-[0.18em] text-slate-500">{t("Utilization")}</div><Pct value={ra.utilization_pct} /></div>
        <div className="border rounded p-3 bg-white"><div className="text-[10px] uppercase font-mono tracking-[0.18em] text-slate-500">{t("Inspection Compliance")}</div><Pct value={ra.inspection_compliance_pct} /></div>
      </div>
      <MiniTable
        headers={[t("Capacity Bucket"), t("Count")]}
        rows={[
          [t("Unknown"), cap.unknown ?? 0],
          [t("< 40k lb"), cap.lt_40k ?? 0],
          [t("40k–80k lb"), cap["40k_80k"] ?? 0],
          [t("≥ 80k lb"), cap.ge_80k ?? 0],
        ]}
        testId="rp-capacity-table"
      />
      <MiniTable
        headers={[t("Trend · 30 Days"), t("Count")]}
        rows={[
          [t("Repair Activity"), tr.repair_history ?? 0],
          [t("Deployment Events"), tr.deployment_history ?? 0],
        ]}
        testId="rp-trend-table"
      />
    </div>
  );
}

function ReportInspectionCompliance({ data }) {
  const { t } = useT();
  const tt = data?.totals || {};
  return (
    <div className="space-y-3" data-testid="report-inspection-compliance">
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
        <StatCard label={t("Completed")}    value={tt.completed ?? 0}    tone="ok"   testId="ic-completed" />
        <StatCard label={t("Due Soon")}     value={tt.due_soon ?? 0}     tone="warn" testId="ic-due-soon" />
        <StatCard label={t("Overdue")}      value={tt.overdue ?? 0}      tone={tt.overdue ? "danger" : "default"} testId="ic-overdue" />
        <StatCard label={t("Failed · 30d")} value={tt.failed_30d ?? 0}   tone={tt.failed_30d ? "danger" : "default"} testId="ic-failed" />
        <StatCard label={t("Missing")}      value={tt.missing ?? 0}      tone={tt.missing ? "warn" : "default"} testId="ic-missing" />
      </div>
      <div className="border rounded p-3 bg-white">
        <div className="text-[10px] uppercase font-mono tracking-[0.18em] text-slate-500">{t("Compliance Score")}</div>
        <Pct value={data?.compliance_score} />
      </div>
      <MiniTable
        headers={[t("Type"), t("Total"), t("Overdue"), t("Compliance %")]}
        rows={Object.entries(data?.by_asset_type || {}).map(([k, v]) => [t(k), v.total, v.overdue, `${v.compliance_pct}%`])}
        testId="ic-by-type"
      />
      <MiniTable
        headers={[t("Yard / Location"), t("Total"), t("Overdue"), t("Compliance %")]}
        rows={(data?.top_risk_areas || []).map((r) => [r.yard, r.total, r.overdue, `${r.compliance_pct}%`])}
        testId="ic-top-risk"
      />
      <MiniTable
        headers={[t("Window"), t("Inspections")]}
        rows={Object.entries(data?.trend || {}).map(([k, v]) => [k.replace("last_", "").toUpperCase(), v])}
        testId="ic-trend"
      />
    </div>
  );
}

function ReportRepairBacklog({ data }) {
  const { t } = useT();
  const tt = data?.totals || {};
  return (
    <div className="space-y-3" data-testid="report-repair-backlog">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <StatCard label={t("Open Repairs")}        value={tt.open_repairs ?? 0}      tone={tt.open_repairs ? "warn" : "default"} testId="rb-open" />
        <StatCard label={t("Completed")}           value={tt.completed_repairs ?? 0} tone="ok"   testId="rb-completed" />
        <StatCard label={t("Avg Days Open")}       value={tt.avg_days_open ?? 0}     testId="rb-avg-open" />
        <StatCard label={t("Avg Days to Close")}   value={tt.avg_days_to_close ?? 0} testId="rb-avg-close" />
      </div>
      <MiniTable
        headers={[t("Kind"), t("Count")]}
        rows={Object.entries(data?.by_kind || {}).map(([k, v]) => [k, v])}
        testId="rb-kind"
      />
      <MiniTable
        headers={[t("Asset Type"), t("Count")]}
        rows={Object.entries(data?.by_asset_type || {}).map(([k, v]) => [t(k), v])}
        testId="rb-asset-type"
      />
      <MiniTable
        headers={[t("Asset"), t("Type"), t("Repair Count")]}
        rows={(data?.top_repeat_assets || []).map((r) => [r.asset_id, t(r.asset_type || "—"), r.repair_count])}
        testId="rb-top-repeat"
      />
      <MiniTable
        headers={[t("Window"), t("Repairs Opened")]}
        rows={Object.entries(data?.trend || {}).map(([k, v]) => [k.replace("last_", "").toUpperCase(), v])}
        testId="rb-trend"
      />
    </div>
  );
}

function ReportHolds({ data }) {
  const { t } = useT();
  const tt = data?.totals || {};
  return (
    <div className="space-y-3" data-testid="report-holds">
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
        <StatCard label={t("Active")}             value={tt.active ?? 0}              tone={tt.active ? "danger" : "ok"} testId="hl-active" />
        <StatCard label={t("Released")}           value={tt.released ?? 0}            testId="hl-released" />
        <StatCard label={t("Safety")}             value={tt.safety_holds ?? 0}        tone="danger" testId="hl-safety" />
        <StatCard label={t("Inspection")}         value={tt.inspection_holds ?? 0}    tone="warn"   testId="hl-inspection" />
        <StatCard label={t("Maintenance")}        value={tt.maintenance_holds ?? 0}   tone="warn"   testId="hl-maint" />
        <StatCard label={t("Certification")}      value={tt.certification_holds ?? 0} tone="warn"   testId="hl-cert" />
        <StatCard label={t("Avg Days Open")}      value={tt.avg_days_open ?? 0}       testId="hl-avg-days" />
      </div>
      <MiniTable
        headers={[t("Asset"), t("Type"), t("Hold Count")]}
        rows={(data?.most_frequent_assets || []).map((r) => [r.asset_id, t(r.asset_type || "—"), r.hold_count])}
        testId="hl-frequent"
      />
      <MiniTable
        headers={[t("Project"), t("Active Holds")]}
        rows={Object.entries(data?.by_project || {}).map(([k, v]) => [k, v])}
        testId="hl-by-project"
      />
      <MiniTable
        headers={[t("Window"), t("Holds Opened")]}
        rows={Object.entries(data?.trend || {}).map(([k, v]) => [k.replace("last_", "").toUpperCase(), v])}
        testId="hl-trend"
      />
    </div>
  );
}

function ReportUtilization({ data }) {
  const { t } = useT();
  const tt = data?.totals || {};
  return (
    <div className="space-y-3" data-testid="report-utilization">
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
        <StatCard label={t("Available")}      value={tt.available ?? 0}    tone="ok"   testId="ut-available" />
        <StatCard label={t("Assigned")}       value={tt.assigned ?? 0}     tone="info" testId="ut-assigned" />
        <StatCard label={t("In Transport")}   value={tt.in_transport ?? 0} tone="info" testId="ut-intransport" />
        <StatCard label={t("Idle")}           value={tt.idle ?? 0}         testId="ut-idle" />
        <StatCard label={t("Retired")}        value={tt.retired ?? 0}      testId="ut-retired" />
      </div>
      <div className="border rounded p-3 bg-white">
        <div className="text-[10px] uppercase font-mono tracking-[0.18em] text-slate-500">{t("Utilization")}</div>
        <Pct value={data?.utilization_pct} />
      </div>
      <MiniTable
        headers={[t("Type"), t("Total"), t("In Use"), t("Idle"), t("Util %")]}
        rows={Object.entries(data?.by_asset_type || {}).map(([k, v]) => [t(k), v.total, v.in_use, v.idle, `${v.utilization_pct}%`])}
        testId="ut-by-type"
      />
      <MiniTable
        headers={[t("Project"), t("Assets Deployed")]}
        rows={Object.entries(data?.by_project || {}).map(([k, v]) => [k, v])}
        testId="ut-by-project"
      />
    </div>
  );
}

function ReportMissingData({ data }) {
  const { t } = useT();
  const counts = data?.counts || {};
  const items = [
    { key: "missing_serial",       label: t("Missing Serial Number") },
    { key: "missing_capacity",     label: t("Missing Capacity Data") },
    { key: "missing_photos",       label: t("Missing Photos") },
    { key: "missing_manufacturer", label: t("Missing Manufacturer") },
    { key: "missing_inspection",   label: t("Missing Inspection") },
    { key: "missing_project",      label: t("Missing Project Assignment") },
    { key: "missing_location",     label: t("Missing Location") },
    { key: "missing_tabulated",    label: t("Missing Tabulated Data") },
  ];
  return (
    <div className="space-y-3" data-testid="report-missing-data">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {items.map((it) => (
          <StatCard key={it.key} label={it.label} value={counts[it.key] ?? 0} tone={(counts[it.key] ?? 0) > 0 ? "warn" : "default"} testId={`md-${it.key}`} />
        ))}
      </div>
      {items.filter((it) => (counts[it.key] ?? 0) > 0).map((it) => (
        <div key={it.key}>
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600 mb-1">{it.label} · {t("affected assets")}</div>
          <MiniTable
            headers={[t("Asset ID"), t("Type")]}
            rows={(data?.affected?.[it.key] || []).slice(0, 25).map((r) => [r.asset_id, t(r.asset_type || "—")])}
            testId={`md-${it.key}-list`}
          />
        </div>
      ))}
    </div>
  );
}

function ReportProjectAssets({ data }) {
  const { t } = useT();
  return (
    <div className="space-y-3" data-testid="report-project-assets">
      <div className="grid grid-cols-2 gap-2">
        <StatCard label={t("Projects with Assets")} value={data?.total_projects ?? 0} testId="pa-projects" />
        <StatCard label={t("Total Rows")} value={(data?.rows || []).length} testId="pa-rows" />
      </div>
      <MiniTable
        headers={[t("Project"), t("Assets"), t("Trench Boxes"), t("Road Plates"), t("Open Repairs"), t("Insp Due"), t("Holds"), t("Health"), t("Risk")]}
        rows={(data?.rows || []).map((r) => [r.project, r.assigned_assets, r.trench_boxes, r.road_plates, r.open_repairs, r.inspections_due, r.active_holds, r.asset_health_score, r.risk_score])}
        testId="pa-rows-table"
      />
    </div>
  );
}

function ReportActivity({ data }) {
  const { t } = useT();
  const by = data?.by_window || {};
  const allKinds = Array.from(new Set(Object.values(by).flatMap((w) => Object.keys(w))));
  const headers = [t("Event Kind"), "7D", "30D", "90D"];
  const rows = allKinds.map((k) => [k.replace("trench_", "").replace(/_/g, " "), by.last_7d?.[k] ?? 0, by.last_30d?.[k] ?? 0, by.last_90d?.[k] ?? 0]);
  return (
    <div className="space-y-3" data-testid="report-activity">
      <MiniTable headers={headers} rows={rows} testId="act-table" />
    </div>
  );
}

const RENDERERS = {
  "executive": ReportExecutive,
  "road-plate": ReportRoadPlate,
  "inspection-compliance": ReportInspectionCompliance,
  "repair-backlog": ReportRepairBacklog,
  "holds": ReportHolds,
  "utilization": ReportUtilization,
  "missing-data": ReportMissingData,
  "project-assets": ReportProjectAssets,
  "activity": ReportActivity,
};

// ─────────────────────────────────────────────────────────────────────
// Per-report collapsible section
// ─────────────────────────────────────────────────────────────────────
function ReportSection({ report, filters, defaultOpen = false }) {
  const { t } = useT();
  const [open, setOpen] = useState(defaultOpen);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const params = useMemo(() => {
    const out = {};
    Object.entries(filters || {}).forEach(([k, v]) => { if (v) out[k] = v; });
    return out;
  }, [filters]);
  const paramsKey = useMemo(() => JSON.stringify(params), [params]);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    const requestParams = paramsKey ? JSON.parse(paramsKey) : {};
    (async () => {
      setLoading(true);
      setErr("");
      try {
        const r = await api.get(`/trench-safety/reports/${report.id}`, { params: requestParams });
        if (!cancelled) setData(r.data || null);
      } catch (e) {
        if (!cancelled) setErr(e?.response?.data?.detail || e?.message || "Failed");
      } finally { if (!cancelled) setLoading(false); }
    })();
    return () => { cancelled = true; };
  }, [open, paramsKey, report.id]);

  const Renderer = RENDERERS[report.id];
  const Icon = report.icon;

  const downloadCsv = () => {
    const apiBase = process.env.REACT_APP_BACKEND_URL;
    const qs = new URLSearchParams(params).toString();
    const url = `${apiBase}/api/trench-safety/reports/${report.id}/export.csv${qs ? "?" + qs : ""}`;
    window.open(url, "_blank");
  };
  const downloadFormat = (fmt) => {
    // Phase 9B — same params, just swap the extension
    const apiBase = process.env.REACT_APP_BACKEND_URL;
    const qs = new URLSearchParams(params).toString();
    const url = `${apiBase}/api/trench-safety/reports/${report.id}/export.${fmt}${qs ? "?" + qs : ""}`;
    window.open(url, "_blank");
  };

  return (
    <section className="border border-slate-200 rounded-md overflow-hidden" data-testid={`report-section-${report.id}`}>
      <header
        className="flex items-center justify-between gap-2 px-3 py-2 bg-slate-50 cursor-pointer"
        onClick={() => setOpen((x) => !x)}
        data-testid={`report-toggle-${report.id}`}
      >
        <div className="flex items-center gap-2">
          {open ? <ChevronDown className="w-4 h-4 text-cyan-700" /> : <ChevronRight className="w-4 h-4 text-slate-500" />}
          <Icon className="w-4 h-4 text-cyan-700" />
          <h2 className="font-display font-black text-slate-900">{t(report.title)}</h2>
        </div>
        <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
          <Button size="sm" variant="outline" onClick={() => downloadFormat("csv")} data-testid={`report-csv-${report.id}`}>
            <Download className="w-3.5 h-3.5 mr-1" /> CSV
          </Button>
          <Button size="sm" variant="outline" onClick={() => downloadFormat("xlsx")} data-testid={`report-xlsx-${report.id}`}>
            <Download className="w-3.5 h-3.5 mr-1" /> XLSX
          </Button>
          <Button size="sm" variant="outline" onClick={() => downloadFormat("pdf")} data-testid={`report-pdf-${report.id}`}>
            <Download className="w-3.5 h-3.5 mr-1" /> PDF
          </Button>
        </div>
      </header>
      {open && (
        <div className="p-3 bg-white">
          {loading ? (
            <div className="flex items-center gap-2 text-slate-500"><Loader2 className="w-4 h-4 animate-spin" /> {t("Loading…")}</div>
          ) : err ? (
            <div className="p-2 border border-red-300 bg-red-50 rounded text-red-900 text-sm" data-testid={`report-error-${report.id}`}>
              <AlertTriangle className="w-4 h-4 inline -mt-0.5 mr-1" /> {err}
            </div>
          ) : Renderer && data ? (
            <Renderer data={data} />
          ) : null}
        </div>
      )}
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────
// Page
// ─────────────────────────────────────────────────────────────────────
export default function TrenchSafetyReports() {
  const { t } = useT();
  const [filters, setFilters] = useState({});
  const [subOpen, setSubOpen] = useState(false);
  return (
    <TrenchSafetyShell active="reports" title={t("Trench Safety Reports")} kicker={t("Operational reporting on certified data")}>
      <p className="text-slate-700 mb-4 max-w-3xl" data-testid="reports-intro">
        {t("Nine read-only operational reports computed from the certified asset registry. Apply filters once — they cascade across every report. CSV / XLSX / PDF export available on each section.")}
      </p>
      <div className="flex flex-wrap items-center gap-2 mb-3" data-testid="reports-actions">
        <Button size="sm" variant="outline" onClick={() => setSubOpen(true)} data-testid="open-subscriptions">
          <Mail className="w-3.5 h-3.5 mr-1" /> {t("Subscriptions")}
        </Button>
        <LeadershipDigestButton />
      </div>
      <SubscriptionManagerDialog open={subOpen} onOpenChange={setSubOpen} />
      <GlobalFilterBar filters={filters} onChange={setFilters} />
      <div className="mt-4 space-y-3" data-testid="reports-list">
        {REPORTS.map((r, idx) => (
          <ReportSection
            key={r.id}
            report={r}
            filters={filters}
            defaultOpen={idx === 0}
          />
        ))}
      </div>
      <div className="mt-6 p-3 border border-slate-200 rounded bg-slate-50 text-xs text-slate-600" data-testid="reports-footnote">
        <History className="w-3.5 h-3.5 inline -mt-0.5 mr-1" />
        {t("All figures are read directly from the Trench Safety registry, activity log, inspection/repair/hold collections, and the latest stored Pulse snapshot. No separate analytics layer or duplicate data store.")}
      </div>
    </TrenchSafetyShell>
  );
}
