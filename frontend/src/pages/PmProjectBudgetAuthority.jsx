import React, { useEffect, useMemo, useState } from "react";
import { Download, FileUp, RefreshCw, ShieldCheck, Wallet } from "lucide-react";
import { toast } from "sonner";
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
  activatePmProjectBudgetImport,
  createPmProjectBudgetImport,
  downloadPmBudgetComparison,
  downloadPmBudgetExport,
  fetchPmProjectBudgetImportDetail,
  fetchPmProjectBudgetImports,
  fetchPmProjectBudgetLines,
  fetchPmProjectBudgetOverview,
  fetchPmProjectBudgetReviewQueue,
  fetchPmProjectBudgetVersions,
  fetchPmProjectPayItems,
  fetchPmWorkTypes,
  reviewPmProjectBudgetImportRow,
} from "@/lib/projectControlsApi";
import { useSearchParams } from "react-router-dom";

const SOURCE_OPTIONS = [
  ["schedule_of_values", "Schedule of Values (SOV)"],
  ["bid_tab", "Bid tab"],
  ["pay_item_list", "Pay-item list"],
  ["engineer_bid_form", "Engineer bid form"],
  ["csv", "CSV"],
  ["excel", "Excel"],
  ["pdf_review", "PDF (review assisted)"],
];

const VERSION_OPTIONS = [
  ["bid", "Bid"],
  ["awarded_contract", "Awarded contract"],
  ["original_approved_budget", "Original approved budget"],
  ["current_approved_budget", "Current approved budget"],
  ["pending_revision", "Pending revision"],
];

const LINE_KIND_OPTIONS = [
  ["direct_cost", "Direct cost"],
  ["allowance", "Allowance"],
  ["contingency", "Contingency"],
  ["management_reserve", "Management reserve"],
];

function emptyImportForm() {
  return {
    file: null,
    source_kind: "csv",
    target_version_stage: "original_approved_budget",
    version_name: "",
  };
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

function buildDrafts(rows) {
  return Object.fromEntries((rows || []).map((row) => [row.row_id, { ...(row.selected || {}) }]));
}

function summaryCards(overview) {
  const counts = overview?.counts || {};
  return [
    ["versions", counts.versions || 0, Wallet],
    ["active-lines", counts.active_lines || 0, ShieldCheck],
    ["imports", counts.imports || 0, FileUp],
    ["review-queue-open", counts.review_queue_open || 0, RefreshCw],
  ];
}

export default function PmProjectBudgetAuthority() {
  const { t } = useT();
  const [params, setParams] = useSearchParams();
  const [projectNumber, setProjectNumber] = useState(params.get("project_number") || "");
  const [loading, setLoading] = useState(false);
  const [working, setWorking] = useState(false);
  const [overview, setOverview] = useState(null);
  const [versions, setVersions] = useState([]);
  const [lines, setLines] = useState([]);
  const [imports, setImports] = useState([]);
  const [reviewQueue, setReviewQueue] = useState([]);
  const [workTypes, setWorkTypes] = useState([]);
  const [payItems, setPayItems] = useState([]);
  const [importForm, setImportForm] = useState(emptyImportForm());
  const [activeImportId, setActiveImportId] = useState("");
  const [importDetail, setImportDetail] = useState(null);
  const [rowDrafts, setRowDrafts] = useState({});
  const [compareWith, setCompareWith] = useState("");

  useEffect(() => {
    const next = params.get("project_number") || "";
    setProjectNumber(next);
  }, [params]);

  const load = async (pn = projectNumber, pinnedImportId = "") => {
    if (!pn) return;
    setLoading(true);
    try {
      const [overviewData, versionData, importData, reviewData, workTypeData, payItemData] = await Promise.all([
        fetchPmProjectBudgetOverview(pn),
        fetchPmProjectBudgetVersions(pn),
        fetchPmProjectBudgetImports(pn),
        fetchPmProjectBudgetReviewQueue(pn),
        fetchPmWorkTypes(),
        fetchPmProjectPayItems(pn),
      ]);
      setOverview(overviewData || null);
      setVersions(versionData?.items || []);
      setImports(importData?.items || []);
      setReviewQueue(reviewData?.items || []);
      setWorkTypes(workTypeData?.items || []);
      setPayItems(payItemData?.items || []);
      const nextImportId = pinnedImportId || activeImportId || importData?.items?.[0]?.import_id || "";
      setActiveImportId(nextImportId);
      const activeVersionId = overviewData?.active_version?.version_id || versionData?.items?.find((item) => item.status === "active")?.version_id || "";
      if (activeVersionId) {
        const lineData = await fetchPmProjectBudgetLines(pn, activeVersionId);
        setLines(lineData?.items || []);
      } else {
        setLines([]);
      }
      if (nextImportId) {
        const detail = await fetchPmProjectBudgetImportDetail(pn, nextImportId);
        setImportDetail(detail || null);
        setRowDrafts(buildDrafts(detail?.rows || []));
      } else {
        setImportDetail(null);
        setRowDrafts({});
      }
      if (!compareWith && versionData?.items?.length > 1) {
        setCompareWith(versionData.items[1].version_id);
      }
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not load the governed budget workspace."));
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
      const payload = await createPmProjectBudgetImport(projectNumber, importForm);
      const nextImportId = payload?.session?.import_id || payload?.duplicate_of || "";
      toast.success(t("Budget import staged for PM review."));
      setImportForm(emptyImportForm());
      await load(projectNumber, nextImportId);
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not stage the budget import."));
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
      await reviewPmProjectBudgetImportRow(projectNumber, activeImportId, rowId, { ...(rowDrafts[rowId] || {}), action });
      toast.success(action === "approve" ? t("Budget row approved.") : action === "reject" ? t("Budget row rejected.") : t("Budget row returned to review."));
      await load(projectNumber, activeImportId);
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not update the budget row."));
    } finally {
      setWorking(false);
    }
  };

  const onActivateImport = async () => {
    if (!projectNumber || !activeImportId) return;
    setWorking(true);
    try {
      await activatePmProjectBudgetImport(projectNumber, activeImportId);
      toast.success(t("Governed budget version activated."));
      await load(projectNumber, activeImportId);
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not activate the budget version."));
    } finally {
      setWorking(false);
    }
  };

  const onExport = async () => {
    const versionId = overview?.active_version?.version_id;
    if (!projectNumber || !versionId) return;
    try {
      const response = await downloadPmBudgetExport(projectNumber, versionId);
      downloadResponseFile(response, `${projectNumber}-budget.csv`);
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not export the active budget."));
    }
  };

  const onExportComparison = async () => {
    const leftVersionId = overview?.active_version?.version_id;
    if (!projectNumber || !leftVersionId || !compareWith) return;
    try {
      const response = await downloadPmBudgetComparison(projectNumber, leftVersionId, compareWith);
      downloadResponseFile(response, `${projectNumber}-budget-comparison.csv`);
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not export the budget comparison."));
    }
  };

  const cards = useMemo(() => summaryCards(overview), [overview]);
  const importRows = importDetail?.rows || [];
  const activeVersion = overview?.active_version || null;

  return (
    <PmShell
      title="Project Budget Authority"
      section="jobs"
      subtitle="Stage governed budget imports, approve mappings, and activate budget versions without guessing financial truth."
    >
      <div className="space-y-6" data-testid="pm-project-budget-authority-page">
        <div className="rounded-[1.75rem] border border-white/30 bg-white/85 p-5 shadow-sm backdrop-blur" data-testid="pm-project-budget-header-card">
          <div className="grid gap-4 lg:grid-cols-[1fr_auto] lg:items-end">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">{t("Budget hierarchy")}</div>
              <h1 className="mt-2 text-3xl font-black text-slate-900">{t("Project Budget Authority")}</h1>
              <p className="mt-2 max-w-3xl text-sm text-slate-600">{t("Customer pay items stay contractual truth, enterprise work types stay governed, and every budget line remains future-ready for commitments, actuals, forecast, and field-work linkage.")}</p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Button type="button" variant="outline" onClick={() => load(projectNumber, activeImportId)} data-testid="pm-project-budget-refresh-button">
                <RefreshCw className="mr-2 h-4 w-4" /> {t("Refresh")}
              </Button>
              <Button type="button" variant="outline" onClick={onExport} disabled={!activeVersion} data-testid="pm-project-budget-export-button">
                <Download className="mr-2 h-4 w-4" /> {t("Export budget")}
              </Button>
            </div>
          </div>
          <div className="mt-4 max-w-sm" data-testid="pm-project-budget-project-picker-shell">
            <PmProjectSelector projectNumber={projectNumber} onChange={setProject} />
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-4" data-testid="pm-project-budget-summary-grid">
          {cards.map(([label, value, Icon]) => (
            <div key={label} className="rounded-[1.5rem] border border-white/30 bg-white/85 p-4 shadow-sm" data-testid={`pm-project-budget-summary-${label}`}>
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">{t(String(label).replace(/-/g, " "))}</div>
                  <div className="mt-2 text-3xl font-black text-slate-900">{value}</div>
                </div>
                <div className="rounded-full bg-emerald-50 p-3 text-emerald-700"><Icon className="h-5 w-5" /></div>
              </div>
            </div>
          ))}
        </div>

        <Alert data-testid="pm-project-budget-guardrail-alert">
          <ShieldCheck className="h-4 w-4" />
          <AlertTitle>{t("Constitutional guardrails")}</AlertTitle>
          <AlertDescription>
            {t("Imports never activate automatically. PM approval is required, ambiguous rows stay in governed review, and commitments / actual costs remain separate trust lines from the budget itself.")}
          </AlertDescription>
        </Alert>

        <Tabs defaultValue="imports" className="space-y-4" data-testid="pm-project-budget-tabs">
          <TabsList data-testid="pm-project-budget-tabs-list">
            <TabsTrigger value="imports" data-testid="pm-project-budget-imports-tab">{t("Imports")}</TabsTrigger>
            <TabsTrigger value="versions" data-testid="pm-project-budget-versions-tab">{t("Versions")}</TabsTrigger>
            <TabsTrigger value="review" data-testid="pm-project-budget-review-tab">{t("Review queue")}</TabsTrigger>
          </TabsList>

          <TabsContent value="imports" className="space-y-6" data-testid="pm-project-budget-imports-panel">
            <section className="rounded-[1.75rem] border border-white/30 bg-white/85 p-5 shadow-sm" data-testid="pm-project-budget-import-upload-section">
              <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
                <div className="space-y-4">
                  <div>
                    <h2 className="text-xl font-black text-slate-900">{t("Governed import")}</h2>
                    <p className="mt-1 text-sm text-slate-600">{t("Supported entry lanes: SOV, bid tabs, pay-item lists, CSV, Excel, and review-assisted PDF. Nothing activates until you approve it.")}</p>
                  </div>
                  <div className="grid gap-3 md:grid-cols-2">
                    <div>
                      <label className="mb-1 block text-xs font-semibold uppercase tracking-[0.18em] text-slate-500" htmlFor="pm-budget-source-kind">{t("Source kind")}</label>
                      <select id="pm-budget-source-kind" className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm" value={importForm.source_kind} onChange={(event) => setImportForm((prev) => ({ ...prev, source_kind: event.target.value }))} data-testid="pm-project-budget-source-kind-select">
                        {SOURCE_OPTIONS.map(([value, label]) => <option key={value} value={value}>{t(label)}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="mb-1 block text-xs font-semibold uppercase tracking-[0.18em] text-slate-500" htmlFor="pm-budget-version-stage">{t("Target version")}</label>
                      <select id="pm-budget-version-stage" className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm" value={importForm.target_version_stage} onChange={(event) => setImportForm((prev) => ({ ...prev, target_version_stage: event.target.value }))} data-testid="pm-project-budget-target-version-select">
                        {VERSION_OPTIONS.map(([value, label]) => <option key={value} value={value}>{t(label)}</option>)}
                      </select>
                    </div>
                    <Input value={importForm.version_name} onChange={(event) => setImportForm((prev) => ({ ...prev, version_name: event.target.value }))} placeholder={t("Version name (optional)")} data-testid="pm-project-budget-version-name-input" />
                    <Input type="file" accept=".csv,.xlsx,.xlsm,.xltx,.xltm,.pdf" onChange={(event) => setImportForm((prev) => ({ ...prev, file: event.target.files?.[0] || null }))} data-testid="pm-project-budget-file-input" />
                  </div>
                  <div className="flex justify-end">
                    <Button type="button" onClick={onImport} disabled={!projectNumber || !importForm.file || working} data-testid="pm-project-budget-upload-button">{working ? t("Working…") : t("Stage import")}</Button>
                  </div>
                </div>
                <div className="rounded-[1.5rem] border border-slate-200 bg-slate-50 p-4" data-testid="pm-project-budget-import-session-list">
                  <div className="flex items-center justify-between gap-3">
                    <h3 className="text-sm font-black uppercase tracking-[0.22em] text-slate-600">{t("Recent imports")}</h3>
                    <Badge variant="secondary" data-testid="pm-project-budget-import-count-badge">{imports.length}</Badge>
                  </div>
                  <div className="mt-3 space-y-3">
                    {imports.map((row) => (
                      <button key={row.import_id} type="button" className={`w-full rounded-2xl border p-3 text-left transition ${activeImportId === row.import_id ? "border-emerald-300 bg-emerald-50" : "border-slate-200 bg-white hover:border-slate-300"}`} onClick={async () => { setActiveImportId(row.import_id); const detail = await fetchPmProjectBudgetImportDetail(projectNumber, row.import_id); setImportDetail(detail); setRowDrafts(buildDrafts(detail?.rows || [])); }} data-testid={`pm-project-budget-import-card-${row.import_id}`}>
                        <div className="flex items-center justify-between gap-3">
                          <div className="font-semibold text-slate-900">{row.filename}</div>
                          <Badge variant={row.status === "activated" ? "default" : "secondary"}>{row.status}</Badge>
                        </div>
                        <div className="mt-2 text-xs text-slate-500">{row.source_kind} · {row.target_version_stage} · {row.total_rows} {t("rows")}</div>
                      </button>
                    ))}
                    {!loading && imports.length === 0 ? <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-4 text-sm text-slate-500" data-testid="pm-project-budget-import-empty-state">{t("No staged budget imports yet.")}</div> : null}
                  </div>
                </div>
              </div>
            </section>

            {importDetail ? (
              <section className="rounded-[1.75rem] border border-white/30 bg-white/85 p-5 shadow-sm" data-testid="pm-project-budget-import-detail-section">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-slate-900">{t("Review staged rows")}</h2>
                    <p className="mt-1 text-sm text-slate-600">{t("Workflow: import → suggestions → PM review → PM approval → activation.")}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Badge data-testid="pm-project-budget-active-import-status">{importDetail?.session?.status || "review_required"}</Badge>
                    <Button type="button" onClick={onActivateImport} disabled={working || !["approved_ready", "partially_reviewed"].includes(importDetail?.session?.status)} data-testid="pm-project-budget-activate-import-button">{t("Activate budget")}</Button>
                  </div>
                </div>
                {(importDetail?.session?.parser_warnings || []).length ? (
                  <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900" data-testid="pm-project-budget-parser-warning-list">
                    {(importDetail.session.parser_warnings || []).map((warning, index) => <div key={`${warning}-${index}`}>{warning}</div>)}
                  </div>
                ) : null}
                <div className="mt-4 space-y-4">
                  {importRows.map((row) => {
                    const draft = rowDrafts[row.row_id] || row.selected || {};
                    return (
                      <div key={row.row_id} className="rounded-[1.5rem] border border-slate-200 bg-slate-50 p-4" data-testid={`pm-project-budget-row-card-${row.row_id}`}>
                        <div className="flex flex-wrap items-center justify-between gap-3">
                          <div>
                            <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{t("Row")} {row.row_number}</div>
                            <div className="mt-1 font-semibold text-slate-900">{row.normalized?.customer_pay_item_number || t("Unnumbered row")} · {row.normalized?.description || t("Needs description review")}</div>
                          </div>
                          <div className="flex flex-wrap gap-2">
                            <Badge variant="secondary" data-testid={`pm-project-budget-row-status-${row.row_id}`}>{row.review_status}</Badge>
                            <Badge variant={row.suggestion?.confidence === "high" ? "default" : "outline"}>{row.suggestion?.confidence || "review_required"}</Badge>
                          </div>
                        </div>
                        <div className="mt-3 grid gap-3 lg:grid-cols-2">
                          <div className="rounded-2xl border border-slate-200 bg-white p-3" data-testid={`pm-project-budget-row-source-${row.row_id}`}>
                            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{t("Preserved source")}</div>
                            <div className="mt-2 text-sm text-slate-700">{Object.entries(row.source_values || {}).slice(0, 8).map(([key, value]) => <div key={key}><strong>{key}:</strong> {String(value || "—")}</div>)}</div>
                          </div>
                          <div className="rounded-2xl border border-slate-200 bg-white p-3" data-testid={`pm-project-budget-row-suggestion-${row.row_id}`}>
                            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{t("Suggestion")}</div>
                            <div className="mt-2 text-sm text-slate-700">{(row.suggestion?.reasons || []).map((reason, index) => <div key={`${reason}-${index}`}>{reason}</div>)}</div>
                            {(row.suggestion?.warnings || []).length ? <div className="mt-2 text-xs text-amber-700">{(row.suggestion.warnings || []).join(" • ")}</div> : null}
                          </div>
                        </div>
                        <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                          <Input value={draft.customer_pay_item_number || ""} onChange={(event) => onRowDraft(row.row_id, "customer_pay_item_number", event.target.value)} placeholder={t("Customer pay item")} list="pm-budget-pay-items-list" data-testid={`pm-project-budget-row-pay-item-${row.row_id}`} />
                          <Input value={draft.description || ""} onChange={(event) => onRowDraft(row.row_id, "description", event.target.value)} placeholder={t("Description")} data-testid={`pm-project-budget-row-description-${row.row_id}`} />
                          <select className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm" value={draft.enterprise_work_type_id || ""} onChange={(event) => onRowDraft(row.row_id, "enterprise_work_type_id", event.target.value)} data-testid={`pm-project-budget-row-work-type-${row.row_id}`}>
                            <option value="">{t("Choose enterprise work type")}</option>
                            {workTypes.map((workType) => <option key={workType.work_type_id} value={workType.work_type_id}>{workType.code} · {workType.name}</option>)}
                          </select>
                          <select className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm" value={draft.line_kind || "direct_cost"} onChange={(event) => onRowDraft(row.row_id, "line_kind", event.target.value)} data-testid={`pm-project-budget-row-line-kind-${row.row_id}`}>
                            {LINE_KIND_OPTIONS.map(([value, label]) => <option key={value} value={value}>{t(label)}</option>)}
                          </select>
                          <Input value={draft.quantity ?? ""} onChange={(event) => onRowDraft(row.row_id, "quantity", event.target.value)} placeholder={t("Quantity")} data-testid={`pm-project-budget-row-quantity-${row.row_id}`} />
                          <Input value={draft.unit || ""} onChange={(event) => onRowDraft(row.row_id, "unit", event.target.value)} placeholder={t("Unit")} data-testid={`pm-project-budget-row-unit-${row.row_id}`} />
                          <Input value={draft.unit_price ?? ""} onChange={(event) => onRowDraft(row.row_id, "unit_price", event.target.value)} placeholder={t("Unit price")} data-testid={`pm-project-budget-row-unit-price-${row.row_id}`} />
                          <Input value={draft.budget_amount ?? ""} onChange={(event) => onRowDraft(row.row_id, "budget_amount", event.target.value)} placeholder={t("Budget amount")} data-testid={`pm-project-budget-row-budget-amount-${row.row_id}`} />
                          <Input value={draft.project_cost_code || ""} onChange={(event) => onRowDraft(row.row_id, "project_cost_code", event.target.value)} placeholder={t("Project cost code")} data-testid={`pm-project-budget-row-cost-code-${row.row_id}`} />
                          <Input value={draft.phase_id || ""} onChange={(event) => onRowDraft(row.row_id, "phase_id", event.target.value)} placeholder={t("Phase")}
 data-testid={`pm-project-budget-row-phase-${row.row_id}`} />
                          <Input value={draft.work_package_id || ""} onChange={(event) => onRowDraft(row.row_id, "work_package_id", event.target.value)} placeholder={t("Work package")} data-testid={`pm-project-budget-row-work-package-${row.row_id}`} />
                          <Input value={draft.schedule_activity_id || ""} onChange={(event) => onRowDraft(row.row_id, "schedule_activity_id", event.target.value)} placeholder={t("Schedule activity")} data-testid={`pm-project-budget-row-schedule-activity-${row.row_id}`} />
                        </div>
                        <Textarea className="mt-3" value={draft.review_note || ""} onChange={(event) => onRowDraft(row.row_id, "review_note", event.target.value)} placeholder={t("Why this row is approved, rejected, or still needs review.")} data-testid={`pm-project-budget-row-review-note-${row.row_id}`} />
                        <div className="mt-4 flex flex-wrap justify-end gap-2">
                          <Button type="button" variant="outline" onClick={() => onReviewRow(row.row_id, "needs_review")} disabled={working} data-testid={`pm-project-budget-row-needs-review-${row.row_id}`}>{t("Needs review")}</Button>
                          <Button type="button" variant="ghost" onClick={() => onReviewRow(row.row_id, "reject")} disabled={working} data-testid={`pm-project-budget-row-reject-${row.row_id}`}>{t("Reject")}</Button>
                          <Button type="button" onClick={() => onReviewRow(row.row_id, "approve")} disabled={working} data-testid={`pm-project-budget-row-approve-${row.row_id}`}>{t("Approve row")}</Button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </section>
            ) : null}
          </TabsContent>

          <TabsContent value="versions" className="space-y-6" data-testid="pm-project-budget-versions-panel">
            <section className="rounded-[1.75rem] border border-white/30 bg-white/85 p-5 shadow-sm" data-testid="pm-project-budget-active-version-section">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-xl font-black text-slate-900">{t("Active budget version")}</h2>
                  <p className="mt-1 text-sm text-slate-600">{t("Budget, commitment, actual cost, forecast, revenue, billing, and collections stay separate here.")}</p>
                </div>
                {activeVersion ? <Badge data-testid="pm-project-budget-active-version-badge">{activeVersion.stage}</Badge> : null}
              </div>
              {activeVersion ? (
                <div className="mt-4 grid gap-4 md:grid-cols-3" data-testid="pm-project-budget-version-metrics-grid">
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><div className="text-xs uppercase tracking-[0.18em] text-slate-500">{t("Budget total")}</div><div className="mt-2 text-2xl font-black text-slate-900">${Number(activeVersion.totals?.budget_amount || 0).toFixed(2)}</div></div>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><div className="text-xs uppercase tracking-[0.18em] text-slate-500">{t("Allowance / contingency / reserve")}</div><div className="mt-2 text-2xl font-black text-slate-900">${Number((activeVersion.totals?.allowance_amount || 0) + (activeVersion.totals?.contingency_amount || 0) + (activeVersion.totals?.management_reserve_amount || 0)).toFixed(2)}</div></div>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><div className="text-xs uppercase tracking-[0.18em] text-slate-500">{t("Forecast foundation")}</div><div className="mt-2 text-2xl font-black text-slate-900">${Number(activeVersion.totals?.forecast_amount || 0).toFixed(2)}</div></div>
                </div>
              ) : <div className="mt-4 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500" data-testid="pm-project-budget-no-active-version">{t("No active budget version yet. Stage and approve an import first.")}</div>}
            </section>

            <section className="rounded-[1.75rem] border border-white/30 bg-white/85 p-5 shadow-sm" data-testid="pm-project-budget-lines-section">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-xl font-black text-slate-900">{t("Budget lines")}</h2>
                  <p className="mt-1 text-sm text-slate-600">{t("Every line is future-ready for work blocks, crews, employees, equipment, materials, vendors, subcontractors, commitments, actuals, and forecasts.")}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <select className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm" value={compareWith} onChange={(event) => setCompareWith(event.target.value)} data-testid="pm-project-budget-compare-version-select">
                    <option value="">{t("Choose comparison version")}</option>
                    {versions.filter((version) => version.version_id !== activeVersion?.version_id).map((version) => <option key={version.version_id} value={version.version_id}>{version.version_name}</option>)}
                  </select>
                  <Button type="button" variant="outline" onClick={onExportComparison} disabled={!activeVersion || !compareWith} data-testid="pm-project-budget-export-comparison-button">{t("Export comparison")}</Button>
                </div>
              </div>
              <div className="mt-4 overflow-x-auto">
                <table className="min-w-full text-left text-sm" data-testid="pm-project-budget-lines-table">
                  <thead className="text-xs uppercase tracking-[0.18em] text-slate-500">
                    <tr>
                      <th className="px-3 py-2">{t("Pay item")}</th>
                      <th className="px-3 py-2">{t("Work type")}</th>
                      <th className="px-3 py-2">{t("Line kind")}</th>
                      <th className="px-3 py-2">{t("Budget")}</th>
                      <th className="px-3 py-2">{t("Forecast")}</th>
                      <th className="px-3 py-2">{t("Remaining")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {lines.map((line) => (
                      <tr key={line.budget_line_id} className="border-t border-slate-200" data-testid={`pm-project-budget-line-row-${line.budget_line_id}`}>
                        <td className="px-3 py-3"><div className="font-semibold text-slate-900">{line.customer_pay_item_number}</div><div className="text-xs text-slate-500">{line.description}</div></td>
                        <td className="px-3 py-3 text-slate-700">{workTypes.find((item) => item.work_type_id === line.enterprise_work_type_id)?.name || line.enterprise_work_type_id || "—"}</td>
                        <td className="px-3 py-3 text-slate-700">{line.line_kind}</td>
                        <td className="px-3 py-3 text-slate-700">${Number(line.budget_amount || 0).toFixed(2)}</td>
                        <td className="px-3 py-3 text-slate-700">${Number(line.forecast_amount || 0).toFixed(2)}</td>
                        <td className="px-3 py-3 text-slate-700">${Number(line.remaining_amount || 0).toFixed(2)}</td>
                      </tr>
                    ))}
                    {!loading && lines.length === 0 ? <tr><td className="px-3 py-6 text-sm text-slate-500" colSpan={6}>{t("No active budget lines yet.")}</td></tr> : null}
                  </tbody>
                </table>
              </div>
            </section>
          </TabsContent>

          <TabsContent value="review" className="space-y-6" data-testid="pm-project-budget-review-panel">
            <section className="rounded-[1.75rem] border border-white/30 bg-white/85 p-5 shadow-sm" data-testid="pm-project-budget-review-queue-section">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-xl font-black text-slate-900">{t("Governed review queue")}</h2>
                  <p className="mt-1 text-sm text-slate-600">{t("Unknown financial links stay here with a rationale. Nothing is fabricated or silently normalized.")}</p>
                </div>
                <Badge variant="secondary" data-testid="pm-project-budget-review-count-badge">{reviewQueue.length}</Badge>
              </div>
              <div className="mt-4 space-y-3">
                {reviewQueue.map((row) => (
                  <div key={row.review_id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid={`pm-project-budget-review-item-${row.review_id}`}>
                    <div className="flex items-center justify-between gap-3">
                      <div className="font-semibold text-slate-900">{row.title}</div>
                      <Badge variant={row.status === "resolved" ? "default" : "outline"}>{row.status}</Badge>
                    </div>
                    <div className="mt-2 text-sm text-slate-600">{row.reason}</div>
                    <div className="mt-2 text-xs text-slate-500">{t("Source")}: {row.source_kind || row.source_record_id}</div>
                  </div>
                ))}
                {!loading && reviewQueue.length === 0 ? <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500" data-testid="pm-project-budget-review-empty-state">{t("No governed budget review items are open right now.")}</div> : null}
              </div>
            </section>

            <section className="grid gap-6 xl:grid-cols-2" data-testid="pm-project-budget-trustline-grid">
              <div className="rounded-[1.75rem] border border-white/30 bg-white/85 p-5 shadow-sm" data-testid="pm-project-budget-commitment-candidates-section">
                <h2 className="text-xl font-black text-slate-900">{t("Commitment candidates")}</h2>
                <p className="mt-1 text-sm text-slate-600">{t("PO Requests remain commitment truth. Unlinked commitments are preserved for review.")}</p>
                <div className="mt-4 space-y-3">
                  {(overview?.commitment_candidates || []).map((row) => (
                    <div key={row.candidate_id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid={`pm-project-budget-commitment-row-${row.candidate_id}`}>
                      <div className="font-semibold text-slate-900">{row.vendor || t("Vendor pending")}</div>
                      <div className="mt-1 text-sm text-slate-600">{row.description || t("No description")}</div>
                      <div className="mt-2 text-xs text-slate-500">${Number(row.commitment_amount || 0).toFixed(2)} · {row.review_status}</div>
                    </div>
                  ))}
                  {!loading && !(overview?.commitment_candidates || []).length ? <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500">{t("No commitment candidates for this project yet.")}</div> : null}
                </div>
              </div>

              <div className="rounded-[1.75rem] border border-white/30 bg-white/85 p-5 shadow-sm" data-testid="pm-project-budget-actual-cost-candidates-section">
                <h2 className="text-xl font-black text-slate-900">{t("Actual-cost candidates")}</h2>
                <p className="mt-1 text-sm text-slate-600">{t("Candidate receipts are review-only and do not replace accounting / ERP truth.")}</p>
                <div className="mt-4 space-y-3">
                  {(overview?.actual_cost_candidates || []).map((row) => (
                    <div key={row.candidate_id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid={`pm-project-budget-actual-cost-row-${row.candidate_id}`}>
                      <div className="font-semibold text-slate-900">{row.vendor || t("Vendor pending")}</div>
                      <div className="mt-1 text-sm text-slate-600">{row.description || t("No description")}</div>
                      <div className="mt-2 text-xs text-slate-500">${Number(row.candidate_amount || 0).toFixed(2)} · {row.review_status}</div>
                    </div>
                  ))}
                  {!loading && !(overview?.actual_cost_candidates || []).length ? <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500">{t("No actual-cost candidates for this project yet.")}</div> : null}
                </div>
              </div>
            </section>
          </TabsContent>
        </Tabs>

        <datalist id="pm-budget-pay-items-list">
          {payItems.map((item) => <option key={item.pay_item_id} value={item.customer_pay_item_number}>{item.description}</option>)}
        </datalist>
      </div>
    </PmShell>
  );
}
