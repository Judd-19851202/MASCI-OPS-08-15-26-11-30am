import React, { useEffect, useMemo, useState } from "react";
import { Download, FileUp, Plus, RefreshCw, ShieldCheck, Trash2, Wallet } from "lucide-react";
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
import { operatorConfidenceLabel, operatorStatusLabel } from "@/lib/operatorLanguage";
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
  reviewPmBudgetActualCostCandidate,
  reviewPmBudgetCommitmentCandidate,
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

function fmtMoney(value) {
  return `$${Number(value || 0).toFixed(2)}`;
}

function TrustLinkEditor({ candidate, kind, lineOptions, onSubmit, working }) {
  const { t } = useT();
  const sourceAmount = Number(kind === "commitment" ? candidate?.commitment_amount : candidate?.candidate_amount || 0);
  const seedAllocations = (candidate?.allocations || []).length
    ? candidate.allocations.map((row) => ({ budget_line_id: row.budget_line_id || "", amount: String(row.amount ?? "") }))
    : [{ budget_line_id: candidate?.budget_line_id || lineOptions[0]?.value || "", amount: sourceAmount ? sourceAmount.toFixed(2) : "" }];
  const [allocations, setAllocations] = useState(seedAllocations);
  const [reviewNote, setReviewNote] = useState(candidate?.review_note || "");

  const updateAllocation = (index, key, value) => {
    setAllocations((prev) => prev.map((row, rowIndex) => (rowIndex === index ? { ...row, [key]: value } : row)));
  };

  const addAllocation = () => {
    setAllocations((prev) => [...prev, { budget_line_id: lineOptions[0]?.value || "", amount: "" }]);
  };

  const removeAllocation = (index) => {
    setAllocations((prev) => prev.filter((_, rowIndex) => rowIndex !== index));
  };

  const allocatedTotal = allocations.reduce((sum, row) => sum + Number(row.amount || 0), 0);
  const isMatched = Math.abs(allocatedTotal - sourceAmount) < 0.01;

  const submit = (action) => {
    onSubmit?.(candidate.candidate_id, {
      action,
      review_note: reviewNote,
      allocations: allocations
        .filter((row) => row.budget_line_id && Number(row.amount || 0) > 0)
        .map((row) => ({ budget_line_id: row.budget_line_id, amount: Number(row.amount || 0) })),
    });
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid={`pm-project-budget-${kind}-row-${candidate.candidate_id}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="font-semibold text-slate-900">{candidate.vendor || candidate.source_label || t("Vendor pending")}</div>
          <div className="mt-1 text-sm text-slate-600">{candidate.description || t("No description")}</div>
          <div className="mt-2 text-xs text-slate-500" data-testid={`pm-project-budget-${kind}-source-${candidate.candidate_id}`}>
            {fmtMoney(sourceAmount)} · {operatorStatusLabel(candidate.review_status, t)}
          </div>
        </div>
        <Badge variant={candidate.review_status === "approved" ? "default" : "outline"} data-testid={`pm-project-budget-${kind}-status-${candidate.candidate_id}`}>
          {operatorStatusLabel(candidate.review_status, t)}
        </Badge>
      </div>

      <div className="mt-4 space-y-3">
        {allocations.map((row, index) => (
          <div key={`${candidate.candidate_id}-allocation-${index}`} className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-3 md:grid-cols-[1.6fr_0.7fr_auto]" data-testid={`pm-project-budget-${kind}-allocation-${candidate.candidate_id}-${index}`}>
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500" htmlFor={`${kind}-line-${candidate.candidate_id}-${index}`}>{t("Budget line")}</label>
              <select id={`${kind}-line-${candidate.candidate_id}-${index}`} className="h-10 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm" value={row.budget_line_id} onChange={(event) => updateAllocation(index, "budget_line_id", event.target.value)} data-testid={`pm-project-budget-${kind}-allocation-line-${candidate.candidate_id}-${index}`}>
                <option value="">{t("Choose budget line")}</option>
                {lineOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500" htmlFor={`${kind}-amount-${candidate.candidate_id}-${index}`}>{t("Amount to link")}</label>
              <Input id={`${kind}-amount-${candidate.candidate_id}-${index}`} type="number" min="0" step="0.01" value={row.amount} onChange={(event) => updateAllocation(index, "amount", event.target.value)} data-testid={`pm-project-budget-${kind}-allocation-amount-${candidate.candidate_id}-${index}`} />
            </div>
            <div className="flex items-end justify-end">
              <Button type="button" variant="outline" size="icon" onClick={() => removeAllocation(index)} disabled={working || allocations.length === 1} data-testid={`pm-project-budget-${kind}-allocation-remove-${candidate.candidate_id}-${index}`}>
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        ))}

        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="text-xs text-slate-500" data-testid={`pm-project-budget-${kind}-allocation-total-${candidate.candidate_id}`}>
            {t("Allocated")}: {fmtMoney(allocatedTotal)} · {t("Source")}: {fmtMoney(sourceAmount)} · {isMatched ? t("Ready to approve") : t("Amounts must equal the source total")}
          </div>
          <Button type="button" variant="outline" onClick={addAllocation} disabled={working} data-testid={`pm-project-budget-${kind}-allocation-add-${candidate.candidate_id}`}>
            <Plus className="mr-2 h-4 w-4" /> {t("Add line")}
          </Button>
        </div>

        <div className="space-y-2">
          <label className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500" htmlFor={`${kind}-review-note-${candidate.candidate_id}`}>{t("Review note")}</label>
          <Textarea id={`${kind}-review-note-${candidate.candidate_id}`} value={reviewNote} onChange={(event) => setReviewNote(event.target.value)} data-testid={`pm-project-budget-${kind}-review-note-${candidate.candidate_id}`} />
        </div>

        <div className="flex flex-wrap gap-2">
          <Button type="button" onClick={() => submit("approve")} disabled={working || !isMatched} data-testid={`pm-project-budget-${kind}-approve-${candidate.candidate_id}`}>{t("Approve linkage")}</Button>
          <Button type="button" variant="outline" onClick={() => submit("review_required")} disabled={working} data-testid={`pm-project-budget-${kind}-review-required-${candidate.candidate_id}`}>{t("Keep in review")}</Button>
          <Button type="button" variant="outline" onClick={() => submit("reject")} disabled={working} data-testid={`pm-project-budget-${kind}-reject-${candidate.candidate_id}`}>{t("Reject")}</Button>
        </div>
      </div>
    </div>
  );
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
  const lineOptions = useMemo(() => lines.map((line) => ({ value: line.budget_line_id, label: `${line.customer_pay_item_number || "—"} · ${line.project_cost_code || "—"} · ${line.description || line.budget_line_id}` })), [lines]);

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
      toast.error(error?.response?.data?.detail || t("Could not load the project budget."));
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
      toast.success(t("Budget version activated."));
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

  const onReviewTrustCandidate = async (kind, candidateId, payload) => {
    if (!projectNumber) return;
    setWorking(true);
    try {
      if (kind === "commitment") await reviewPmBudgetCommitmentCandidate(projectNumber, candidateId, payload);
      else await reviewPmBudgetActualCostCandidate(projectNumber, candidateId, payload);
      toast.success(payload.action === "approve" ? t("Trust-line linkage approved.") : payload.action === "reject" ? t("Candidate rejected.") : t("Candidate kept in review."));
      await load(projectNumber, activeImportId);
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not update the trust-line review."));
    } finally {
      setWorking(false);
    }
  };

  const cards = useMemo(() => summaryCards(overview), [overview]);
  const importRows = importDetail?.rows || [];
  const activeVersion = overview?.active_version || null;

  return (
    <PmShell
      title="Project Budget"
      section="jobs"
      subtitle="Review budget imports, approve line setup, and activate the budget version without guessing the current job cost picture."
    >
      <div className="space-y-6" data-testid="pm-project-budget-authority-page">
        <div className="rounded-[1.75rem] border border-white/30 bg-white/85 p-5 shadow-sm backdrop-blur" data-testid="pm-project-budget-header-card">
          <div className="grid gap-4 lg:grid-cols-[1fr_auto] lg:items-end">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">{t("Budget setup")}</div>
              <h1 className="mt-2 text-3xl font-black text-slate-900">{t("Project Budget")}</h1>
              <p className="mt-2 max-w-3xl text-sm text-slate-600">{t("Customer pay items stay tied to the contract record, company work types stay admin-managed, and each budget line stays ready for job cost review.")}</p>
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
          {[["versions", cards[0]?.[1], cards[0]?.[2], t("Budget versions")], ["active-lines", cards[1]?.[1], cards[1]?.[2], t("Active lines")], ["imports", cards[2]?.[1], cards[2]?.[2], t("Imports")], ["review-queue-open", cards[3]?.[1], cards[3]?.[2], t("Items needing review")]].map(([key, value, Icon, label]) => (
            <div key={key} className="rounded-[1.5rem] border border-white/30 bg-white/85 p-4 shadow-sm" data-testid={`pm-project-budget-summary-${key}`}>
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">{label}</div>
                  <div className="mt-2 text-3xl font-black text-slate-900">{value}</div>
                </div>
                <div className="rounded-full bg-emerald-50 p-3 text-emerald-700"><Icon className="h-5 w-5" /></div>
              </div>
            </div>
          ))}
        </div>

        <Alert data-testid="pm-project-budget-guardrail-alert">
          <ShieldCheck className="h-4 w-4" />
          <AlertTitle>{t("Financial rules")}</AlertTitle>
          <AlertDescription>
            {t("Imports never activate automatically. PM approval is required, unclear rows stay in review, and commitments plus actual costs stay separate from the budget itself.")}
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
                  <h2 className="text-xl font-black text-slate-900">{t("Import for review")}</h2>
                  <p className="mt-1 text-sm text-slate-600">{t("Supported entry lanes include SOV, bid tabs, pay-item lists, CSV, Excel, and PDF review. Nothing activates until you approve it.")}</p>
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
                    <Button type="button" onClick={onImport} disabled={!projectNumber || !importForm.file || working} data-testid="pm-project-budget-upload-button">{working ? t("Working…") : t("Start import review")}</Button>
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
                          <Badge variant={row.status === "activated" ? "default" : "secondary"}>{operatorStatusLabel(row.status, t)}</Badge>
                        </div>
                        <div className="mt-2 text-xs text-slate-500">{operatorStatusLabel(row.source_kind, t)} · {operatorStatusLabel(row.target_version_stage, t)} · {row.total_rows} {t("rows")}</div>
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
                    <h2 className="text-xl font-black text-slate-900">{t("Review imported rows")}</h2>
                    <p className="mt-1 text-sm text-slate-600">{t("Workflow: import → suggested matches → PM review → PM approval → activation.")}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Badge data-testid="pm-project-budget-active-import-status">{operatorStatusLabel(importDetail?.session?.status || "review_required", t)}</Badge>
                    <Button type="button" onClick={onActivateImport} disabled={working || !["approved_ready", "partially_reviewed"].includes(importDetail?.session?.status)} data-testid="pm-project-budget-activate-import-button">{t("Activate budget version")}</Button>
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
                            <div className="mt-1 font-semibold text-slate-900">{row.normalized?.customer_pay_item_number || t("Unnumbered pay item")} · {row.normalized?.description || t("Needs description review")}</div>
                          </div>
                          <div className="flex flex-wrap gap-2">
                            <Badge variant="secondary" data-testid={`pm-project-budget-row-status-${row.row_id}`}>{operatorStatusLabel(row.review_status, t)}</Badge>
                            <Badge variant={row.suggestion?.confidence === "high" ? "default" : "outline"}>{operatorConfidenceLabel(row.suggestion?.confidence || "review_required", t)}</Badge>
                          </div>
                        </div>
                        <div className="mt-3 grid gap-3 lg:grid-cols-2">
                          <div className="rounded-2xl border border-slate-200 bg-white p-3" data-testid={`pm-project-budget-row-source-${row.row_id}`}>
                            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{t("Original source")}</div>
                            <div className="mt-2 text-sm text-slate-700">{Object.entries(row.source_values || {}).slice(0, 8).map(([key, value]) => <div key={key}><strong>{key}:</strong> {String(value || "—")}</div>)}</div>
                          </div>
                          <div className="rounded-2xl border border-slate-200 bg-white p-3" data-testid={`pm-project-budget-row-suggestion-${row.row_id}`}>
                            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{t("Suggested match")}</div>
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
                  <h2 className="text-xl font-black text-slate-900">{t("Active budget")}</h2>
                  <p className="mt-1 text-sm text-slate-600">{t("Budget, commitments, receipts, forecast, revenue, billing, and collections stay separate here.")}</p>
                </div>
                {activeVersion ? <Badge data-testid="pm-project-budget-active-version-badge">{operatorStatusLabel(activeVersion.stage, t)}</Badge> : null}
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
                  <p className="mt-1 text-sm text-slate-600">{t("Each line stays ready for work blocks, crews, equipment, materials, vendors, subcontractors, commitments, receipts, and forecasts.")}</p>
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
                        <th className="px-3 py-2">{t("Commitments")}</th>
                        <th className="px-3 py-2">{t("Actual cost")}</th>
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
                          <td className="px-3 py-3 text-slate-700">${Number(line.commitment_amount || 0).toFixed(2)}</td>
                          <td className="px-3 py-3 text-slate-700">${Number(line.actual_cost_amount || 0).toFixed(2)}</td>
                        <td className="px-3 py-3 text-slate-700">${Number(line.forecast_amount || 0).toFixed(2)}</td>
                        <td className="px-3 py-3 text-slate-700">${Number(line.remaining_amount || 0).toFixed(2)}</td>
                      </tr>
                    ))}
                      {!loading && lines.length === 0 ? <tr><td className="px-3 py-6 text-sm text-slate-500" colSpan={8}>{t("No active budget lines yet.")}</td></tr> : null}
                  </tbody>
                </table>
              </div>
            </section>
          </TabsContent>

          <TabsContent value="review" className="space-y-6" data-testid="pm-project-budget-review-panel">
            <section className="rounded-[1.75rem] border border-white/30 bg-white/85 p-5 shadow-sm" data-testid="pm-project-budget-review-queue-section">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-xl font-black text-slate-900">{t("Items needing review")}</h2>
                  <p className="mt-1 text-sm text-slate-600">{t("Unknown financial links stay here with a reason. Nothing is guessed or silently changed.")}</p>
                </div>
                <Badge variant="secondary" data-testid="pm-project-budget-review-count-badge">{reviewQueue.length}</Badge>
              </div>
              <div className="mt-4 space-y-3">
                {reviewQueue.map((row) => (
                  <div key={row.review_id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid={`pm-project-budget-review-item-${row.review_id}`}>
                    <div className="flex items-center justify-between gap-3">
                      <div className="font-semibold text-slate-900">{row.title}</div>
                      <Badge variant={row.status === "resolved" ? "default" : "outline"}>{operatorStatusLabel(row.status, t)}</Badge>
                    </div>
                    <div className="mt-2 text-sm text-slate-600">{row.reason}</div>
                    <div className="mt-2 text-xs text-slate-500">{t("Source")}: {row.source_kind || row.source_record_id}</div>
                  </div>
                ))}
                {!loading && reviewQueue.length === 0 ? <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500" data-testid="pm-project-budget-review-empty-state">{t("No budget items need review right now.")}</div> : null}
              </div>
            </section>

            <section className="grid gap-6 xl:grid-cols-2" data-testid="pm-project-budget-trustline-grid">
              <div className="rounded-[1.75rem] border border-white/30 bg-white/85 p-5 shadow-sm" data-testid="pm-project-budget-commitment-candidates-section">
                <h2 className="text-xl font-black text-slate-900">{t("PO links needing review")}</h2>
                <p className="mt-1 text-sm text-slate-600">{t("Each approved PO amount needs to land on the right budget line before committed cost can be trusted here.")}</p>
                <div className="mt-4 space-y-3">
                  {(overview?.commitment_candidates || []).map((row) => (
                    <TrustLinkEditor key={`${row.candidate_id}:${row.review_status}:${row.reviewed_at || ""}`} candidate={row} kind="commitment" lineOptions={lineOptions} onSubmit={(candidateId, payload) => onReviewTrustCandidate("commitment", candidateId, payload)} working={working} />
                  ))}
                  {!loading && !(overview?.commitment_candidates || []).length ? <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500" data-testid="pm-project-budget-commitment-empty-state">{t("No PO links need review for this project yet.")}</div> : null}
                </div>
              </div>

              <div className="rounded-[1.75rem] border border-white/30 bg-white/85 p-5 shadow-sm" data-testid="pm-project-budget-actual-cost-candidates-section">
                <h2 className="text-xl font-black text-slate-900">{t("Receipts needing review")}</h2>
                <p className="mt-1 text-sm text-slate-600">{t("Each receipt amount needs to be tied to the right budget line before actual cost is ready here. Receipt review supports cost tracking but does not replace accounting.")}</p>
                <div className="mt-4 space-y-3">
                  {(overview?.actual_cost_candidates || []).map((row) => (
                    <TrustLinkEditor key={`${row.candidate_id}:${row.review_status}:${row.reviewed_at || ""}`} candidate={row} kind="actual-cost" lineOptions={lineOptions} onSubmit={(candidateId, payload) => onReviewTrustCandidate("actual", candidateId, payload)} working={working} />
                  ))}
                  {!loading && !(overview?.actual_cost_candidates || []).length ? <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500" data-testid="pm-project-budget-actual-cost-empty-state">{t("No receipts need review for this project yet.")}</div> : null}
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
