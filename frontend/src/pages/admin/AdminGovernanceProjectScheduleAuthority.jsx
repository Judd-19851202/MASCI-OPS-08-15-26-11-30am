import React, { useEffect, useMemo, useState } from "react";
import { Download, GitBranchPlus, RefreshCw, ShieldCheck } from "lucide-react";
import { toast } from "sonner";
import { useSearchParams } from "react-router-dom";
import LegacyAdminModernShell from "@/components/admin/LegacyAdminModernShell";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useT } from "@/lib/i18n";
import {
  downloadAdminScheduleExport,
  fetchAdminProjectScheduleActivities,
  fetchAdminProjectScheduleActualsOverview,
  fetchAdminProjectScheduleImportDetail,
  fetchAdminProjectScheduleImports,
  fetchAdminProjectScheduleOverview,
  fetchAdminProjectScheduleReviewQueue,
  fetchAdminProjectScheduleVersions,
  fetchAdminProjectScheduleWorkPackages,
  runAdminProjectScheduleBackfill,
} from "@/lib/projectControlsApi";

const EXPORT_OPTIONS = [
  ["master_schedule_csv", "Master schedule CSV"],
  ["forecast_schedule_csv", "Forecast schedule CSV"],
  ["two_week_csv", "Two-week lookahead CSV"],
  ["four_week_csv", "Four-week lookahead CSV"],
  ["daily_work_plan_csv", "Daily work plan CSV"],
  ["crew_plan_csv", "Crew plan CSV"],
  ["equipment_plan_csv", "Equipment plan CSV"],
  ["material_plan_csv", "Material plan CSV"],
  ["schedule_actuals_csv", "Schedule actuals CSV"],
  ["work_package_plan_csv", "Work-package plan CSV"],
];

function summaryCards(overview) {
  const summary = overview?.summary || {};
  return [
    ["schedule-versions", summary.schedule_versions || 0],
    ["schedule-activities", summary.schedule_activities || 0],
    ["work-packages", summary.work_packages || 0],
    ["review-queue-open", summary.review_queue_open || 0],
    ["schedule-actual-candidates", summary.schedule_actual_candidates || 0],
    ["approved-schedule-actuals", summary.approved_schedule_actuals || 0],
  ];
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

export default function AdminGovernanceProjectScheduleAuthority() {
  const { t } = useT();
  const [params, setParams] = useSearchParams();
  const [projectNumberInput, setProjectNumberInput] = useState(params.get("project_number") || "");
  const [projectNumber, setProjectNumber] = useState(params.get("project_number") || "");
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [overview, setOverview] = useState(null);
  const [versions, setVersions] = useState([]);
  const [activities, setActivities] = useState([]);
  const [workPackages, setWorkPackages] = useState([]);
  const [imports, setImports] = useState([]);
  const [importDetail, setImportDetail] = useState(null);
  const [reviewQueue, setReviewQueue] = useState([]);
  const [exportKind, setExportKind] = useState("master_schedule_csv");
  const [actualsOverview, setActualsOverview] = useState(null);

  const load = async (pn = projectNumber) => {
    setLoading(true);
    try {
      const [overviewData, reviewData] = await Promise.all([
        fetchAdminProjectScheduleOverview(pn),
        fetchAdminProjectScheduleReviewQueue(pn),
      ]);
      setOverview(overviewData || null);
      setReviewQueue(reviewData?.items || []);
      setActualsOverview((overviewData || {}).schedule_actuals || null);
      if (pn) {
        const [versionData, importData] = await Promise.all([
          fetchAdminProjectScheduleVersions(pn),
          fetchAdminProjectScheduleImports(pn),
        ]);
        setVersions(versionData?.items || []);
        setImports(importData?.items || []);
        const activeVersionId = versionData?.items?.find((item) => item.status === "active")?.version_id || versionData?.items?.[0]?.version_id || "";
        if (activeVersionId) {
          const [activityData, workPackageData] = await Promise.all([
            fetchAdminProjectScheduleActivities(pn, activeVersionId),
            fetchAdminProjectScheduleWorkPackages(pn, activeVersionId),
          ]);
          setActivities(activityData?.items || []);
          setWorkPackages(workPackageData?.items || []);
        } else {
          setActivities([]);
          setWorkPackages([]);
        }
        if (importData?.items?.[0]?.import_id) {
          const detail = await fetchAdminProjectScheduleImportDetail(pn, importData.items[0].import_id);
          setImportDetail(detail || null);
        } else {
          setImportDetail(null);
        }
        const actualsData = await fetchAdminProjectScheduleActualsOverview(pn).catch(() => null);
        setActualsOverview(actualsData || (overviewData || {}).schedule_actuals || null);
      } else {
        setVersions([]);
        setActivities([]);
        setWorkPackages([]);
        setImports([]);
        setImportDetail(null);
        const actualsData = await fetchAdminProjectScheduleActualsOverview("").catch(() => null);
        setActualsOverview(actualsData || (overviewData || {}).schedule_actuals || null);
      }
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not load governed schedule governance."));
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
      await runAdminProjectScheduleBackfill();
      toast.success(t("Schedule backfill queued."));
      await load(projectNumber);
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not run the schedule backfill."));
    } finally {
      setWorking(false);
    }
  };

  const onExport = async () => {
    const versionId = versions.find((item) => item.status === "active")?.version_id;
    if (!projectNumber || !versionId) return;
    try {
      const response = await downloadAdminScheduleExport(projectNumber, versionId, exportKind);
      downloadResponseFile(response, `${projectNumber}-${exportKind}.csv`);
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not export the governed schedule."));
    }
  };

  const cards = useMemo(() => summaryCards(overview), [overview]);

  return (
    <LegacyAdminModernShell title={t("Project Schedule Authority")} subtitle={t("Govern schedule imports, work-package readiness, and additive C4 oversight without duplicating project, budget, or Daily Report truth.")}>
      <div className="space-y-6" data-testid="admin-project-schedule-authority-page">
        <div className="flex flex-wrap gap-3" data-testid="admin-project-schedule-actions-row">
          <Input value={projectNumberInput} onChange={(event) => setProjectNumberInput(event.target.value)} placeholder={t("Project number filter (optional)")} className="max-w-sm" data-testid="admin-project-schedule-project-filter-input" />
          <Button type="button" variant="outline" onClick={applyProjectFilter} data-testid="admin-project-schedule-apply-filter-button">{t("Apply filter")}</Button>
          <Button type="button" variant="outline" onClick={() => load(projectNumber)} data-testid="admin-project-schedule-refresh-button"><RefreshCw className="mr-2 h-4 w-4" /> {t("Refresh")}</Button>
          <Button type="button" variant="outline" onClick={onBackfill} disabled={working} data-testid="admin-project-schedule-backfill-button"><GitBranchPlus className="mr-2 h-4 w-4" /> {working ? t("Working…") : t("Run compatibility backfill")}</Button>
          <select className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm" value={exportKind} onChange={(event) => setExportKind(event.target.value)} data-testid="admin-project-schedule-export-kind-select">
            {EXPORT_OPTIONS.map(([value, label]) => <option key={value} value={value}>{t(label)}</option>)}
          </select>
          <Button type="button" variant="outline" onClick={onExport} disabled={!projectNumber || !versions.find((item) => item.status === "active")} data-testid="admin-project-schedule-export-button"><Download className="mr-2 h-4 w-4" /> {t("Export schedule")}</Button>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3" data-testid="admin-project-schedule-summary-grid">
          {cards.map(([label, value]) => (
            <div key={label} className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm" data-testid={`admin-project-schedule-summary-${label}`}>
              <div className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">{t(String(label).replace(/-/g, " "))}</div>
              <div className="mt-2 text-3xl font-black text-slate-900">{value}</div>
            </div>
          ))}
        </div>

        <Alert data-testid="admin-project-schedule-guardrail-alert">
          <ShieldCheck className="h-4 w-4" />
          <AlertTitle>{t("Planning trust lines")}</AlertTitle>
          <AlertDescription>
            {t("The schedule remains planning truth only. Budget, commitments, actual cost, forecast, revenue, billing, and collections stay separate. Constraints remain governed operational records, not free-form notes.")}
          </AlertDescription>
        </Alert>

        <Tabs defaultValue="review" className="space-y-4" data-testid="admin-project-schedule-tabs">
          <TabsList data-testid="admin-project-schedule-tabs-list">
            <TabsTrigger value="review" data-testid="admin-project-schedule-review-tab">{t("Review queue")}</TabsTrigger>
            <TabsTrigger value="versions" data-testid="admin-project-schedule-versions-tab">{t("Versions")}</TabsTrigger>
            <TabsTrigger value="actuals" data-testid="admin-project-schedule-actuals-tab">{t("C5 actuals")}</TabsTrigger>
            <TabsTrigger value="imports" data-testid="admin-project-schedule-imports-tab">{t("Imports")}</TabsTrigger>
          </TabsList>

          <TabsContent value="review" className="space-y-6" data-testid="admin-project-schedule-review-panel">
            <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm" data-testid="admin-project-schedule-review-queue-section">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-xl font-black text-slate-900">{t("Governed review queue")}</h2>
                  <p className="mt-1 text-sm text-slate-600">{t("Unresolved schedule mappings, legacy compatibility items, and review-only distribution requests stay visible here.")}</p>
                </div>
                <Badge variant="secondary" data-testid="admin-project-schedule-review-count-badge">{reviewQueue.length}</Badge>
              </div>
              <div className="mt-4 space-y-3">
                {reviewQueue.map((row) => (
                  <div key={row.review_id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid={`admin-project-schedule-review-item-${row.review_id}`}>
                    <div className="flex items-center justify-between gap-3">
                      <div className="font-semibold text-slate-900">{row.title}</div>
                      <Badge variant={row.status === "resolved" ? "default" : "outline"}>{row.status}</Badge>
                    </div>
                    <div className="mt-2 text-sm text-slate-600">{row.reason}</div>
                    <div className="mt-2 text-xs text-slate-500">{t("Project")}: {row.project_number || "—"} · {t("Source")}: {row.source_kind || row.source_record_id}</div>
                  </div>
                ))}
                {!loading && reviewQueue.length === 0 ? <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500" data-testid="admin-project-schedule-review-empty-state">{t("No governed schedule review items are open right now.")}</div> : null}
              </div>
            </section>
          </TabsContent>

          <TabsContent value="actuals" className="space-y-6" data-testid="admin-project-schedule-actuals-panel">
            <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm" data-testid="admin-project-schedule-actuals-summary-section">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-xl font-black text-slate-900">{t("C5 actuals oversight")}</h2>
                  <p className="mt-1 text-sm text-slate-600">{t("Admin can inspect candidate volume, approved actuals, and daily work-plan publication without becoming the project authority gate.")}</p>
                </div>
                <Badge variant="secondary" data-testid="admin-project-schedule-actuals-count-badge">{actualsOverview?.summary?.candidates || 0}</Badge>
              </div>
              <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><div className="text-xs uppercase tracking-[0.18em] text-slate-500">{t("Candidates")}</div><div className="mt-2 text-2xl font-black text-slate-900">{actualsOverview?.summary?.candidates || 0}</div></div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><div className="text-xs uppercase tracking-[0.18em] text-slate-500">{t("Approved")}</div><div className="mt-2 text-2xl font-black text-slate-900">{actualsOverview?.summary?.approved || 0}</div></div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><div className="text-xs uppercase tracking-[0.18em] text-slate-500">{t("Review required")}</div><div className="mt-2 text-2xl font-black text-slate-900">{actualsOverview?.summary?.review_required || 0}</div></div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><div className="text-xs uppercase tracking-[0.18em] text-slate-500">{t("Daily plans")}</div><div className="mt-2 text-2xl font-black text-slate-900">{actualsOverview?.summary?.daily_work_plans || 0}</div></div>
              </div>
            </section>

            <section className="grid gap-6 xl:grid-cols-2" data-testid="admin-project-schedule-actuals-detail-grid">
              <div className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm" data-testid="admin-project-schedule-actuals-candidates-section">
                <h3 className="text-lg font-black text-slate-900">{t("Recent candidate evidence")}</h3>
                <div className="mt-4 space-y-3">
                  {(actualsOverview?.candidates || []).slice(0, 10).map((row) => (
                    <div key={row.candidate_id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid={`admin-project-schedule-actual-candidate-${row.candidate_id}`}>
                      <div className="flex items-center justify-between gap-3">
                        <div className="font-semibold text-slate-900">{row.source_report_number || row.source_report_id}</div>
                        <Badge variant={row.review_status === "approved" ? "default" : "outline"}>{row.review_status}</Badge>
                      </div>
                      <div className="mt-2 text-xs text-slate-500">{row.report_date} · {row.activity_resolution?.resolved_activity_id || t("Needs PM review")}</div>
                    </div>
                  ))}
                  {!loading && (actualsOverview?.candidates || []).length === 0 ? <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500">{t("No C5 actual candidate evidence found yet.")}</div> : null}
                </div>
              </div>

              <div className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm" data-testid="admin-project-schedule-actuals-plans-section">
                <h3 className="text-lg font-black text-slate-900">{t("Published daily work plans")}</h3>
                <div className="mt-4 space-y-3">
                  {(actualsOverview?.daily_work_plans || []).slice(0, 10).map((row) => (
                    <div key={row.plan_id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid={`admin-project-schedule-daily-plan-${row.plan_id}`}>
                      <div className="flex items-center justify-between gap-3">
                        <div className="font-semibold text-slate-900">{row.work_date}</div>
                        <Badge variant={row.status === "published" ? "default" : "outline"}>{row.status}</Badge>
                      </div>
                      <div className="mt-2 text-xs text-slate-500">{(row.items || []).length} {t("items")}</div>
                    </div>
                  ))}
                  {!loading && (actualsOverview?.daily_work_plans || []).length === 0 ? <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500">{t("No governed daily work plans published yet.")}</div> : null}
                </div>
              </div>
            </section>
          </TabsContent>

          <TabsContent value="versions" className="space-y-6" data-testid="admin-project-schedule-versions-panel">
            <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm" data-testid="admin-project-schedule-versions-section">
              <h2 className="text-xl font-black text-slate-900">{t("Schedule versions")}</h2>
              <p className="mt-1 text-sm text-slate-600">{t("Use a project filter to inspect additive versions, activities, and work-package coverage without losing the baseline lineage.")}</p>
              <div className="mt-4 grid gap-3">
                {versions.map((row) => (
                  <div key={row.version_id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid={`admin-project-schedule-version-card-${row.version_id}`}>
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="font-semibold text-slate-900">{row.version_name}</div>
                        <div className="mt-1 text-xs text-slate-500">{row.project_number} · {row.version_kind}</div>
                      </div>
                      <Badge variant={row.status === "active" ? "default" : "outline"}>{row.status}</Badge>
                    </div>
                    <div className="mt-2 text-sm text-slate-600">{row.counts?.activity_count || 0} {t("activities")} · {row.counts?.work_package_count || 0} {t("work packages")}</div>
                  </div>
                ))}
                {!loading && versions.length === 0 ? <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500" data-testid="admin-project-schedule-versions-empty-state">{t("No project schedule versions found for the current filter.")}</div> : null}
              </div>
            </section>

            {projectNumber ? (
              <section className="grid gap-6 xl:grid-cols-2" data-testid="admin-project-schedule-detail-grid">
                <div className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm" data-testid="admin-project-schedule-activities-section">
                  <h2 className="text-xl font-black text-slate-900">{t("Active activities")}</h2>
                  <div className="mt-4 space-y-3">
                    {activities.map((row) => (
                      <div key={row.activity_id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid={`admin-project-schedule-activity-row-${row.activity_id}`}>
                        <div className="font-semibold text-slate-900">{row.activity_id} · {row.activity_name}</div>
                        <div className="mt-1 text-xs text-slate-500">{row.work_package_id} · {row.project_cost_code} · {row.status}</div>
                      </div>
                    ))}
                    {!loading && activities.length === 0 ? <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500">{t("No active schedule activities found.")}</div> : null}
                  </div>
                </div>
                <div className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm" data-testid="admin-project-schedule-work-packages-section">
                  <h2 className="text-xl font-black text-slate-900">{t("Active work packages")}</h2>
                  <div className="mt-4 space-y-3">
                    {workPackages.map((row) => (
                      <div key={`${row.version_id}-${row.work_package_id}`} className="rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid={`admin-project-schedule-work-package-row-${row.work_package_id}`}>
                        <div className="font-semibold text-slate-900">{row.work_package_id}</div>
                        <div className="mt-1 text-xs text-slate-500">{row.activity_count || 0} {t("activities")} · {Number(row.planned_hours || 0).toFixed(1)} {t("hours")}</div>
                      </div>
                    ))}
                    {!loading && workPackages.length === 0 ? <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500">{t("No governed work packages found.")}</div> : null}
                  </div>
                </div>
              </section>
            ) : null}
          </TabsContent>

          <TabsContent value="imports" className="space-y-6" data-testid="admin-project-schedule-imports-panel">
            <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm" data-testid="admin-project-schedule-imports-section">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-xl font-black text-slate-900">{t("Recent staged imports")}</h2>
                  <p className="mt-1 text-sm text-slate-600">{t("Use these records to verify source preservation, warnings, and PM approval readiness.")}</p>
                </div>
                <Badge variant="secondary" data-testid="admin-project-schedule-imports-count-badge">{imports.length}</Badge>
              </div>
              <div className="mt-4 space-y-3">
                {imports.map((row) => (
                  <div key={row.import_id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid={`admin-project-schedule-import-card-${row.import_id}`}>
                    <div className="flex items-center justify-between gap-3">
                      <div className="font-semibold text-slate-900">{row.filename}</div>
                      <Badge variant={row.status === "activated" ? "default" : "outline"}>{row.status}</Badge>
                    </div>
                    <div className="mt-2 text-xs text-slate-500">{row.source_kind} · {row.target_version_kind} · {row.total_rows} {t("rows")}</div>
                  </div>
                ))}
                {!loading && imports.length === 0 ? <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500" data-testid="admin-project-schedule-imports-empty-state">{t("No schedule imports found for the current filter.")}</div> : null}
              </div>
            </section>

            {importDetail ? (
              <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm" data-testid="admin-project-schedule-import-detail-section">
                <h2 className="text-xl font-black text-slate-900">{t("Latest import evidence")}</h2>
                <p className="mt-1 text-sm text-slate-600">{t("This evidence is advisory only; PM approval remains the activation gate.")}</p>
                <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid="admin-project-schedule-import-evidence-card">
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