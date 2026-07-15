// MaintainxDefectCoverageSection — read-only operational intelligence
// layer. Shows every active equipment defect across all sources and
// classifies each for MaintainX readiness.
//
// Backend endpoint:
//   GET /api/admin/maintainx/defect-coverage?sample_limit=&since_days=
// Or, when used from non-admin portals:
//   GET /api/integrations/maintainx/defect-coverage
//
// SAFETY: This component triggers NO writes. There are no action
// buttons that mutate any defect, asset, mapping, or MaintainX
// record. It is intelligence-only.
import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  RefreshCcw, Loader2, Layers, Truck, Wrench, Camera, AlertTriangle,
  CheckCircle2, ShieldAlert, Copy as CopyIcon, Eye, X as XIcon, Lock,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription,
} from "@/components/ui/sheet";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { operationalError } from "@/lib/errors";

const READINESS_PILL = {
  READY:          "bg-emerald-100 text-emerald-900 border-emerald-300",
  BLOCKED:        "bg-amber-100 text-amber-900 border-amber-300",
  DUPLICATE_RISK: "bg-violet-100 text-violet-900 border-violet-300",
  EXCLUDED:       "bg-slate-100 text-slate-600 border-slate-200",
};

const MX_STATUS_PILL = {
  Mapped:         "bg-emerald-100 text-emerald-900 border-emerald-300",
  Ready:          "bg-sky-100 text-sky-900 border-sky-300",
  Blocked:        "bg-amber-100 text-amber-900 border-amber-300",
  "Duplicate Risk": "bg-violet-100 text-violet-900 border-violet-300",
  Excluded:       "bg-slate-100 text-slate-600 border-slate-200",
  "Not Evaluated": "bg-slate-100 text-slate-600 border-slate-200",
};

function Pill({ tone = "muted", className = "", children, testId }) {
  const base = "inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[10px] font-mono font-bold uppercase tracking-wide";
  return <span data-testid={testId} className={`${base} ${className}`}>{children}</span>;
}

function StatCell({ label, value, tone, testId }) {
  const toneCls = {
    ok:    "border-emerald-200 bg-emerald-50",
    warn:  "border-amber-200 bg-amber-50",
    bad:   "border-red-200 bg-red-50",
    info:  "border-sky-200 bg-sky-50",
    muted: "border-slate-200 bg-slate-50",
  }[tone] || "border-slate-200 bg-slate-50";
  return (
    <div className={`border rounded-md px-3 py-2 ${toneCls}`} data-testid={testId}>
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600 font-bold">{label}</div>
      <div className="text-lg font-display font-black text-slate-900 tabular-nums">{value ?? 0}</div>
    </div>
  );
}

export default function MaintainxDefectCoverageSection({
  endpoint = "/admin/maintainx/defect-coverage",
  scope = "admin",     // "admin" | "shop" — controls visible cells
  testIdPrefix = "mx-coverage",
} = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filterSource, setFilterSource] = useState(null);
  const [drawerDefect, setDrawerDefect] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get(endpoint, { params: { sample_limit: 200, since_days: 60 } });
      setData(data);
    } catch (e) {
      toast.error(operationalError(e, "Could not load defect coverage"));
    } finally {
      setLoading(false);
    }
  }, [endpoint]);

  useEffect(() => { load(); }, [load]);

  const totals = data?.totals || {};
  const breakdown = data?.breakdown || [];
  const defects = useMemo(() => (data?.defects || []), [data?.defects]);

  const filteredDefects = useMemo(() => {
    if (!filterSource) return defects;
    return defects.filter((d) => d.source_type === filterSource);
  }, [defects, filterSource]);

  return (
    <section
      className="bg-white border border-slate-200 rounded-md p-4"
      data-testid={`${testIdPrefix}-root`}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Layers className="w-5 h-5 text-slate-700" />
          <h3 className="font-display text-lg font-black tracking-tight">
            MaintainX Defect Source Coverage
          </h3>
        </div>
        <Button
          size="sm"
          variant="outline"
          onClick={load}
          disabled={loading}
          data-testid={`${testIdPrefix}-refresh`}
        >
          {loading
            ? <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
            : <RefreshCcw className="w-3.5 h-3.5 mr-1" />}
          Refresh
        </Button>
      </div>

      {scope === "admin" && (
        <div
          className="bg-slate-50 border border-slate-200 rounded-md p-3 mb-3 flex items-start gap-3"
          data-testid={`${testIdPrefix}-banner`}
        >
          <Lock className="w-4 h-4 text-slate-600 shrink-0 mt-0.5" />
          <p className="text-xs text-slate-700 leading-snug">
            <strong>Read-only intelligence.</strong> This view shows what would flow into MaintainX
            once writes are authorized. It performs zero writes against MaintainX,
            equipment records, defects, RTS, DVIR, Pre-Op, Shop, or Dispatch.
          </p>
        </div>
      )}

      {/* ── Overview tile ───────────────────────────────────────── */}
      {data && (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2 mb-4">
          <StatCell label="Open Defects" value={totals.open_defects} tone="info"
            testId={`${testIdPrefix}-total-open`} />
          <StatCell label="High Severity" value={totals.high_severity} tone="warn"
            testId={`${testIdPrefix}-total-high`} />
          <StatCell label="Safety Critical" value={totals.safety_critical} tone="bad"
            testId={`${testIdPrefix}-total-safety`} />
          <StatCell label="Out of Service" value={totals.out_of_service} tone="bad"
            testId={`${testIdPrefix}-total-oos`} />
          <StatCell label="Ready" value={totals.ready_for_maintainx} tone="ok"
            testId={`${testIdPrefix}-total-ready`} />
          <StatCell label="Blocked" value={totals.blocked} tone="warn"
            testId={`${testIdPrefix}-total-blocked`} />
          <StatCell label="Duplicate Risk" value={totals.duplicate_risk} tone="muted"
            testId={`${testIdPrefix}-total-dup`} />
        </div>
      )}

      {/* ── Source breakdown grid ───────────────────────────────── */}
      <div className="border border-slate-200 rounded-md overflow-hidden mb-4" data-testid={`${testIdPrefix}-breakdown`}>
        <table className="w-full text-sm">
          <thead className="bg-slate-100">
            <tr className="text-left">
              <th className="px-3 py-2 font-mono text-[10px] uppercase tracking-wide text-slate-600">Source</th>
              <th className="px-3 py-2 font-mono text-[10px] uppercase tracking-wide text-slate-600 text-right">Open</th>
              <th className="px-3 py-2 font-mono text-[10px] uppercase tracking-wide text-slate-600 text-right">OOS</th>
              <th className="px-3 py-2 font-mono text-[10px] uppercase tracking-wide text-slate-600 text-right">Safety</th>
              <th className="px-3 py-2 font-mono text-[10px] uppercase tracking-wide text-slate-600 text-right">Ready</th>
              <th className="px-3 py-2 font-mono text-[10px] uppercase tracking-wide text-slate-600 text-right">Blocked</th>
              <th className="px-3 py-2 font-mono text-[10px] uppercase tracking-wide text-slate-600 text-right">Dup Risk</th>
              <th className="px-3 py-2 font-mono text-[10px] uppercase tracking-wide text-slate-600 text-right">Mapped</th>
            </tr>
          </thead>
          <tbody>
            {breakdown.map((b) => (
              <tr
                key={b.source_type}
                className={`border-t border-slate-100 cursor-pointer hover:bg-slate-50 ${filterSource === b.source_type ? "bg-slate-100" : ""}`}
                onClick={() => setFilterSource(filterSource === b.source_type ? null : b.source_type)}
                data-testid={`${testIdPrefix}-row-${b.source_type}`}
              >
                <td className="px-3 py-2 font-medium text-slate-800 flex items-center gap-2">
                  <Truck className="w-3.5 h-3.5 text-slate-500" />
                  {b.label}
                </td>
                <td className="px-3 py-2 text-right tabular-nums">{b.open}</td>
                <td className="px-3 py-2 text-right tabular-nums">{b.oos}</td>
                <td className="px-3 py-2 text-right tabular-nums">{b.safety_critical}</td>
                <td className="px-3 py-2 text-right tabular-nums text-emerald-700 font-bold">{b.ready}</td>
                <td className="px-3 py-2 text-right tabular-nums text-amber-700">{b.blocked}</td>
                <td className="px-3 py-2 text-right tabular-nums text-violet-700">{b.duplicate_risk}</td>
                <td className="px-3 py-2 text-right tabular-nums text-emerald-700">{b.mapped}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* ── Defect explorer ─────────────────────────────────────── */}
      <div className="border border-slate-200 rounded-md overflow-hidden">
        <div className="flex items-center justify-between bg-slate-50 px-3 py-2 border-b border-slate-200">
          <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-slate-600 font-bold">
            Defect Explorer
            {filterSource ? ` · filter: ${filterSource}` : ""}
          </span>
          {filterSource && (
            <Button
              size="sm"
              variant="ghost"
              className="h-7"
              onClick={() => setFilterSource(null)}
              data-testid={`${testIdPrefix}-filter-clear`}
            >
              <XIcon className="w-3.5 h-3.5 mr-1" />
              Clear filter
            </Button>
          )}
        </div>
        {filteredDefects.length === 0 ? (
          <div className="text-center text-xs text-slate-500 py-6" data-testid={`${testIdPrefix}-empty`}>
            No defects in the current view.
          </div>
        ) : (
          <ul className="divide-y divide-slate-100 max-h-[420px] overflow-y-auto" data-testid={`${testIdPrefix}-list`}>
            {filteredDefects.map((d) => (
              <li
                key={`${d.source_type}-${d.source_record_id}`}
                className="px-3 py-2 hover:bg-slate-50 flex items-start gap-3 cursor-pointer"
                onClick={() => setDrawerDefect(d)}
                data-testid={`${testIdPrefix}-defect-${d.source_record_id}`}
              >
                <div className="shrink-0 mt-0.5">
                  {d.out_of_service
                    ? <ShieldAlert className="w-4 h-4 text-red-600" />
                    : <Wrench className="w-4 h-4 text-slate-500" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-slate-800 truncate">
                    {d.defect_title || "—"}
                  </div>
                  <div className="text-[11px] text-slate-500 flex items-center gap-2 flex-wrap">
                    <span className="font-mono">{d.unit_number || "—"}</span>
                    <span>·</span>
                    <span>{d.equipment_name || "—"}</span>
                    <span>·</span>
                    <span>{d.reported_by || "—"}</span>
                    <span>·</span>
                    <span>{(d.reported_at || "").slice(0, 10)}</span>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <Pill className={READINESS_PILL[d.classification?.readiness] || READINESS_PILL.BLOCKED}>
                    {d.classification?.readiness || "—"}
                  </Pill>
                  <Pill className={MX_STATUS_PILL[d.classification?.maintainx_status] || MX_STATUS_PILL["Not Evaluated"]}>
                    {d.classification?.maintainx_status || "—"}
                  </Pill>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* ── Drawer ──────────────────────────────────────────────── */}
      <Sheet open={!!drawerDefect} onOpenChange={(o) => !o && setDrawerDefect(null)}>
        <SheetContent
          side="right"
          className="w-[460px] sm:max-w-[460px] overflow-y-auto"
          data-testid={`${testIdPrefix}-drawer`}
        >
          {drawerDefect && (
            <>
              <SheetHeader>
                <SheetTitle className="font-display text-xl font-black leading-tight">
                  {drawerDefect.defect_title || "Defect"}
                </SheetTitle>
                <SheetDescription className="text-xs text-slate-500">
                  {drawerDefect.source_collection} · {drawerDefect.source_record_id}
                </SheetDescription>
              </SheetHeader>

              <div className="mt-4 space-y-3 text-sm">
                <Row label="Source" value={drawerDefect.source_type} />
                <Row label="Equipment Name" value={drawerDefect.equipment_name || "—"} />
                <Row label="Unit Number" value={drawerDefect.unit_number || "—"} />
                <Row label="Make / Model" value={`${drawerDefect.make || "—"} ${drawerDefect.model || ""}`.trim()} />
                <Row label="Reported By" value={drawerDefect.reported_by || "—"} />
                <Row label="Date Reported" value={(drawerDefect.reported_at || "").slice(0, 19) || "—"} />
                <Row label="Severity" value={drawerDefect.severity || "—"} />
                <Row label="Status" value={drawerDefect.status || "—"} />
                <Row label="Out of Service" value={drawerDefect.out_of_service ? "Yes" : "No"} />
                <Row label="Safety Critical" value={drawerDefect.safety_critical ? "Yes" : "No"} />
                <Row label="Photos Present" value={drawerDefect.photos_present ? "Yes" : "No"} />
                <Row label="RTS Required" value={drawerDefect.rts_required ? "Yes" : "No"} />
                <Row label="MaintainX Status" value={drawerDefect.classification?.maintainx_status || "Not Evaluated"} />
                <Row label="Readiness" value={drawerDefect.classification?.readiness || "—"} />
                <div className="pt-2 border-t border-slate-100">
                  <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-1">
                    Reasons
                  </div>
                  <ul className="list-disc pl-5 text-xs text-slate-700">
                    {(drawerDefect.classification?.reasons || []).map((r, i) => <li key={i}>{r}</li>)}
                  </ul>
                </div>
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>

      {/* Writes-verified footer */}
      {data?.writes_performed && (
        <div
          className="mt-3 text-[11px] text-emerald-900 bg-emerald-50 border border-emerald-200 rounded-md p-2 flex items-center gap-2"
          data-testid={`${testIdPrefix}-writes`}
        >
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span className="font-mono">
            writes_performed:
            mx={data.writes_performed.maintainx ?? 0} ·
            eq_master={data.writes_performed.equipment_master ?? 0} ·
            fleet_defects={data.writes_performed.fleet_defects ?? 0} ·
            inspections={data.writes_performed.equipment_inspections ?? 0} ·
            holds={data.writes_performed.asset_holds ?? 0} ·
            mappings={data.writes_performed.asset_mappings ?? 0}
          </span>
        </div>
      )}
    </section>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex items-center justify-between border-b border-slate-100 pb-1">
      <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-slate-500 font-bold">
        {label}
      </span>
      <span className="text-sm text-slate-800 text-right break-words max-w-[60%]">{value}</span>
    </div>
  );
}
