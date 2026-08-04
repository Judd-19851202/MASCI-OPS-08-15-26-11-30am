import React, { useEffect, useMemo, useState } from "react";
import { CalendarRange, Download, FileUp, RefreshCw, Send, ShieldCheck } from "lucide-react";
import { toast } from "sonner";
import { useSearchParams } from "react-router-dom";
import PmShell from "@/components/PmShell";
import PmProjectSelector from "@/components/pm/command/PmProjectSelector";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { useT } from "@/lib/i18n";
import {
  activatePmProjectScheduleImport,
  createPmProjectScheduleImport,
  downloadPmScheduleExport,
  fetchPmProjectScheduleActivities,
  fetchPmProjectScheduleImportDetail,
  fetchPmProjectScheduleImports,
  fetchPmProjectScheduleLookahead,
  fetchPmProjectScheduleOverview,
  fetchPmProjectScheduleReviewQueue,
  fetchPmProjectScheduleVersions,
  fetchPmProjectScheduleWorkPackages,
  queuePmScheduleEmailExport,
  reviewPmProjectScheduleImportRow,
  savePmProjectScheduleLookahead,
} from "@/lib/projectControlsApi";

const SOURCE_OPTIONS = [
  ["csv", "CSV (runtime certified)"],
  ["primavera_p6", "Primavera P6 (extension lane)"],
  ["ms_project", "Microsoft Project (extension lane)"],
  ["excel", "Excel (extension lane)"],
  ["pdf_review", "PDF review assisted (extension lane)"],
];

const VERSION_OPTIONS = [
  ["master_schedule", "Master schedule"],
  ["pending_revision", "Pending revision"],
  ["baseline_refresh", "Baseline refresh"],
];

const EXPORT_OPTIONS = [
  ["master_schedule_csv", "Master schedule CSV"],
  ["two_week_csv", "Two-week lookahead CSV"],
  ["four_week_csv", "Four-week lookahead CSV"],
  ["crew_plan_csv", "Crew plan CSV"],
  ["equipment_plan_csv", "Equipment plan CSV"],
  ["material_plan_csv", "Material plan CSV"],
  ["work_package_plan_csv", "Work-package plan CSV"],
];

function emptyImportForm() {
  return { file: null, source_kind: "csv", target_version_kind: "master_schedule", version_name: "" };
}

function emptyLookaheadDraft() {
  return { status: "draft", comparison_note: "", tasks_text: "", constraints_text: "" };
}

function fileNameFromResponse(response, fallback) {
  const disposition = response?.headers?.["content-disposition"] || "";
  const match = disposition.match(/filename="?([^\"]+)"?/i);
  return match?.[1] || fallback;
}

function downloadResponseFile(response, fallback) {
  const blob = new Blob([response.data], { type: response.data?.type || "text/csv" });
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileNameFromResponse(response, fallback);
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(url);
}

function buildRowDrafts(rows) {
  return Object.fromEntries((rows || []).map((row) => [row.row_id, { ...(row.selected || {}) }]));
}

function summaryCards(overview) {
  const counts = overview?.counts || {};
  return [
    ["versions", counts.versions || 0],
    ["activities", counts.activities || 0],
    ["work-packages", counts.work_packages || 0],
    ["review-queue-open", counts.review_queue_open || 0],
  ];
}

function joinNamedRefs(rows, key) {
  return (rows || []).map((row) => row?.[key] || row?.label || "").filter(Boolean).join(", ");
}

function joinMaterials(rows) {
  return (rows || []).map((row) => [row?.description || "", row?.quantity || "", row?.unit || ""].filter(Boolean).join(" | ")).filter(Boolean).join("\n");
}

function joinConstraints(rows) {
  return (rows || []).map((row) => [row?.title || "", row?.category || "", row?.status || "", row?.notes || ""].filter(Boolean).join(" | ")).filter(Boolean).join("\n");
}

function parseNamedRefs(text, idKey, labelKey) {
  return String(text || "").split(",").map((item) => item.trim()).filter(Boolean).map((item) => ({ [idKey]: "", [labelKey]: item }));
}

function parseMaterials(text) {
  return String(text || "").split("\n").map((line) => line.trim()).filter(Boolean).map((line) => {
    const [description = "", quantity = "0", unit = ""] = line.split("|").map((item) => item.trim());
    return { material_id: "", description, quantity: Number(quantity || 0), unit };
  });
}

function parseConstraints(text) {
  return String(text || "").split("\n").map((line) => line.trim()).filter(Boolean).map((line) => {
    const [title = "", category = "unknown", status = "planned", notes = ""] = line.split("|").map((item) => item.trim());
    return { constraint_id: "", title, category, status, notes };
  });
}

function buildLookaheadDraft(lookahead) {
  if (!lookahead) return emptyLookaheadDraft();
  return {
    status: lookahead.status || "draft",
    comparison_note: lookahead.comparison_note || "",
    tasks_text: (lookahead.tasks || []).map((row) => row.label || row.activity_name || row.activity_id || "").filter(Boolean).join("\n"),
    constraints_text: (lookahead.constraints || []).map((row) => row.title || row.label || row.constraint_id || "").filter(Boolean).join("\n"),
  };
}

function buildRowPayload(draft, action) {
  return {
    action,
    activity_id: draft.activity_id || "",
    activity_name: draft.activity_name || "",
    phase_id: draft.phase_id || "",
    work_package_id: draft.work_package_id || "",
    budget_line_id: draft.budget_line_id || "",
    customer_pay_item_number: draft.customer_pay_item_number || "",
    enterprise_work_type_id: draft.enterprise_work_type_id || "",
    project_cost_code: draft.project_cost_code || "",
    planned_start_date: draft.planned_start_date || "",
    planned_finish_date: draft.planned_finish_date || "",
    duration_days: Number(draft.duration_days || 1),
    calendar_name: draft.calendar_name || "Default",
    status: draft.status || "not_started",
    percent_complete: Number(draft.percent_complete || 0),
    owner: draft.owner || "",
    priority: draft.priority || "normal",
    notes: draft.notes || "",
    execution_strategy: draft.execution_strategy || "self_perform",
    planned_crew_ids: parseNamedRefs(draft.planned_crew_text ?? joinNamedRefs(draft.planned_crew_ids, "label"), "crew_id", "label"),
    planned_employee_ids: parseNamedRefs(draft.planned_employee_text ?? joinNamedRefs(draft.planned_employee_ids, "label"), "employee_id", "label"),
    planned_equipment_ids: parseNamedRefs(draft.planned_equipment_text ?? joinNamedRefs(draft.planned_equipment_ids, "label"), "equipment_id", "label"),
    planned_materials: parseMaterials(draft.planned_materials_text ?? joinMaterials(draft.planned_materials)),
    planned_vendor_refs: parseNamedRefs(draft.planned_vendors_text ?? joinNamedRefs(draft.planned_vendor_refs, "vendor_name"), "vendor_id", "vendor_name"),
    planned_subcontractor_refs: parseNamedRefs(draft.planned_subcontractors_text ?? joinNamedRefs(draft.planned_subcontractor_refs, "subcontractor_name"), "vendor_id", "subcontractor_name"),
    planned_production_quantity: Number(draft.planned_production_quantity || 0),
    planned_hours: Number(draft.planned_hours || 0),
    planned_constraints: parseConstraints(draft.planned_constraints_text ?? joinConstraints(draft.planned_constraints)),
    review_note: draft.review_note || "",
  };
}

function renderSourceValues(sourceValues) {
  return Object.entries(sourceValues || {}).slice(0, 10).map(([key, value]) => (
    <div key={key}><strong>{key}:</strong> {String(value || "—")}</div>
  ));
}

export default function PmProjectSchedule() {
  const { t } = useT();
  const [params, setParams] = useSearchParams();
  const [projectNumber, setProjectNumber] = useState(params.get("project_number") || "");
  const [loading, setLoading] = useState(false);
  const [working, setWorking] = useState(false);
  const [overview, setOverview] = useState(null);
  const [versions, setVersions] = useState([]);
  const [activities, setActivities] = useState([]);
  const [workPackages, setWorkPackages] = useState([]);
  const [imports, setImports] = useState([]);
  const [reviewQueue, setReviewQueue] = useState([]);
  const [lookahead, setLookahead] = useState(null);
  const [lookaheadDraft, setLookaheadDraft] = useState(emptyLookaheadDraft());
  const [importForm, setImportForm] = useState(emptyImportForm());
  const [activeImportId, setActiveImportId] = useState("");
  const [importDetail, setImportDetail] = useState(null);
  const [rowDrafts, setRowDrafts] = useState({});
  const [exportKind, setExportKind] = useState("master_schedule_csv");
  const [emailRecipients, setEmailRecipients] = useState("");

  useEffect(() => {
    const next = params.get("project_number") || "";
    setProjectNumber(next);
  }, [params]);

  const load = async (pn = projectNumber, pinnedImportId = "") => {
    if (!pn) return;
    setLoading(true);
    try {
      const [overviewData, versionData, importData, reviewData, lookaheadData] = await Promise.all([
        fetchPmProjectScheduleOverview(pn),
        fetchPmProjectScheduleVersions(pn),
        fetchPmProjectScheduleImports(pn),
        fetchPmProjectScheduleReviewQueue(pn),
        fetchPmProjectScheduleLookahead(pn).catch(() => null),
      ]);
      setOverview(overviewData || null);
      setVersions(versionData?.items || []);
      setImports(importData?.items || []);
      setReviewQueue(reviewData?.items || []);
      setLookahead(lookaheadData || null);
      setLookaheadDraft(buildLookaheadDraft(lookaheadData));
      const activeVersionId = overviewData?.active_version?.version_id || versionData?.items?.find((item) => item.status === "active")?.version_id || "";
      if (activeVersionId) {
        const [activityData, workPackageData] = await Promise.all([
          fetchPmProjectScheduleActivities(pn, activeVersionId),
          fetchPmProjectScheduleWorkPackages(pn, activeVersionId),
        ]);
        setActivities(activityData?.items || []);
        setWorkPackages(workPackageData?.items || []);
      } else {
        setActivities([]);
        setWorkPackages([]);
      }
      const nextImportId = pinnedImportId || activeImportId || importData?.items?.[0]?.import_id || "";
      setActiveImportId(nextImportId);
      if (nextImportId) {
        const detail = await fetchPmProjectScheduleImportDetail(pn, nextImportId);
        setImportDetail(detail || null);
        setRowDrafts(buildRowDrafts(detail?.rows || []));
      } else {
        setImportDetail(null);
        setRowDrafts({});
      }
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not load the governed schedule workspace."));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (projectNumber) load(projectNumber);
  }, [projectNumber]);

  const setProject = (pn) => {
    setParams((prev) => {
      const next = new URLSearchParams(prev);
      if (pn) next.set("project_number", pn);
      else next.delete("project_number");
      return next;
    });
  };

  const onImport = async () => {
    if (!projectNumber || !importForm.file) return;
    setWorking(true);
    try {
      const payload = await createPmProjectScheduleImport(projectNumber, importForm);
      const nextImportId = payload?.session?.import_id || payload?.duplicate_of || "";
      toast.success(t("Schedule import staged for PM review."));
      setImportForm(emptyImportForm());
      await load(projectNumber, nextImportId);
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not stage the schedule import."));
    } finally {
      setWorking(false);
    }
  };

  const onRowDraft = (rowId, key, value) => {
    setRowDrafts((prev) => ({ ...prev, [rowId]: { ...(prev[rowId] || {}), [key]: value } }));
  };

  const onReviewRow = async (rowId, action) => {
    if (!projectNumber || !activeImportId) return;
    setWorking(true);
    try {
      await reviewPmProjectScheduleImportRow(projectNumber, activeImportId, rowId, buildRowPayload(rowDrafts[rowId] || {}, action));
      toast.success(action === "approve" ? t("Schedule row approved.") : action === "reject" ? t("Schedule row rejected.") : t("Schedule row returned to review."));
      await load(projectNumber, activeImportId);
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not update the schedule row."));
    } finally {
      setWorking(false);
    }
  };

  const onActivateImport = async () => {
    if (!projectNumber || !activeImportId) return;
    setWorking(true);
    try {
      await activatePmProjectScheduleImport(projectNumber, activeImportId);
      toast.success(t("Governed schedule version activated."));
      await load(projectNumber, activeImportId);
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not activate the schedule version."));
    } finally {
      setWorking(false);
    }
  };

  const onExport = async () => {
    const versionId = overview?.active_version?.version_id;
    if (!projectNumber || !versionId) return;
    try {
      const response = await downloadPmScheduleExport(projectNumber, versionId, exportKind);
      downloadResponseFile(response, `${projectNumber}-${exportKind}.csv`);
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not export the schedule view."));
    }
  };

  const onQueueEmail = async () => {
    const versionId = overview?.active_version?.version_id;
    if (!projectNumber || !versionId || !emailRecipients.trim()) return;
    try {
      await queuePmScheduleEmailExport(projectNumber, {
        export_kind: exportKind,
        version_id: versionId,
        recipients: emailRecipients.split(",").map((item) => item.trim()).filter(Boolean),
      });
      toast.success(t("Email export queued for governed review."));
      await load(projectNumber, activeImportId);
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not queue the email export."));
    }
  };

  const onSaveLookahead = async () => {
    if (!projectNumber) return;
    setWorking(true);
    try {
      const response = await savePmProjectScheduleLookahead(projectNumber, {
        status: lookaheadDraft.status,
        comparison_note: lookaheadDraft.comparison_note,
        tasks: lookaheadDraft.tasks_text.split("\n").map((row) => row.trim()).filter(Boolean).map((label, index) => ({ task_id: `manual-${index + 1}`, label })),
        constraints: lookaheadDraft.constraints_text.split("\n").map((row) => row.trim()).filter(Boolean).map((title, index) => ({ constraint_id: `manual-${index + 1}`, title })),
      });
      setLookahead(response?.lookahead || null);
      setLookaheadDraft(buildLookaheadDraft(response?.lookahead || null));
      toast.success(t("Lookahead overlay saved."));
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not save the lookahead overlay."));
    } finally {
      setWorking(false);
    }
  };

  const cards = useMemo(() => summaryCards(overview), [overview]);
  const importRows = importDetail?.rows || [];
  const activeVersion = overview?.active_version || null;

  return (
    <PmShell title={t("Project Schedule")} section="jobs" subtitle={t("Governed schedule imports, work packages, assignments, and lookahead overlays without breaking baseline truth.")}>
      <div className="space-y-6" data-testid="pm-project-schedule-page">
        <div className="rounded-[1.75rem] border border-white/30 bg-white/85 p-5 shadow-sm backdrop-blur" data-testid="pm-project-schedule-header-card">
          <div className="grid gap-4 lg:grid-cols-[1fr_auto] lg:items-end">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">{t("Operational planning spine")}</div>
              <h1 className="mt-2 text-3xl font-black text-slate-900">{t("Project Schedule Authority")}</h1>
              <p className="mt-2 max-w-3xl text-sm text-slate-600">{t("The schedule stays connected to work packages, budget lines, pay items, enterprise work types, work blocks, daily reports, and actual production. Imports remain review-first and advisory only until a PM approves activation.")}</p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Button type="button" variant="outline" onClick={() => load(projectNumber, activeImportId)} data-testid="pm-project-schedule-refresh-button">
                <RefreshCw className="mr-2 h-4 w-4" /> {t("Refresh")}
              </Button>
              <Button type="button" variant="outline" onClick={onExport} disabled={!activeVersion} data-testid="pm-project-schedule-export-button">
                <Download className="mr-2 h-4 w-4" /> {t("Export view")}
              </Button>
            </div>
          </div>
          <div className="mt-4 max-w-sm" data-testid="pm-project-schedule-project-picker-shell">
            <PmProjectSelector projectNumber={projectNumber} onChange={setProject} />
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-4" data-testid="pm-project-schedule-summary-grid">
          {cards.map(([label, value]) => (
            <div key={label} className="rounded-[1.5rem] border border-white/30 bg-white/85 p-4 shadow-sm" data-testid={`pm-project-schedule-summary-${label}`}>
              <div className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">{t(String(label).replace(/-/g, " "))}</div>
              <div className="mt-2 text-3xl font-black text-slate-900">{value}</div>
            </div>
          ))}
        </div>

        <Alert data-testid="pm-project-schedule-guardrail-alert">
          <ShieldCheck className="h-4 w-4" />
          <AlertTitle>{t("Constitutional guardrails")}</AlertTitle>
          <AlertDescription>
            {t("CSV is the production-certified import lane in C4. P6, Microsoft Project, Excel, and PDF review-assisted lanes are architected but remain governed extension paths until they are runtime-tested. Daily Reports continue as actual-execution truth.")}
          </AlertDescription>
        </Alert>

        <Tabs defaultValue="imports" className="space-y-4" data-testid="pm-project-schedule-tabs">
          <TabsList data-testid="pm-project-schedule-tabs-list">
            <TabsTrigger value="imports" data-testid="pm-project-schedule-imports-tab">{t("Imports")}</TabsTrigger>
            <TabsTrigger value="schedule" data-testid="pm-project-schedule-active-tab">{t("Active schedule")}</TabsTrigger>
            <TabsTrigger value="lookahead" data-testid="pm-project-schedule-lookahead-tab">{t("Lookahead")}</TabsTrigger>
            <TabsTrigger value="review" data-testid="pm-project-schedule-review-tab">{t("Review queue")}</TabsTrigger>
          </TabsList>

          <TabsContent value="imports" className="space-y-6" data-testid="pm-project-schedule-imports-panel">
            <section className="rounded-[1.75rem] border border-white/30 bg-white/85 p-5 shadow-sm" data-testid="pm-project-schedule-import-upload-section">
              <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
                <div className="space-y-4">
                  <div>
                    <h2 className="text-xl font-black text-slate-900">{t("Governed import")}</h2>
                    <p className="mt-1 text-sm text-slate-600">{t("Workflow: import → suggestions → PM review → PM edits → PM approval → activation. Nothing activates automatically.")}</p>
                  </div>
                  <div className="grid gap-3 md:grid-cols-2">
                    <div>
                      <label className="mb-1 block text-xs font-semibold uppercase tracking-[0.18em] text-slate-500" htmlFor="pm-schedule-source-kind">{t("Source kind")}</label>
                      <select id="pm-schedule-source-kind" className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm" value={importForm.source_kind} onChange={(event) => setImportForm((prev) => ({ ...prev, source_kind: event.target.value }))} data-testid="pm-project-schedule-source-kind-select">
                        {SOURCE_OPTIONS.map(([value, label]) => <option key={value} value={value}>{t(label)}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="mb-1 block text-xs font-semibold uppercase tracking-[0.18em] text-slate-500" htmlFor="pm-schedule-version-kind">{t("Target version")}</label>
                      <select id="pm-schedule-version-kind" className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm" value={importForm.target_version_kind} onChange={(event) => setImportForm((prev) => ({ ...prev, target_version_kind: event.target.value }))} data-testid="pm-project-schedule-target-version-select">
                        {VERSION_OPTIONS.map(([value, label]) => <option key={value} value={value}>{t(label)}</option>)}
                      </select>
                    </div>
                    <Input value={importForm.version_name} onChange={(event) => setImportForm((prev) => ({ ...prev, version_name: event.target.value }))} placeholder={t("Version name (optional)")} data-testid="pm-project-schedule-version-name-input" />
                    <Input type="file" accept=".csv,.xlsx,.xlsm,.pdf,.xer,.xml,.mpp" onChange={(event) => setImportForm((prev) => ({ ...prev, file: event.target.files?.[0] || null }))} data-testid="pm-project-schedule-file-input" />
                  </div>
                  <div className="flex justify-end">
                    <Button type="button" onClick={onImport} disabled={!projectNumber || !importForm.file || working} data-testid="pm-project-schedule-upload-button">
                      <FileUp className="mr-2 h-4 w-4" /> {working ? t("Working…") : t("Stage import")}
                    </Button>
                  </div>
                </div>
                <div className="rounded-[1.5rem] border border-slate-200 bg-slate-50 p-4" data-testid="pm-project-schedule-import-session-list">
                  <div className="flex items-center justify-between gap-3">
                    <h3 className="text-sm font-black uppercase tracking-[0.22em] text-slate-600">{t("Recent imports")}</h3>
                    <Badge variant="secondary" data-testid="pm-project-schedule-import-count-badge">{imports.length}</Badge>
                  </div>
                  <div className="mt-3 space-y-3">
                    {imports.map((row) => (
                      <button key={row.import_id} type="button" className={`w-full rounded-2xl border p-3 text-left transition ${activeImportId === row.import_id ? "border-emerald-300 bg-emerald-50" : "border-slate-200 bg-white hover:border-slate-300"}`} onClick={async () => { setActiveImportId(row.import_id); const detail = await fetchPmProjectScheduleImportDetail(projectNumber, row.import_id); setImportDetail(detail); setRowDrafts(buildRowDrafts(detail?.rows || [])); }} data-testid={`pm-project-schedule-import-card-${row.import_id}`}>
                        <div className="flex items-center justify-between gap-3">
                          <div className="font-semibold text-slate-900">{row.filename}</div>
                          <Badge variant={row.status === "activated" ? "default" : "secondary"}>{row.status}</Badge>
                        </div>
                        <div className="mt-2 text-xs text-slate-500">{row.source_kind} · {row.target_version_kind} · {row.total_rows} {t("rows")}</div>
                      </button>
                    ))}
                    {!loading && imports.length === 0 ? <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-4 text-sm text-slate-500" data-testid="pm-project-schedule-import-empty-state">{t("No staged schedule imports yet.")}</div> : null}
                  </div>
                </div>
              </div>
            </section>

            {importDetail ? (
              <section className="rounded-[1.75rem] border border-white/30 bg-white/85 p-5 shadow-sm" data-testid="pm-project-schedule-import-detail-section">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-slate-900">{t("Review staged rows")}</h2>
                    <p className="mt-1 text-sm text-slate-600">{t("Review unresolved links before the schedule can become active planning truth.")}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Badge data-testid="pm-project-schedule-active-import-status">{importDetail?.session?.status || "review_required"}</Badge>
                    <Button type="button" onClick={onActivateImport} disabled={working || !["approved_ready", "partially_reviewed"].includes(importDetail?.session?.status)} data-testid="pm-project-schedule-activate-import-button">{t("Activate schedule")}</Button>
                  </div>
                </div>
                {(importDetail?.session?.parser_warnings || []).length ? (
                  <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900" data-testid="pm-project-schedule-parser-warning-list">
                    {(importDetail.session.parser_warnings || []).map((warning, index) => <div key={`${warning}-${index}`}>{warning}</div>)}
                  </div>
                ) : null}
                <div className="mt-4 space-y-4">
                  {importRows.map((row) => {
                    const draft = rowDrafts[row.row_id] || row.selected || {};
                    return (
                      <div key={row.row_id} className="rounded-[1.5rem] border border-slate-200 bg-slate-50 p-4" data-testid={`pm-project-schedule-row-card-${row.row_id}`}>
                        <div className="flex flex-wrap items-center justify-between gap-3">
                          <div>
                            <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{t("Row")} {row.row_number}</div>
                            <div className="mt-1 font-semibold text-slate-900">{row.normalized?.activity_id || t("Unnumbered activity")} · {row.normalized?.activity_name || t("Needs activity review")}</div>
                          </div>
                          <div className="flex flex-wrap gap-2">
                            <Badge variant="secondary" data-testid={`pm-project-schedule-row-status-${row.row_id}`}>{row.review_status}</Badge>
                            <Badge variant={row.suggestion?.confidence === "high" ? "default" : "outline"}>{row.suggestion?.confidence || "review_required"}</Badge>
                          </div>
                        </div>
                        <div className="mt-3 grid gap-3 lg:grid-cols-2">
                          <div className="rounded-2xl border border-slate-200 bg-white p-3 text-sm text-slate-700" data-testid={`pm-project-schedule-row-source-${row.row_id}`}>
                            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{t("Preserved source")}</div>
                            <div className="mt-2 space-y-1">{renderSourceValues(row.source_values)}</div>
                          </div>
                          <div className="rounded-2xl border border-slate-200 bg-white p-3 text-sm text-slate-700" data-testid={`pm-project-schedule-row-suggestion-${row.row_id}`}>
                            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{t("Suggestion")}</div>
                            <div className="mt-2 space-y-1">{(row.suggestion?.reasons || []).map((reason, index) => <div key={`${reason}-${index}`}>{reason}</div>)}</div>
                            {(row.suggestion?.warnings || []).length ? <div className="mt-2 text-xs text-amber-700">{(row.suggestion.warnings || []).join(" • ")}</div> : null}
                          </div>
                        </div>
                        <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                          <Input value={draft.activity_id || ""} onChange={(event) => onRowDraft(row.row_id, "activity_id", event.target.value)} placeholder={t("Activity ID")} data-testid={`pm-project-schedule-row-activity-id-${row.row_id}`} />
                          <Input value={draft.activity_name || ""} onChange={(event) => onRowDraft(row.row_id, "activity_name", event.target.value)} placeholder={t("Activity name")} data-testid={`pm-project-schedule-row-activity-name-${row.row_id}`} />
                          <Input value={draft.phase_id || ""} onChange={(event) => onRowDraft(row.row_id, "phase_id", event.target.value)} placeholder={t("Phase")} data-testid={`pm-project-schedule-row-phase-${row.row_id}`} />
                          <Input value={draft.work_package_id || ""} onChange={(event) => onRowDraft(row.row_id, "work_package_id", event.target.value)} placeholder={t("Work package")} data-testid={`pm-project-schedule-row-work-package-${row.row_id}`} />
                          <Input value={draft.budget_line_id || ""} onChange={(event) => onRowDraft(row.row_id, "budget_line_id", event.target.value)} placeholder={t("Budget line")} data-testid={`pm-project-schedule-row-budget-line-${row.row_id}`} />
                          <Input value={draft.customer_pay_item_number || ""} onChange={(event) => onRowDraft(row.row_id, "customer_pay_item_number", event.target.value)} placeholder={t("Customer pay item")} data-testid={`pm-project-schedule-row-pay-item-${row.row_id}`} />
                          <Input value={draft.enterprise_work_type_id || ""} onChange={(event) => onRowDraft(row.row_id, "enterprise_work_type_id", event.target.value)} placeholder={t("Enterprise work type")} data-testid={`pm-project-schedule-row-work-type-${row.row_id}`} />
                          <Input value={draft.project_cost_code || ""} onChange={(event) => onRowDraft(row.row_id, "project_cost_code", event.target.value)} placeholder={t("Project cost code")} data-testid={`pm-project-schedule-row-cost-code-${row.row_id}`} />
                          <Input type="date" value={draft.planned_start_date || ""} onChange={(event) => onRowDraft(row.row_id, "planned_start_date", event.target.value)} data-testid={`pm-project-schedule-row-start-${row.row_id}`} />
                          <Input type="date" value={draft.planned_finish_date || ""} onChange={(event) => onRowDraft(row.row_id, "planned_finish_date", event.target.value)} data-testid={`pm-project-schedule-row-finish-${row.row_id}`} />
                          <Input value={draft.duration_days ?? ""} onChange={(event) => onRowDraft(row.row_id, "duration_days", event.target.value)} placeholder={t("Duration days")} data-testid={`pm-project-schedule-row-duration-${row.row_id}`} />
                          <Input value={draft.owner || ""} onChange={(event) => onRowDraft(row.row_id, "owner", event.target.value)} placeholder={t("Owner")} data-testid={`pm-project-schedule-row-owner-${row.row_id}`} />
                          <Input value={draft.priority || ""} onChange={(event) => onRowDraft(row.row_id, "priority", event.target.value)} placeholder={t("Priority")} data-testid={`pm-project-schedule-row-priority-${row.row_id}`} />
                          <Input value={draft.status || ""} onChange={(event) => onRowDraft(row.row_id, "status", event.target.value)} placeholder={t("Status")} data-testid={`pm-project-schedule-row-status-input-${row.row_id}`} />
                          <Input value={draft.planned_production_quantity ?? ""} onChange={(event) => onRowDraft(row.row_id, "planned_production_quantity", event.target.value)} placeholder={t("Planned production qty")} data-testid={`pm-project-schedule-row-production-${row.row_id}`} />
                          <Input value={draft.planned_hours ?? ""} onChange={(event) => onRowDraft(row.row_id, "planned_hours", event.target.value)} placeholder={t("Planned hours")} data-testid={`pm-project-schedule-row-hours-${row.row_id}`} />
                        </div>
                        <div className="mt-4 grid gap-3 xl:grid-cols-2">
                          <Textarea value={draft.planned_crew_text ?? joinNamedRefs(draft.planned_crew_ids, "label")} onChange={(event) => onRowDraft(row.row_id, "planned_crew_text", event.target.value)} placeholder={t("Planned crews, comma separated")} data-testid={`pm-project-schedule-row-crews-${row.row_id}`} />
                          <Textarea value={draft.planned_employee_text ?? joinNamedRefs(draft.planned_employee_ids, "label")} onChange={(event) => onRowDraft(row.row_id, "planned_employee_text", event.target.value)} placeholder={t("Planned employees, comma separated")} data-testid={`pm-project-schedule-row-employees-${row.row_id}`} />
                          <Textarea value={draft.planned_equipment_text ?? joinNamedRefs(draft.planned_equipment_ids, "label")} onChange={(event) => onRowDraft(row.row_id, "planned_equipment_text", event.target.value)} placeholder={t("Planned equipment, comma separated")} data-testid={`pm-project-schedule-row-equipment-${row.row_id}`} />
                          <Textarea value={draft.planned_vendors_text ?? joinNamedRefs(draft.planned_vendor_refs, "vendor_name")} onChange={(event) => onRowDraft(row.row_id, "planned_vendors_text", event.target.value)} placeholder={t("Planned vendors, comma separated")} data-testid={`pm-project-schedule-row-vendors-${row.row_id}`} />
                          <Textarea value={draft.planned_subcontractors_text ?? joinNamedRefs(draft.planned_subcontractor_refs, "subcontractor_name")} onChange={(event) => onRowDraft(row.row_id, "planned_subcontractors_text", event.target.value)} placeholder={t("Planned subcontractors, comma separated")} data-testid={`pm-project-schedule-row-subcontractors-${row.row_id}`} />
                          <Textarea value={draft.planned_materials_text ?? joinMaterials(draft.planned_materials)} onChange={(event) => onRowDraft(row.row_id, "planned_materials_text", event.target.value)} placeholder={t("Materials as description | quantity | unit per line")} data-testid={`pm-project-schedule-row-materials-${row.row_id}`} />
                        </div>
                        <Textarea className="mt-3" value={draft.planned_constraints_text ?? joinConstraints(draft.planned_constraints)} onChange={(event) => onRowDraft(row.row_id, "planned_constraints_text", event.target.value)} placeholder={t("Constraints as title | category | status | notes per line")} data-testid={`pm-project-schedule-row-constraints-${row.row_id}`} />
                        <Textarea className="mt-3" value={draft.notes || ""} onChange={(event) => onRowDraft(row.row_id, "notes", event.target.value)} placeholder={t("Operator notes")} data-testid={`pm-project-schedule-row-notes-${row.row_id}`} />
                        <Textarea className="mt-3" value={draft.review_note || ""} onChange={(event) => onRowDraft(row.row_id, "review_note", event.target.value)} placeholder={t("Why this row is approved, rejected, or still needs review.")} data-testid={`pm-project-schedule-row-review-note-${row.row_id}`} />
                        <div className="mt-4 flex flex-wrap justify-end gap-2">
                          <Button type="button" variant="outline" onClick={() => onReviewRow(row.row_id, "needs_review")} disabled={working} data-testid={`pm-project-schedule-row-needs-review-${row.row_id}`}>{t("Needs review")}</Button>
                          <Button type="button" variant="ghost" onClick={() => onReviewRow(row.row_id, "reject")} disabled={working} data-testid={`pm-project-schedule-row-reject-${row.row_id}`}>{t("Reject")}</Button>
                          <Button type="button" onClick={() => onReviewRow(row.row_id, "approve")} disabled={working} data-testid={`pm-project-schedule-row-approve-${row.row_id}`}>{t("Approve row")}</Button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </section>
            ) : null}
          </TabsContent>

          <TabsContent value="schedule" className="space-y-6" data-testid="pm-project-schedule-active-panel">
            <section className="rounded-[1.75rem] border border-white/30 bg-white/85 p-5 shadow-sm" data-testid="pm-project-schedule-version-section">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-xl font-black text-slate-900">{t("Active governed schedule")}</h2>
                  <p className="mt-1 text-sm text-slate-600">{t("Baseline stays preserved while lookahead overlays and assignment planning remain editable.")}</p>
                </div>
                {activeVersion ? <Badge data-testid="pm-project-schedule-active-version-badge">{activeVersion.version_kind || activeVersion.status}</Badge> : null}
              </div>
              {activeVersion ? (
                <div className="mt-4 grid gap-4 md:grid-cols-4" data-testid="pm-project-schedule-version-metrics-grid">
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><div className="text-xs uppercase tracking-[0.18em] text-slate-500">{t("Version name")}</div><div className="mt-2 text-base font-black text-slate-900" data-testid="pm-project-schedule-active-version-name">{activeVersion.version_name}</div></div>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><div className="text-xs uppercase tracking-[0.18em] text-slate-500">{t("Baseline")}</div><div className="mt-2 text-base font-black text-slate-900" data-testid="pm-project-schedule-baseline-id">{activeVersion.baseline_version_id || "—"}</div></div>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><div className="text-xs uppercase tracking-[0.18em] text-slate-500">{t("Activities")}</div><div className="mt-2 text-2xl font-black text-slate-900" data-testid="pm-project-schedule-activity-count">{activeVersion.counts?.activity_count || activities.length}</div></div>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><div className="text-xs uppercase tracking-[0.18em] text-slate-500">{t("Constraint refs")}</div><div className="mt-2 text-2xl font-black text-slate-900" data-testid="pm-project-schedule-constraint-count">{activeVersion.counts?.constraint_refs || 0}</div></div>
                </div>
              ) : <div className="mt-4 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500" data-testid="pm-project-schedule-no-active-version">{t("No active schedule version yet. Stage and approve an import first.")}</div>}
            </section>

            <section className="rounded-[1.75rem] border border-white/30 bg-white/85 p-5 shadow-sm" data-testid="pm-project-schedule-export-section">
              <div className="grid gap-4 lg:grid-cols-[1fr_auto] lg:items-end">
                <div>
                  <h2 className="text-xl font-black text-slate-900">{t("Governed exports")}</h2>
                  <p className="mt-1 text-sm text-slate-600">{t("Prepare master schedule, lookahead, crew, equipment, material, and work-package plan exports without creating a parallel reporting truth.")}</p>
                </div>
                <div className="flex flex-wrap gap-3">
                  <select className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm" value={exportKind} onChange={(event) => setExportKind(event.target.value)} data-testid="pm-project-schedule-export-kind-select">
                    {EXPORT_OPTIONS.map(([value, label]) => <option key={value} value={value}>{t(label)}</option>)}
                  </select>
                  <Button type="button" variant="outline" onClick={onExport} disabled={!activeVersion} data-testid="pm-project-schedule-download-export-button"><Download className="mr-2 h-4 w-4" /> {t("Download")}</Button>
                </div>
              </div>
              <div className="mt-4 grid gap-3 lg:grid-cols-[1fr_auto]">
                <Input value={emailRecipients} onChange={(event) => setEmailRecipients(event.target.value)} placeholder={t("Email recipients, comma separated") } data-testid="pm-project-schedule-email-recipients-input" />
                <Button type="button" variant="outline" onClick={onQueueEmail} disabled={!activeVersion || !emailRecipients.trim()} data-testid="pm-project-schedule-email-export-button"><Send className="mr-2 h-4 w-4" /> {t("Queue email review")}</Button>
              </div>
            </section>

            <section className="rounded-[1.75rem] border border-white/30 bg-white/85 p-5 shadow-sm" data-testid="pm-project-schedule-activities-section">
              <h2 className="text-xl font-black text-slate-900">{t("Schedule activities")}</h2>
              <p className="mt-1 text-sm text-slate-600">{t("Planned assignments remain separate from actual execution. Daily Reports later populate actuals through work blocks.")}</p>
              <div className="mt-4 overflow-x-auto">
                <table className="min-w-full text-left text-sm" data-testid="pm-project-schedule-activities-table">
                  <thead className="text-xs uppercase tracking-[0.18em] text-slate-500">
                    <tr>
                      <th className="px-3 py-2">{t("Activity")}</th>
                      <th className="px-3 py-2">{t("Dates")}</th>
                      <th className="px-3 py-2">{t("Assignments")}</th>
                      <th className="px-3 py-2">{t("Status")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activities.map((row) => (
                      <tr key={row.activity_id} className="border-t border-slate-200" data-testid={`pm-project-schedule-activity-row-${row.activity_id}`}>
                        <td className="px-3 py-3"><div className="font-semibold text-slate-900">{row.activity_id}</div><div className="text-xs text-slate-500">{row.activity_name}</div><div className="text-xs text-slate-500">{row.work_package_id} · {row.project_cost_code}</div></td>
                        <td className="px-3 py-3 text-slate-700">{row.planned_start_date || "—"}<br />{row.planned_finish_date || "—"}</td>
                        <td className="px-3 py-3 text-slate-700">{joinNamedRefs(row.planned_assignments?.planned_crew_ids, "label") || "—"}<br /><span className="text-xs text-slate-500">{joinNamedRefs(row.planned_assignments?.planned_equipment_ids, "label") || t("No equipment")}</span></td>
                        <td className="px-3 py-3 text-slate-700">{row.status}<br /><span className="text-xs text-slate-500">{Number(row.percent_complete || 0).toFixed(0)}%</span></td>
                      </tr>
                    ))}
                    {!loading && activities.length === 0 ? <tr><td className="px-3 py-6 text-sm text-slate-500" colSpan={4}>{t("No active schedule activities yet.")}</td></tr> : null}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="rounded-[1.75rem] border border-white/30 bg-white/85 p-5 shadow-sm" data-testid="pm-project-schedule-work-packages-section">
              <h2 className="text-xl font-black text-slate-900">{t("Work packages")}</h2>
              <p className="mt-1 text-sm text-slate-600">{t("Work packages are operational containers linking schedule activities, budget lines, constraints, and future field execution.")}</p>
              <div className="mt-4 overflow-x-auto">
                <table className="min-w-full text-left text-sm" data-testid="pm-project-schedule-work-packages-table">
                  <thead className="text-xs uppercase tracking-[0.18em] text-slate-500">
                    <tr>
                      <th className="px-3 py-2">{t("Work package")}</th>
                      <th className="px-3 py-2">{t("Coverage")}</th>
                      <th className="px-3 py-2">{t("Planned totals")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {workPackages.map((row) => (
                      <tr key={`${row.version_id}-${row.work_package_id}`} className="border-t border-slate-200" data-testid={`pm-project-schedule-work-package-row-${row.work_package_id}`}>
                        <td className="px-3 py-3"><div className="font-semibold text-slate-900">{row.work_package_id}</div><div className="text-xs text-slate-500">{row.phase_id || "—"}</div></td>
                        <td className="px-3 py-3 text-slate-700">{row.activity_count || 0} {t("activities")}<br /><span className="text-xs text-slate-500">{(row.budget_line_ids || []).slice(0, 2).join(", ") || t("No budget lines")}</span></td>
                        <td className="px-3 py-3 text-slate-700">{Number(row.planned_hours || 0).toFixed(1)} {t("hours")}<br /><span className="text-xs text-slate-500">{Number(row.planned_production_quantity || 0).toFixed(1)} {t("planned qty")}</span></td>
                      </tr>
                    ))}
                    {!loading && workPackages.length === 0 ? <tr><td className="px-3 py-6 text-sm text-slate-500" colSpan={3}>{t("No governed work packages yet.")}</td></tr> : null}
                  </tbody>
                </table>
              </div>
            </section>
          </TabsContent>

          <TabsContent value="lookahead" className="space-y-6" data-testid="pm-project-schedule-lookahead-panel">
            <section className="rounded-[1.75rem] border border-white/30 bg-white/85 p-5 shadow-sm" data-testid="pm-project-schedule-lookahead-editor-section">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-xl font-black text-slate-900">{t("Two-week lookahead overlay")}</h2>
                  <p className="mt-1 text-sm text-slate-600">{t("This is a governed operational view of the master schedule. PM edits here do not destroy the baseline schedule version.")}</p>
                </div>
                <Button type="button" onClick={onSaveLookahead} disabled={!projectNumber || working} data-testid="pm-project-schedule-save-lookahead-button"><CalendarRange className="mr-2 h-4 w-4" /> {t("Save lookahead")}</Button>
              </div>
              <div className="mt-4 grid gap-4 md:grid-cols-3" data-testid="pm-project-schedule-lookahead-summary-grid">
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><div className="text-xs uppercase tracking-[0.18em] text-slate-500">{t("Current status")}</div><div className="mt-2 text-base font-black text-slate-900" data-testid="pm-project-schedule-lookahead-status-value">{lookahead?.status || lookaheadDraft.status}</div></div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><div className="text-xs uppercase tracking-[0.18em] text-slate-500">{t("Two-week rows")}</div><div className="mt-2 text-2xl font-black text-slate-900" data-testid="pm-project-schedule-lookahead-2w-count">{(overview?.lookahead_2w || []).length}</div></div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><div className="text-xs uppercase tracking-[0.18em] text-slate-500">{t("Four-week rows")}</div><div className="mt-2 text-2xl font-black text-slate-900" data-testid="pm-project-schedule-lookahead-4w-count">{(overview?.lookahead_4w || []).length}</div></div>
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-2">
                <div>
                  <label className="mb-1 block text-xs font-semibold uppercase tracking-[0.18em] text-slate-500" htmlFor="pm-schedule-lookahead-status">{t("Lookahead status")}</label>
                  <Input id="pm-schedule-lookahead-status" value={lookaheadDraft.status} onChange={(event) => setLookaheadDraft((prev) => ({ ...prev, status: event.target.value }))} data-testid="pm-project-schedule-lookahead-status-input" />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-semibold uppercase tracking-[0.18em] text-slate-500" htmlFor="pm-schedule-lookahead-note">{t("Comparison note")}</label>
                  <Input id="pm-schedule-lookahead-note" value={lookaheadDraft.comparison_note} onChange={(event) => setLookaheadDraft((prev) => ({ ...prev, comparison_note: event.target.value }))} data-testid="pm-project-schedule-lookahead-note-input" />
                </div>
              </div>
              <div className="mt-4 grid gap-3 xl:grid-cols-2">
                <Textarea value={lookaheadDraft.tasks_text} onChange={(event) => setLookaheadDraft((prev) => ({ ...prev, tasks_text: event.target.value }))} placeholder={t("One planned lookahead task per line")} data-testid="pm-project-schedule-lookahead-tasks-input" />
                <Textarea value={lookaheadDraft.constraints_text} onChange={(event) => setLookaheadDraft((prev) => ({ ...prev, constraints_text: event.target.value }))} placeholder={t("One governed constraint title per line")} data-testid="pm-project-schedule-lookahead-constraints-input" />
              </div>
            </section>
          </TabsContent>

          <TabsContent value="review" className="space-y-6" data-testid="pm-project-schedule-review-panel">
            <section className="rounded-[1.75rem] border border-white/30 bg-white/85 p-5 shadow-sm" data-testid="pm-project-schedule-review-queue-section">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-xl font-black text-slate-900">{t("Governed review queue")}</h2>
                  <p className="mt-1 text-sm text-slate-600">{t("Ambiguity stays queued with rationale instead of becoming silent schedule truth.")}</p>
                </div>
                <Badge variant="secondary" data-testid="pm-project-schedule-review-count-badge">{reviewQueue.length}</Badge>
              </div>
              <div className="mt-4 space-y-3">
                {reviewQueue.map((row) => (
                  <div key={row.review_id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid={`pm-project-schedule-review-item-${row.review_id}`}>
                    <div className="flex items-center justify-between gap-3">
                      <div className="font-semibold text-slate-900">{row.title}</div>
                      <Badge variant={row.status === "resolved" ? "default" : "outline"}>{row.status}</Badge>
                    </div>
                    <div className="mt-2 text-sm text-slate-600">{row.reason}</div>
                    <div className="mt-2 text-xs text-slate-500">{t("Source")}: {row.source_kind || row.source_record_id}</div>
                  </div>
                ))}
                {!loading && reviewQueue.length === 0 ? <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500" data-testid="pm-project-schedule-review-empty-state">{t("No governed schedule review items are open right now.")}</div> : null}
              </div>
            </section>
          </TabsContent>
        </Tabs>
      </div>
    </PmShell>
  );
}