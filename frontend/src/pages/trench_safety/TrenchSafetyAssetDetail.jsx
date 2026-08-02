// Trench Safety Asset Detail — read-only canonical view for Phase 3.
//
// Action buttons are NOT included in Phase 3 (per OMEGA directive:
// "Do NOT add edit/create/repair/inspection action buttons unless
// already fully functional through Phase 2 backend and permission-safe").
// Phase 3 is view-only; lifecycle actions land in Phase 6 once the
// inspection / repair UIs are built.
import React, { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import {
  Loader2, AlertTriangle, FileWarning, ShieldAlert,
  ScanLine, BookOpen, Send, ArrowDownToLine, History, Pencil, Power, Activity,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";
import TrenchSafetyShell from "@/pages/trench_safety/TrenchSafetyShell";
import { DataTable } from "@/design-system";
import { DetailPageHero } from "@/components/detail/DetailPageHero";
import {
  AssignToProjectDialog,
  ReturnFromProjectDialog,
} from "@/pages/trench_safety/TrenchSafetyAssignDialogs";
import {
  EditAssetDialog,
  RetireAssetDialog,
  StatusChangeDialog,
  HoldsPanel,
  InspectionsPanel,
  CertificationsPanel,
  AuditTimelinePanel,
} from "@/pages/trench_safety/TrenchSafetyActions";
import {
  QRManagementPanel,
  PhotoManagementPanel,
} from "@/pages/trench_safety/TrenchSafetyOpsCenter";

const STATUS_COLOR = {
  "Available":          "bg-emerald-50 text-emerald-900 border-emerald-300",
  "Assigned":           "bg-blue-50 text-blue-900 border-blue-300",
  "In Transport":       "bg-cyan-50 text-cyan-900 border-cyan-300",
  "Inspection Hold":    "bg-amber-50 text-amber-900 border-amber-400",
  "Maintenance Hold":   "bg-orange-50 text-orange-900 border-orange-400",
  "Certification Hold": "bg-purple-50 text-purple-900 border-purple-400",
  "Safety Hold":        "bg-red-50 text-red-900 border-red-500",
  "Retired":            "bg-slate-100 text-slate-600 border-slate-300",
};

function Field({ label, value, mono, testId }) {
  return (
    <div data-testid={testId}>
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500">{label}</div>
      <div className={`text-sm mt-0.5 ${mono ? "font-mono" : ""} ${(!value && value !== 0) ? "text-slate-400" : "text-slate-900"}`}>
        {(value === null || value === undefined || value === "") ? "—" : String(value)}
      </div>
    </div>
  );
}

function SurfaceCard({ eyebrow, title, children, className = "", testId }) {
  return (
    <section className={`wp17-panel p-4 sm:p-5 ${className}`.trim()} data-testid={testId}>
      {eyebrow ? <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold mb-2">{eyebrow}</div> : null}
      {title ? <h2 className="font-display text-xl sm:text-2xl font-black tracking-tight text-slate-900">{title}</h2> : null}
      <div className={title ? "mt-4" : ""}>{children}</div>
    </section>
  );
}

export default function TrenchSafetyAssetDetail() {
  const { t } = useT();
  const { assetId } = useParams();
  const location = useLocation();
  const [doc, setDoc] = useState(null);
  const [insp, setInsp] = useState([]);
  const [reps, setReps] = useState([]);
  const [deps, setDeps] = useState([]);
  const [allDeps, setAllDeps] = useState([]);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);
  const [assignOpen, setAssignOpen] = useState(false);
  const [returnOpen, setReturnOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [retireOpen, setRetireOpen] = useState(false);
  const [statusOpen, setStatusOpen] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  const reload = () => setReloadKey((k) => k + 1);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setErr("");
      try {
        const [aRes, iRes, rRes, dRes, dAllRes] = await Promise.all([
          api.get(`/trench-safety/assets/${assetId}`),
          api.get(`/trench-safety/assets/${assetId}/inspections`, { params: { limit: 5 } }).catch(() => ({ data: { items: [] } })),
          api.get(`/trench-safety/assets/${assetId}/repairs`,    { params: { limit: 5 } }).catch(() => ({ data: { items: [] } })),
          api.get(`/trench-safety/assets/${assetId}/deployments`,{ params: { limit: 5 } }).catch(() => ({ data: { items: [] } })),
          api.get(`/trench-safety/assets/${assetId}/deployments`,{ params: { limit: 200 } }).catch(() => ({ data: { items: [] } })),
        ]);
        if (cancelled) return;
        setDoc(aRes.data);
        setInsp(iRes.data?.items || []);
        setReps(rRes.data?.items || []);
        setDeps(dRes.data?.items || []);
        setAllDeps(dAllRes.data?.items || []);
      } catch (e) {
        if (!cancelled) setErr(e?.response?.data?.detail || e?.message || "Failed to load asset");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [assetId, reloadKey]);

  const canAssign =
    doc &&
    !["Inspection Hold", "Repair", "Retired"].includes(doc.operational_status);
  const canReturn =
    doc && doc.operational_status === "Assigned";

  const isPm = location.pathname.startsWith("/pm/trench-safety");
  const isAdmin = location.pathname.startsWith("/admin/trench-safety");
  const portalBase = isPm ? "/pm/trench-safety" : isAdmin ? "/admin/trench-safety" : "/safety/trench-safety";
  const backLabel = isPm ? t("PM · Trench Equipment") : isAdmin ? t("Admin · Trench Equipment") : t("Safety · Trench Equipment");
  const deploymentRows = useMemo(
    () => (allDeps || []).map((d) => ({
      id: d.id,
      project: d.project_name || "—",
      projectNumber: d.project_number || "—",
      superintendent: d.superintendent || "—",
      foreman: d.foreman || "—",
      assignedBy: d.assigned_by || "—",
      assignedAt: d.assigned_at?.slice(0, 16) || "—",
      returnedAt: d.returned_at || null,
      source: d.source || "—",
    })),
    [allDeps]
  );
  const deploymentColumns = useMemo(
    () => [
      { key: "project", header: t("Project"), wrap: true },
      { key: "projectNumber", header: t("Project #") },
      { key: "superintendent", header: t("Superintendent"), wrap: true },
      { key: "foreman", header: t("Foreman"), wrap: true },
      { key: "assignedBy", header: t("Assigned By"), wrap: true },
      { key: "assignedAt", header: t("Assigned") },
      {
        key: "returnedAt",
        header: t("Returned"),
        render: (row) => row.returnedAt ? row.returnedAt.slice(0, 16) : <span className="font-bold text-emerald-700">{t("Active")}</span>,
      },
      { key: "source", header: t("Source"), wrap: true },
    ],
    [t]
  );

  return (
    <TrenchSafetyShell active="assets">
      {loading ? (
        <SurfaceCard testId="trench-detail-loading">
          <div className="flex min-h-[12rem] items-center justify-center gap-2 text-slate-500">
            <Loader2 className="w-5 h-5 animate-spin" /> {t("Loading asset…")}
          </div>
        </SurfaceCard>
      ) : err ? (
        <SurfaceCard className="border border-red-200 bg-red-50" testId="trench-detail-error">
          <div className="text-red-900 text-sm leading-6">{err}</div>
        </SurfaceCard>
      ) : !doc ? (
        <SurfaceCard testId="trench-detail-empty">
          <div className="min-h-[12rem] flex items-center justify-center text-slate-500 text-sm">{t("Asset not found.")}</div>
        </SurfaceCard>
      ) : (
        <>
          <DetailPageHero
            backHref={`${portalBase}/assets`}
            backLabel={backLabel}
            kicker={t(doc.asset_type || "Trench Box")}
            title={doc.asset_id}
            description={[doc.size, doc.color, doc.current_location].filter(Boolean).join(" · ") || t("Live asset record")}
            chips={(
              <>
                <span className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-bold uppercase tracking-[0.12em] ${STATUS_COLOR[doc.operational_status] || "bg-slate-50 text-slate-700 border-slate-300"}`} data-testid="trench-detail-status-badge">
                  {t(doc.operational_status || "Available")}
                </span>
                {doc.condition ? <span className="inline-flex items-center rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-bold text-slate-700" data-testid="trench-detail-condition-chip">{t(doc.condition)}</span> : null}
              </>
            )}
            toolbar={(
              <div className="flex flex-wrap gap-2" data-testid="trench-detail-actions">
                <Button type="button" onClick={() => setAssignOpen(true)} disabled={!canAssign} className="bg-cyan-700 hover:bg-cyan-800 text-white" data-testid="btn-assign-to-project">
                  <Send className="w-3.5 h-3.5 mr-1.5" /> {t("Assign")}
                </Button>
                <Button type="button" variant="outline" onClick={() => setReturnOpen(true)} disabled={!canReturn} className="border-cyan-700 text-cyan-800 hover:bg-cyan-50" data-testid="btn-return-from-project">
                  <ArrowDownToLine className="w-3.5 h-3.5 mr-1.5" /> {t("Return")}
                </Button>
                <Button type="button" variant="outline" onClick={() => setEditOpen(true)} className="border-slate-400 text-slate-800 hover:bg-slate-50" data-testid="btn-edit-asset">
                  <Pencil className="w-3.5 h-3.5 mr-1.5" /> {t("Edit")}
                </Button>
                <Button type="button" variant="outline" onClick={() => setStatusOpen(true)} className="border-slate-400 text-slate-800 hover:bg-slate-50" data-testid="btn-change-status">
                  <Activity className="w-3.5 h-3.5 mr-1.5" /> {t("Status")}
                </Button>
                <Button type="button" variant="outline" onClick={() => setRetireOpen(true)} className="border-red-300 text-red-700 hover:bg-red-50" disabled={doc.operational_status === "Retired"} data-testid="btn-retire-asset">
                  <Power className="w-3.5 h-3.5 mr-1.5" /> {t("Retire")}
                </Button>
              </div>
            )}
            testId="trench-detail-hero"
          />

          {!canAssign && doc.operational_status !== "Assigned" ? (
            <div className="rounded-[1.25rem] border border-amber-200 bg-amber-50 px-4 py-3 text-[11px] font-mono text-amber-900" data-testid="trench-detail-assignment-note">
              {t("Asset is")} {t(doc.operational_status)} — {t("clear before assigning")}
            </div>
          ) : null}

          {(doc.needs_review || doc.missing_serial_number || doc.tabulated_data_missing) && (
            <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-2" data-testid="trench-detail-alerts">
              {doc.missing_serial_number && (
                <div className="flex items-start gap-2 p-3 border border-amber-300 bg-amber-50 rounded text-amber-900 text-sm" data-testid="alert-missing-serial">
                  <FileWarning className="w-4 h-4 mt-0.5 shrink-0" />
                  <div>
                    <div className="font-bold">{t("Missing Serial Number")}</div>
                    <div className="text-xs">{t("Physical plate verification required before use.")}</div>
                  </div>
                </div>
              )}
              {doc.needs_review && (
                <div className="flex items-start gap-2 p-3 border border-amber-300 bg-amber-50 rounded text-amber-900 text-sm" data-testid="alert-needs-review">
                  <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
                  <div>
                    <div className="font-bold">{t("Needs Review")}</div>
                    <div className="text-xs">{doc.needs_review_reason || t("Manufacturer or model data not yet verified.")}</div>
                  </div>
                </div>
              )}
              {doc.tabulated_data_missing && (
                <div className="flex items-start gap-2 p-3 border border-amber-300 bg-amber-50 rounded text-amber-900 text-sm" data-testid="alert-missing-tabdata">
                  <BookOpen className="w-4 h-4 mt-0.5 shrink-0" />
                  <div>
                    <div className="font-bold">{t("Tabulated Data Missing")}</div>
                    <div className="text-xs">
                      {t("No manufacturer PDF linked to this asset yet. ")}
                      <Link to={`${portalBase}/tabulated-data`} className="underline">{t("Browse library")}</Link>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          <SurfaceCard eyebrow={t("Identification")} title={t("Identity and build profile")} testId="trench-detail-identification">
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-x-6 gap-y-3">
              <Field label={t("Asset ID")}     value={doc.asset_id}     mono testId="f-asset-id" />
              <Field label={t("Type")}         value={t(doc.asset_type || "Trench Box")} testId="f-type" />
              <Field label={t("Size")}         value={doc.size} testId="f-size" />
              <Field label={t("Serial #")}     value={doc.serial_number} mono testId="f-serial" />
              <Field label={t("Manufacturer")} value={doc.manufacturer} testId="f-mfr" />
              <Field label={t("Model")}        value={doc.model} testId="f-model" />
              <Field label={t("Color")}        value={doc.color} testId="f-color" />
              <Field label={t("Condition")}    value={t(doc.condition || "Good")} testId="f-condition" />
            </div>
          </SurfaceCard>

          {doc.asset_type === "Road Plate" && (
            <SurfaceCard eyebrow={t("Road Plate")} title={t("Specs and condition")} testId="trench-detail-roadplate">
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-x-6 gap-y-3">
                <Field label={t("Length (in)")}             value={doc.length_in} mono testId="f-rp-length" />
                <Field label={t("Width (in)")}              value={doc.width_in} mono testId="f-rp-width" />
                <Field label={t("Thickness (in)")}          value={doc.thickness_in} mono testId="f-rp-thickness" />
                <Field label={t("Weight (lb)")}             value={doc.weight_lbs} mono testId="f-rp-weight" />
                <Field label={t("Material")}                value={doc.material} testId="f-rp-material" />
                <Field label={t("Rated Capacity (lb)")}     value={doc.rated_capacity_lb} mono testId="f-rp-capacity" />
                <Field label={t("Surface Condition")}       value={doc.surface_condition ? t(doc.surface_condition) : null} testId="f-rp-surface" />
                <Field label={t("Edge Condition")}          value={doc.edge_condition ? t(doc.edge_condition) : null} testId="f-rp-edge" />
                <Field label={t("Lifting Point Condition")} value={doc.lifting_point_condition ? t(doc.lifting_point_condition) : null} testId="f-rp-lifting" />
                <Field label={t("Anti-Skid Status")}        value={doc.anti_skid_status ? t(doc.anti_skid_status) : null} testId="f-rp-antiskid" />
                <Field label={t("Color / Markings")}        value={doc.markings} testId="f-rp-markings" />
              </div>
            </SurfaceCard>
          )}

          <SurfaceCard eyebrow={t("Operational")} title={t("Live field posture")} testId="trench-detail-operational">
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-x-6 gap-y-3">
              <Field label={t("Status")}            value={t(doc.operational_status || "Available")} testId="f-status" />
              <Field label={t("Current Location")}  value={doc.current_location} testId="f-location" />
              <Field label={t("Current Project")}   value={doc.current_project_name} testId="f-project" />
              <Field label={t("Project Number")}    value={doc.current_project_number} mono testId="f-project-number" />
              <Field label={t("Superintendent")}    value={doc.current_superintendent} testId="f-superintendent" />
              <Field label={t("Foreman")}           value={doc.current_foreman} testId="f-foreman" />
              <Field label={t("Yard")}              value={doc.yard_location} testId="f-yard" />
              <Field label={t("Last Inspection")}   value={doc.last_inspection_at ? doc.last_inspection_at.slice(0, 10) : null} testId="f-last-insp" />
              <Field label={t("Next Inspection Due")} value={doc.next_inspection_due ? doc.next_inspection_due.slice(0, 10) : null} testId="f-next-insp" />
              <Field label={t("Compliance Expires")} value={doc.certification_expires_at ? doc.certification_expires_at.slice(0, 10) : null} testId="f-cert-exp" />
              <Field label={t("Last Repair")}       value={doc.last_repair_at ? doc.last_repair_at.slice(0, 10) : null} testId="f-last-repair" />
            </div>
          </SurfaceCard>

          <section className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3" data-testid="trench-detail-qr-and-tabdata">
            <Link to={`/trench-safety/assets/${doc.asset_id}`} className="wp17-panel p-4 hover:border-cyan-600 hover:shadow transition block" data-testid="trench-detail-qr-link">
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold inline-flex items-center gap-1"><ScanLine className="w-3.5 h-3.5" /> {t("Field View")}</div>
              <div className="font-display text-lg font-black text-slate-900 mt-1">{t("Open QR Field View")}</div>
              <div className="text-xs text-slate-600 mt-1">{t("Mobile-first read-only crew view. Safe to scan in the field.")}</div>
            </Link>
            <Link to={`${portalBase}/tabulated-data`} className="wp17-panel p-4 hover:border-cyan-600 hover:shadow transition block" data-testid="trench-detail-tabdata-link">
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold inline-flex items-center gap-1"><BookOpen className="w-3.5 h-3.5" /> {t("Reference")}</div>
              <div className="font-display text-lg font-black text-slate-900 mt-1">{t("Browse Tabulated Data Library")}</div>
              <div className="text-xs text-slate-600 mt-1">{t("Manufacturer-engineered OSHA tabulated PDFs.")}</div>
            </Link>
          </section>

          <section className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3" data-testid="trench-detail-history">
            <div className="wp17-panel p-4">
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 mb-2">{t("Recent Inspections")}</div>
              {insp.length === 0 ? (
                <div className="text-xs text-slate-400">{t("No inspections yet.")}</div>
              ) : (
                <ul className="text-sm divide-y divide-slate-100">
                  {insp.map((i) => (
                    <li key={i.id} className="py-1.5">
                      <div className="font-bold text-slate-900">{t(i.inspection_type)} · <span className={i.result === "Fail" ? "text-red-700" : i.result === "Pass" ? "text-emerald-700" : "text-amber-700"}>{t(i.result)}</span></div>
                      <div className="text-xs text-slate-500 font-mono">{i.submitted_at?.slice(0, 16)} · {i.inspector_name}</div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div className="wp17-panel p-4">
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 mb-2">{t("Recent Repairs")}</div>
              {reps.length === 0 ? (
                <div className="text-xs text-slate-400">{t("No repairs on file.")}</div>
              ) : (
                <ul className="text-sm divide-y divide-slate-100">
                  {reps.map((r) => (
                    <li key={r.id} className="py-1.5">
                      <div className="font-bold text-slate-900">{r.issue_description?.slice(0, 60) || "—"}</div>
                      <div className="text-xs text-slate-500 font-mono">{r.status} · {r.opened_at?.slice(0, 10)}</div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div className="wp17-panel p-4">
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 mb-2">{t("Recent Deployments")}</div>
              {deps.length === 0 ? (
                <div className="text-xs text-slate-400">{t("No deployments recorded.")}</div>
              ) : (
                <ul className="text-sm divide-y divide-slate-100">
                  {deps.map((d) => (
                    <li key={d.id} className="py-1.5">
                      <div className="font-bold text-slate-900">{d.project_name || "—"}</div>
                      <div className="text-xs text-slate-500 font-mono">{d.assigned_at?.slice(0, 10)}{d.returned_at ? ` → ${d.returned_at.slice(0, 10)}` : ` · ${t("active")}`}</div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </section>

          <SurfaceCard eyebrow={<span className="inline-flex items-center gap-1"><History className="w-3.5 h-3.5" /> {t("Deployment History")}</span>} title={t("Full deployment timeline")} testId="trench-detail-deployment-history">
            <DataTable
              columns={deploymentColumns}
              rows={deploymentRows}
              rowKey={(row) => row.id}
              emptyText={t("No deployments recorded.")}
              density="compact"
              tableMinWidth={880}
              data-testid="deployment-history-table"
              getRowTestId={(row) => `deployment-row-${row.id}`}
            />
          </SurfaceCard>

          <section className="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-3" data-testid="trench-detail-cmd-panels">
            <HoldsPanel asset={doc} onChange={reload} />
            <CertificationsPanel asset={doc} onChange={reload} />
            <InspectionsPanel asset={doc} onChange={reload} />
            <AuditTimelinePanel asset={doc} />
          </section>

          <section className="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-3" data-testid="trench-detail-phase7-panels">
            <QRManagementPanel asset={doc} />
            <PhotoManagementPanel asset={doc} />
          </section>

          <div className="mt-6 p-4 border border-amber-300 bg-amber-50 rounded-[1.25rem] text-sm text-amber-900" data-testid="trench-detail-coaching">
            <ShieldAlert className="w-4 h-4 inline mr-1.5 -mt-0.5" />
            <strong>{t("Coaching:")}</strong>{" "}
            {t("Report damage before the box goes into the trench. A box on Inspection Hold is not available for use.")}
          </div>

          {/* Modals */}
          <AssignToProjectDialog
            open={assignOpen}
            onOpenChange={setAssignOpen}
            asset={doc}
            onAssigned={reload}
          />
          <ReturnFromProjectDialog
            open={returnOpen}
            onOpenChange={setReturnOpen}
            asset={doc}
            onReturned={reload}
          />
          <EditAssetDialog open={editOpen} onOpenChange={setEditOpen} asset={doc} onSaved={reload} />
          <StatusChangeDialog open={statusOpen} onOpenChange={setStatusOpen} asset={doc} onChanged={reload} />
          <RetireAssetDialog open={retireOpen} onOpenChange={setRetireOpen} asset={doc} onRetired={reload} />
        </>
      )}
    </TrenchSafetyShell>
  );
}
