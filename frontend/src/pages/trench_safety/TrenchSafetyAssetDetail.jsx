// Trench Safety Asset Detail — read-only canonical view for Phase 3.
//
// Action buttons are NOT included in Phase 3 (per OMEGA directive:
// "Do NOT add edit/create/repair/inspection action buttons unless
// already fully functional through Phase 2 backend and permission-safe").
// Phase 3 is view-only; lifecycle actions land in Phase 6 once the
// inspection / repair UIs are built.
import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  Loader2, ArrowLeft, AlertTriangle, FileWarning, ShieldAlert,
  ScanLine, BookOpen, Send, ArrowDownToLine, History,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";
import TrenchSafetyShell from "@/pages/trench_safety/TrenchSafetyShell";
import {
  AssignToProjectDialog,
  ReturnFromProjectDialog,
} from "@/pages/trench_safety/TrenchSafetyAssignDialogs";

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

export default function TrenchSafetyAssetDetail() {
  const { t } = useT();
  const { assetId } = useParams();
  const [doc, setDoc] = useState(null);
  const [insp, setInsp] = useState([]);
  const [reps, setReps] = useState([]);
  const [deps, setDeps] = useState([]);
  const [allDeps, setAllDeps] = useState([]);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);
  const [assignOpen, setAssignOpen] = useState(false);
  const [returnOpen, setReturnOpen] = useState(false);
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

  return (
    <TrenchSafetyShell active="assets">
      <Link to="/safety/trench-safety/assets" className="inline-flex items-center text-cyan-800 hover:text-cyan-900 text-xs font-bold uppercase tracking-[0.12em] mb-3" data-testid="trench-detail-back">
        <ArrowLeft className="w-3.5 h-3.5 mr-1" /> {t("Back to Trench Equipment")}
      </Link>

      {loading ? (
        <div className="flex items-center gap-2 text-slate-500" data-testid="trench-detail-loading">
          <Loader2 className="w-5 h-5 animate-spin" /> {t("Loading asset…")}
        </div>
      ) : err ? (
        <div className="p-4 border border-red-300 bg-red-50 rounded text-red-900 text-sm" data-testid="trench-detail-error">{err}</div>
      ) : !doc ? (
        <div className="p-8 text-center text-slate-500" data-testid="trench-detail-empty">{t("Asset not found.")}</div>
      ) : (
        <>
          {/* Header */}
          <div className="flex flex-wrap items-end gap-4 justify-between" data-testid="trench-detail-header">
            <div>
              <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-cyan-700 font-bold">{t(doc.asset_type || "Trench Box")}</span>
              <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 leading-none mt-1">{doc.asset_id}</h1>
              <p className="text-slate-600 text-sm mt-2">{doc.size || ""} {doc.color ? `· ${doc.color}` : ""}</p>
            </div>
            <span className={`inline-block px-3 py-1.5 rounded border text-xs font-bold uppercase tracking-[0.12em] ${STATUS_COLOR[doc.operational_status] || "bg-slate-50 text-slate-700 border-slate-300"}`} data-testid="trench-detail-status-badge">
              {t(doc.operational_status || "Available")}
            </span>
          </div>

          {/* Phase 4A action bar */}
          <div className="mt-3 flex flex-wrap gap-2" data-testid="trench-detail-actions">
            <Button
              type="button"
              onClick={() => setAssignOpen(true)}
              disabled={!canAssign}
              className="bg-cyan-700 hover:bg-cyan-800 text-white"
              data-testid="btn-assign-to-project"
            >
              <Send className="w-3.5 h-3.5 mr-1.5" />
              {t("Assign to Project")}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => setReturnOpen(true)}
              disabled={!canReturn}
              className="border-cyan-700 text-cyan-800 hover:bg-cyan-50"
              data-testid="btn-return-from-project"
            >
              <ArrowDownToLine className="w-3.5 h-3.5 mr-1.5" />
              {t("Return from Project")}
            </Button>
            {!canAssign && doc.operational_status !== "Assigned" && (
              <span className="text-[11px] text-slate-500 self-center font-mono">
                {t("Asset is")} {t(doc.operational_status)} — {t("clear before assigning")}.
              </span>
            )}
          </div>

          {/* Needs-Review / Missing-SN alerts */}
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
                      <Link to="/safety/trench-safety/tabulated-data" className="underline">{t("Browse library")}</Link>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Identification */}
          <section className="mt-6 bg-white border border-slate-200 rounded-md p-4" data-testid="trench-detail-identification">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold mb-2">{t("Identification")}</div>
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
          </section>

          {/* Operational */}
          <section className="mt-4 bg-white border border-slate-200 rounded-md p-4" data-testid="trench-detail-operational">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold mb-2">{t("Operational")}</div>
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
              <Field label={t("Certification Expires")} value={doc.certification_expires_at ? doc.certification_expires_at.slice(0, 10) : null} testId="f-cert-exp" />
              <Field label={t("Last Repair")}       value={doc.last_repair_at ? doc.last_repair_at.slice(0, 10) : null} testId="f-last-repair" />
            </div>
          </section>

          {/* QR + linked Tabulated Data */}
          <section className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3" data-testid="trench-detail-qr-and-tabdata">
            <Link to={`/trench-safety/assets/${doc.asset_id}`} className="bg-white border border-slate-200 rounded-md p-4 hover:border-cyan-600 hover:shadow transition" data-testid="trench-detail-qr-link">
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold inline-flex items-center gap-1"><ScanLine className="w-3.5 h-3.5" /> {t("Field View")}</div>
              <div className="font-display text-lg font-black text-slate-900 mt-1">{t("Open QR Field View")}</div>
              <div className="text-xs text-slate-600 mt-1">{t("Mobile-first read-only crew view. Safe to scan in the field.")}</div>
            </Link>
            <Link to="/safety/trench-safety/tabulated-data" className="bg-white border border-slate-200 rounded-md p-4 hover:border-cyan-600 hover:shadow transition" data-testid="trench-detail-tabdata-link">
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold inline-flex items-center gap-1"><BookOpen className="w-3.5 h-3.5" /> {t("Reference")}</div>
              <div className="font-display text-lg font-black text-slate-900 mt-1">{t("Browse Tabulated Data Library")}</div>
              <div className="text-xs text-slate-600 mt-1">{t("Manufacturer-engineered OSHA tabulated PDFs.")}</div>
            </Link>
          </section>

          {/* Recent inspections / repairs / deployments */}
          <section className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3" data-testid="trench-detail-history">
            <div className="bg-white border border-slate-200 rounded-md p-4">
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
            <div className="bg-white border border-slate-200 rounded-md p-4">
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
            <div className="bg-white border border-slate-200 rounded-md p-4">
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

          {/* Full Deployment History timeline (Phase 4A) */}
          <section className="mt-4 bg-white border border-slate-200 rounded-md p-4" data-testid="trench-detail-deployment-history">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold mb-2 inline-flex items-center gap-1">
              <History className="w-3.5 h-3.5" /> {t("Deployment History")}
            </div>
            {allDeps.length === 0 ? (
              <div className="text-xs text-slate-400 py-2">{t("No deployments recorded.")}</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm" data-testid="deployment-history-table">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">{t("Project")}</th>
                      <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">{t("Project #")}</th>
                      <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">{t("Superintendent")}</th>
                      <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">{t("Foreman")}</th>
                      <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">{t("Assigned By")}</th>
                      <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">{t("Assigned")}</th>
                      <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">{t("Returned")}</th>
                      <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">{t("Source")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {allDeps.map((d) => (
                      <tr key={d.id} className="border-t border-slate-100" data-testid={`deployment-row-${d.id}`}>
                        <td className="px-3 py-2 text-slate-900 font-medium">{d.project_name || "—"}</td>
                        <td className="px-3 py-2 font-mono text-xs text-slate-700">{d.project_number || "—"}</td>
                        <td className="px-3 py-2 text-slate-700 text-xs">{d.superintendent || "—"}</td>
                        <td className="px-3 py-2 text-slate-700 text-xs">{d.foreman || "—"}</td>
                        <td className="px-3 py-2 text-slate-700 text-xs">{d.assigned_by || "—"}</td>
                        <td className="px-3 py-2 text-xs font-mono text-slate-700">{d.assigned_at?.slice(0, 16) || "—"}</td>
                        <td className="px-3 py-2 text-xs font-mono text-slate-700">
                          {d.returned_at ? d.returned_at.slice(0, 16) : <span className="text-emerald-700 font-bold">{t("Active")}</span>}
                        </td>
                        <td className="px-3 py-2 text-xs text-slate-500">{d.source || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* Coaching */}
          <div className="mt-6 p-3 border border-amber-300 bg-amber-50 rounded text-sm text-amber-900" data-testid="trench-detail-coaching">
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
        </>
      )}
    </TrenchSafetyShell>
  );
}
