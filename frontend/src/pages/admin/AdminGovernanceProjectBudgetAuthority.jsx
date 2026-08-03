import React, { useEffect, useMemo, useState } from "react";
import { Download, FileSearch, GitBranchPlus, RefreshCw, ShieldCheck } from "lucide-react";
import { toast } from "sonner";
import LegacyAdminModernShell from "@/components/admin/LegacyAdminModernShell";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useT } from "@/lib/i18n";
import {
  downloadAdminBudgetComparison,
  downloadAdminBudgetExport,
  fetchAdminProjectBudgetImportDetail,
  fetchAdminProjectBudgetImports,
  fetchAdminProjectBudgetLines,
  fetchAdminProjectBudgetOverview,
  fetchAdminProjectBudgetReviewQueue,
  fetchAdminProjectBudgetVersions,
  runAdminProjectBudgetBackfill,
} from "@/lib/projectControlsApi";
import { useSearchParams } from "react-router-dom";

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

function summaryCards(overview) {
  const summary = overview?.summary || {};
  return [
    ["budget-versions", summary.budget_versions || 0, GitBranchPlus],
    ["budget-lines", summary.budget_lines || 0, ShieldCheck],
    ["imports", summary.imports || 0, FileSearch],
    ["review-queue-open", summary.review_queue_open || 0, RefreshCw],
  ];
}

export default function AdminGovernanceProjectBudgetAuthority() {
  const { t } = useT();
  const [params, setParams] = useSearchParams();
  const [projectNumberInput, setProjectNumberInput] = useState(params.get("project_number") || "");
  const [projectNumber, setProjectNumber] = useState(params.get("project_number") || "");
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [overview, setOverview] = useState(null);
  const [versions, setVersions] = useState([]);
  const [lines, setLines] = useState([]);
  const [imports, setImports] = useState([]);
  const [importDetail, setImportDetail] = useState(null);
  const [reviewQueue, setReviewQueue] = useState([]);
  const [compareWith, setCompareWith] = useState("");

  const load = async (pn = projectNumber) => {
    setLoading(true);
    try {
      const [overviewData, reviewData] = await Promise.all([
        fetchAdminProjectBudgetOverview(pn),
        fetchAdminProjectBudgetReviewQueue(pn),
      ]);
      setOverview(overviewData || null);
      setReviewQueue(reviewData?.items || []);
      if (pn) {
        const [versionData, importData] = await Promise.all([
          fetchAdminProjectBudgetVersions(pn),
          fetchAdminProjectBudgetImports(pn),
        ]);
        setVersions(versionData?.items || []);
        setImports(importData?.items || []);
        const activeVersionId = versionData?.items?.find((item) => item.status === "active")?.version_id || versionData?.items?.[0]?.version_id || "";
        if (activeVersionId) {
          const lineData = await fetchAdminProjectBudgetLines(pn, activeVersionId);
          setLines(lineData?.items || []);
        } else {
          setLines([]);
        }
        if (importData?.items?.[0]?.import_id) {
          const detail = await fetchAdminProjectBudgetImportDetail(pn, importData.items[0].import_id);
          setImportDetail(detail || null);
        } else {
          setImportDetail(null);
        }
        if (!compareWith && versionData?.items?.length > 1) {
          setCompareWith(versionData.items[1].version_id);
        }
      } else {
        setVersions([]);
        setImports([]);
        setLines([]);
        setImportDetail(null);
      }
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not load governed budget governance."));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load(projectNumber);
  }, [projectNumber]);

  const applyProjectFilter = () => {
    setProjectNumber(projectNumberInput.trim());
    setParams((prev) => {
      const next = new URLSearchParams(prev);
      if (projectNumberInput.trim()) next.set("project_number", projectNumberInput.trim());
      else next.delete("project_number");
      return next;
    });
  };

  const onBackfill = async () => {
    setWorking(true);
    try {
      await runAdminProjectBudgetBackfill();
      toast.success(t("Budget backfill completed."));
      await load(projectNumber);
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not run the budget backfill."));
    } finally {
      setWorking(false);
    }
  };

  const onExportBudget = async () => {
    const versionId = versions.find((item) => item.status === "active")?.version_id;
    if (!projectNumber || !versionId) return;
    try {
      const response = await downloadAdminBudgetExport(projectNumber, versionId);
      downloadResponseFile(response, `${projectNumber}-budget.csv`);
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not export the budget."));
    }
  };

  const onExportComparison = async () => {
    const activeVersionId = versions.find((item) => item.status === "active")?.version_id;
    if (!projectNumber || !activeVersionId || !compareWith) return;
    try {
      const response = await downloadAdminBudgetComparison(projectNumber, activeVersionId, compareWith);
      downloadResponseFile(response, `${projectNumber}-budget-comparison.csv`);
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not export the comparison report."));
    }
  };

  const cards = useMemo(() => summaryCards(overview), [overview]);
  const activeVersion = versions.find((item) => item.status === "active") || null;

  return (
    <LegacyAdminModernShell
      title={t("Project Budget Authority")}
      subtitle={t("Govern budget imports, review unresolved trust lines, and verify additive C3 financial foundations without duplicating accounting truth.")}
    >
      <div className="space-y-6" data-testid="admin-project-budget-authority-page">
        <div className="flex flex-wrap gap-3" data-testid="admin-project-budget-actions-row">
          <Input value={projectNumberInput} onChange={(event) => setProjectNumberInput(event.target.value)} placeholder={t("Project number filter (optional)")} className="max-w-sm" data-testid="admin-project-budget-project-filter-input" />
          <Button type="button" variant="outline" onClick={applyProjectFilter} data-testid="admin-project-budget-apply-filter-button">{t("Apply filter")}</Button>
          <Button type="button" variant="outline" onClick={() => load(projectNumber)} data-testid="admin-project-budget-refresh-button">
            <RefreshCw className="mr-2 h-4 w-4" /> {t("Refresh")}
          </Button>
          <Button type="button" variant="outline" onClick={onBackfill} disabled={working} data-testid="admin-project-budget-backfill-button">
            <GitBranchPlus className="mr-2 h-4 w-4" /> {working ? t("Working…") : t("Run compatibility backfill")}
          </Button>
          <Button type="button" variant="outline" onClick={onExportBudget} disabled={!projectNumber || !activeVersion} data-testid="admin-project-budget-export-button">
            <Download className="mr-2 h-4 w-4" /> {t("Export budget")}
          </Button>
        </div>

        <div className="grid gap-4 md:grid-cols-4" data-testid="admin-project-budget-summary-grid">
          {cards.map(([label, value, Icon]) => (
            <div key={label} className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm" data-testid={`admin-project-budget-summary-${label}`}>
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">{t(String(label).replace(/-/g, " "))}</div>
                  <div className="mt-2 text-3xl font-black text-slate-900">{value}</div>
                </div>
                <div className="rounded-full bg-red-50 p-3 text-red-700"><Icon className="h-5 w-5" /></div>
              </div>
            </div>
          ))}
        </div>

        <Alert data-testid="admin-project-budget-guardrail-alert">
          <ShieldCheck className="h-4 w-4" />
          <AlertTitle>{t("Financial trust lines")}</AlertTitle>
          <AlertDescription>
            {t("Budget is planning truth here. Commitments stay linked to PO Requests, candidate receipts stay review-only, and accounting / ERP remains the actual-cost authority.")}
          </AlertDescription>
        </Alert>

        <Tabs defaultValue="review" className="space-y-4" data-testid="admin-project-budget-tabs">
          <TabsList data-testid="admin-project-budget-tabs-list">
            <TabsTrigger value="review" data-testid="admin-project-budget-review-tab">{t("Review queue")}</TabsTrigger>
            <TabsTrigger value="versions" data-testid="admin-project-budget-versions-tab">{t("Versions")}</TabsTrigger>
            <TabsTrigger value="imports" data-testid="admin-project-budget-imports-tab">{t("Imports")}</TabsTrigger>
          </TabsList>

          <TabsContent value="review" className="space-y-6" data-testid="admin-project-budget-review-panel">
            <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm" data-testid="admin-project-budget-review-queue-section">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-xl font-black text-slate-900">{t("Governed review queue")}</h2>
                  <p className="mt-1 text-sm text-slate-600">{t("Rows, commitments, and candidate actuals remain here until evidence is good enough for the operator to decide.")}</p>
                </div>
                <Badge variant="secondary" data-testid="admin-project-budget-review-count-badge">{reviewQueue.length}</Badge>
              </div>
              <div className="mt-4 space-y-3">
                {reviewQueue.map((row) => (
                  <div key={row.review_id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid={`admin-project-budget-review-item-${row.review_id}`}>
                    <div className="flex items-center justify-between gap-3">
                      <div className="font-semibold text-slate-900">{row.title}</div>
                      <Badge variant={row.status === "resolved" ? "default" : "outline"}>{row.status}</Badge>
                    </div>
                    <div className="mt-2 text-sm text-slate-600">{row.reason}</div>
                    <div className="mt-2 text-xs text-slate-500">{t("Project")}: {row.project_number || "—"} · {t("Source")}: {row.source_kind || row.source_record_id}</div>
                  </div>
                ))}
                {!loading && reviewQueue.length === 0 ? <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500" data-testid="admin-project-budget-review-empty-state">{t("No governed budget review items are open right now.")}</div> : null}
              </div>
            </section>
          </TabsContent>

          <TabsContent value="versions" className="space-y-6" data-testid="admin-project-budget-versions-panel">
            <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm" data-testid="admin-project-budget-versions-section">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-xl font-black text-slate-900">{t("Budget versions")}</h2>
                  <p className="mt-1 text-sm text-slate-600">{t("Use a project filter to inspect additive versions and export comparison evidence.")}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <select className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm" value={compareWith} onChange={(event) => setCompareWith(event.target.value)} data-testid="admin-project-budget-compare-version-select">
                    <option value="">{t("Choose comparison version")}</option>
                    {versions.filter((version) => version.version_id !== activeVersion?.version_id).map((version) => <option key={version.version_id} value={version.version_id}>{version.version_name}</option>)}
                  </select>
                  <Button type="button" variant="outline" onClick={onExportComparison} disabled={!projectNumber || !activeVersion || !compareWith} data-testid="admin-project-budget-export-comparison-button">{t("Export comparison")}</Button>
                </div>
              </div>
              <div className="mt-4 grid gap-3">
                {versions.map((row) => (
                  <div key={row.version_id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid={`admin-project-budget-version-card-${row.version_id}`}>
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="font-semibold text-slate-900">{row.version_name}</div>
                        <div className="mt-1 text-xs text-slate-500">{row.project_number} · {row.stage}</div>
                      </div>
                      <Badge variant={row.status === "active" ? "default" : "outline"}>{row.status}</Badge>
                    </div>
                    <div className="mt-2 text-sm text-slate-600">${Number(row.totals?.budget_amount || 0).toFixed(2)} {t("budget total")}</div>
                  </div>
                ))}
                {!loading && versions.length === 0 ? <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500" data-testid="admin-project-budget-versions-empty-state">{t("No project budget versions found for the current filter.")}</div> : null}
              </div>
            </section>

            {projectNumber ? (
              <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm" data-testid="admin-project-budget-lines-section">
                <h2 className="text-xl font-black text-slate-900">{t("Active budget lines")}</h2>
                <p className="mt-1 text-sm text-slate-600">{t("Budget lines remain structurally ready for crews, equipment, materials, vendors, subcontractors, commitments, actuals, and forecasts.")}</p>
                <div className="mt-4 overflow-x-auto">
                  <table className="min-w-full text-left text-sm" data-testid="admin-project-budget-lines-table">
                    <thead className="text-xs uppercase tracking-[0.18em] text-slate-500">
                      <tr>
                        <th className="px-3 py-2">{t("Pay item")}</th>
                        <th className="px-3 py-2">{t("Description")}</th>
                        <th className="px-3 py-2">{t("Kind")}</th>
                        <th className="px-3 py-2">{t("Budget")}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {lines.map((line) => (
                        <tr key={line.budget_line_id} className="border-t border-slate-200" data-testid={`admin-project-budget-line-row-${line.budget_line_id}`}>
                          <td className="px-3 py-3 font-semibold text-slate-900">{line.customer_pay_item_number}</td>
                          <td className="px-3 py-3 text-slate-700">{line.description}</td>
                          <td className="px-3 py-3 text-slate-700">{line.line_kind}</td>
                          <td className="px-3 py-3 text-slate-700">${Number(line.budget_amount || 0).toFixed(2)}</td>
                        </tr>
                      ))}
                      {!loading && lines.length === 0 ? <tr><td className="px-3 py-6 text-sm text-slate-500" colSpan={4}>{t("No active budget lines found.")}</td></tr> : null}
                    </tbody>
                  </table>
                </div>
              </section>
            ) : null}
          </TabsContent>

          <TabsContent value="imports" className="space-y-6" data-testid="admin-project-budget-imports-panel">
            <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm" data-testid="admin-project-budget-imports-section">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-xl font-black text-slate-900">{t("Recent staged imports")}</h2>
                  <p className="mt-1 text-sm text-slate-600">{t("Use these to verify source preservation, parser warnings, and PM approval readiness.")}</p>
                </div>
                <Badge variant="secondary" data-testid="admin-project-budget-imports-count-badge">{imports.length}</Badge>
              </div>
              <div className="mt-4 space-y-3">
                {imports.map((row) => (
                  <div key={row.import_id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid={`admin-project-budget-import-card-${row.import_id}`}>
                    <div className="flex items-center justify-between gap-3">
                      <div className="font-semibold text-slate-900">{row.filename}</div>
                      <Badge variant={row.status === "activated" ? "default" : "outline"}>{row.status}</Badge>
                    </div>
                    <div className="mt-2 text-xs text-slate-500">{row.source_kind} · {row.target_version_stage} · {row.total_rows} {t("rows")}</div>
                  </div>
                ))}
                {!loading && imports.length === 0 ? <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500" data-testid="admin-project-budget-imports-empty-state">{t("No budget imports found for the current filter.")}</div> : null}
              </div>
            </section>

            {importDetail ? (
              <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm" data-testid="admin-project-budget-import-detail-section">
                <h2 className="text-xl font-black text-slate-900">{t("Latest import evidence")}</h2>
                <p className="mt-1 text-sm text-slate-600">{t("This evidence is advisory only; PM approval remains the activation gate.")}</p>
                <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid="admin-project-budget-import-evidence-card">
                  <div className="font-semibold text-slate-900">{importDetail.session?.filename}</div>
                  <div className="mt-2 text-sm text-slate-600">{t("Status")}: {importDetail.session?.status} · {t("Rows")}: {importDetail.count}</div>
                  {(importDetail.session?.parser_warnings || []).length ? <div className="mt-3 text-xs text-amber-700">{(importDetail.session.parser_warnings || []).join(" • ")}</div> : null}
                </div>
              </section>
            ) : null}
          </TabsContent>
        </Tabs>
      </div>
    </LegacyAdminModernShell>
  );
}
