import { api } from "@/lib/api";

export async function fetchAdminProjectControlsOverview() {
  const { data } = await api.get("/admin/governance/project-controls/overview");
  return data;
}

export async function runAdminProjectControlsBackfill() {
  const { data } = await api.post("/admin/governance/project-controls/backfill/run", {});
  return data;
}

export async function fetchEnterpriseWorkTypes(includeArchived = false) {
  const { data } = await api.get(`/admin/governance/project-controls/work-types?include_archived=${includeArchived ? "true" : "false"}`);
  return data;
}

export async function saveEnterpriseWorkType(payload, workTypeId = "") {
  const method = workTypeId ? "patch" : "post";
  const path = workTypeId
    ? `/admin/governance/project-controls/work-types/${encodeURIComponent(workTypeId)}`
    : "/admin/governance/project-controls/work-types";
  const { data } = await api[method](path, payload);
  return data;
}

export async function fetchProjectControlsReviewQueue(projectNumber = "", status = "") {
  const params = new URLSearchParams();
  if (projectNumber) params.set("project_number", projectNumber);
  if (status) params.set("status", status);
  const suffix = params.toString() ? `?${params.toString()}` : "";
  const { data } = await api.get(`/admin/governance/project-controls/review-queue${suffix}`);
  return data;
}

export async function fetchProjectControlsEventContracts() {
  const { data } = await api.get("/admin/governance/project-controls/event-contracts");
  return data;
}

export async function fetchPmProjectControlsOverview(projectNumber) {
  const { data } = await api.get(`/pm/project-controls/overview?project_number=${encodeURIComponent(projectNumber)}`);
  return data;
}

export async function fetchPmWorkTypes() {
  const { data } = await api.get("/pm/project-controls/work-types");
  return data;
}

export async function fetchPmProjectPayItems(projectNumber) {
  const { data } = await api.get(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/pay-items`);
  return data;
}

export async function savePmProjectPayItem(projectNumber, payload) {
  const { data } = await api.post(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/pay-items`, payload);
  return data;
}

export async function fetchPmProjectMappings(projectNumber) {
  const { data } = await api.get(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/mappings`);
  return data;
}

export async function savePmProjectMapping(projectNumber, payload) {
  const { data } = await api.post(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/mappings`, payload);
  return data;
}

export async function fetchPmProjectLookahead(projectNumber) {
  const { data } = await api.get(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/lookahead`);
  return data;
}

export async function savePmProjectLookahead(projectNumber, payload) {
  const { data } = await api.put(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/lookahead`, payload);
  return data;
}

export async function fetchPmProjectLifecycle(projectNumber) {
  const { data } = await api.get(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/lifecycle`);
  return data;
}

export async function savePmProjectLifecycle(projectNumber, payload) {
  const { data } = await api.post(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/lifecycle`, payload);
  return data;
}

export async function archivePmProject(projectNumber, reason = "") {
  const { data } = await api.post(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/archive`, { reason });
  return data;
}

export async function restorePmProject(projectNumber, reason = "") {
  const { data } = await api.post(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/restore`, { reason });
  return data;
}

export async function fetchPmCrewIntelligence(projectNumber) {
  const { data } = await api.get(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/crew-intelligence`);
  return data;
}

export async function confirmPmCrew(projectNumber, payload) {
  const { data } = await api.post(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/crew-intelligence/confirm`, payload);
  return data;
}

export async function setPmCrewSuggestionState(projectNumber, suggestionId, action, note = "") {
  const { data } = await api.post(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/crew-intelligence/suggestions/${encodeURIComponent(suggestionId)}/${encodeURIComponent(action)}`, { note });
  return data;
}

export async function fetchPmProjectWorkLedger(projectNumber, limit = 100) {
  const { data } = await api.get(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/work-ledger?limit=${encodeURIComponent(limit)}`);
  return data;
}

export async function fetchPmOperationalIntelligenceSnapshot(projectNumber, { forceRefresh = false } = {}) {
  const suffix = forceRefresh ? "?force_refresh=true" : "";
  const { data } = await api.get(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/operational-intelligence${suffix}`);
  return data;
}

export async function downloadPmOperationalIntelligenceExport(projectNumber) {
  return api.get(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/operational-intelligence/export`, {
    responseType: "blob",
  });
}

export async function overridePmOperationalIntelligenceRecommendation(projectNumber, recommendationId, payload) {
  const { data } = await api.post(
    `/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/operational-intelligence/recommendations/${encodeURIComponent(recommendationId)}/override`,
    payload,
  );
  return data;
}

export async function fetchAdminProjectBudgetOverview(projectNumber = "") {
  const suffix = projectNumber ? `?project_number=${encodeURIComponent(projectNumber)}` : "";
  const { data } = await api.get(`/admin/governance/project-controls/budget/overview${suffix}`);
  return data;
}

export async function fetchAdminOperationalIntelligenceOverview(projectNumber = "", { forceRefresh = false } = {}) {
  const params = new URLSearchParams();
  if (projectNumber) params.set("project_number", projectNumber);
  if (forceRefresh) params.set("force_refresh", "true");
  const suffix = params.toString() ? `?${params.toString()}` : "";
  const { data } = await api.get(`/admin/governance/project-controls/operational-intelligence/overview${suffix}`);
  return data;
}

export async function runAdminOperationalIntelligenceBackfill(force = false) {
  const suffix = force ? "?force=true" : "";
  const { data } = await api.post(`/admin/governance/project-controls/operational-intelligence/backfill/run${suffix}`, {});
  return data;
}

export async function downloadAdminOperationalIntelligenceExport(projectNumber) {
  return api.get(`/admin/governance/project-controls/operational-intelligence/projects/${encodeURIComponent(projectNumber)}/export`, {
    responseType: "blob",
  });
}

export async function overrideAdminOperationalIntelligenceRecommendation(projectNumber, recommendationId, payload) {
  const { data } = await api.post(
    `/admin/governance/project-controls/operational-intelligence/projects/${encodeURIComponent(projectNumber)}/recommendations/${encodeURIComponent(recommendationId)}/override`,
    payload,
  );
  return data;
}

export async function runAdminProjectBudgetBackfill() {
  const { data } = await api.post("/admin/governance/project-controls/budget/backfill/run", {});
  return data;
}

export async function fetchAdminProjectBudgetReviewQueue(projectNumber = "") {
  const suffix = projectNumber ? `?project_number=${encodeURIComponent(projectNumber)}` : "";
  const { data } = await api.get(`/admin/governance/project-controls/budget/review-queue${suffix}`);
  return data;
}

export async function fetchAdminProjectBudgetVersions(projectNumber) {
  const { data } = await api.get(`/admin/governance/project-controls/budget/versions?project_number=${encodeURIComponent(projectNumber)}`);
  return data;
}

export async function fetchAdminProjectBudgetLines(projectNumber, versionId) {
  const { data } = await api.get(`/admin/governance/project-controls/budget/versions/${encodeURIComponent(versionId)}/lines?project_number=${encodeURIComponent(projectNumber)}`);
  return data;
}

export async function fetchAdminProjectBudgetImports(projectNumber) {
  const { data } = await api.get(`/admin/governance/project-controls/budget/imports?project_number=${encodeURIComponent(projectNumber)}`);
  return data;
}

export async function fetchAdminProjectBudgetImportDetail(projectNumber, importId) {
  const { data } = await api.get(`/admin/governance/project-controls/budget/imports/${encodeURIComponent(importId)}?project_number=${encodeURIComponent(projectNumber)}`);
  return data;
}

export async function downloadAdminBudgetExport(projectNumber, versionId) {
  return api.get(`/admin/governance/project-controls/budget/export/budget?project_number=${encodeURIComponent(projectNumber)}&version_id=${encodeURIComponent(versionId)}`, {
    responseType: "blob",
  });
}

export async function downloadAdminBudgetComparison(projectNumber, leftVersionId, rightVersionId) {
  return api.get(`/admin/governance/project-controls/budget/export/comparison?project_number=${encodeURIComponent(projectNumber)}&left_version_id=${encodeURIComponent(leftVersionId)}&right_version_id=${encodeURIComponent(rightVersionId)}`, {
    responseType: "blob",
  });
}

export async function fetchPmProjectBudgetOverview(projectNumber) {
  const { data } = await api.get(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/budget/overview`);
  return data;
}

export async function fetchPmProjectBudgetVersions(projectNumber) {
  const { data } = await api.get(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/budget/versions`);
  return data;
}

export async function fetchPmProjectBudgetLines(projectNumber, versionId) {
  const { data } = await api.get(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/budget/versions/${encodeURIComponent(versionId)}/lines`);
  return data;
}

export async function fetchPmProjectBudgetReviewQueue(projectNumber) {
  const { data } = await api.get(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/budget/review-queue`);
  return data;
}

export async function fetchPmProjectBudgetImports(projectNumber) {
  const { data } = await api.get(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/budget/imports`);
  return data;
}

export async function fetchPmProjectBudgetImportDetail(projectNumber, importId) {
  const { data } = await api.get(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/budget/imports/${encodeURIComponent(importId)}`);
  return data;
}

export async function createPmProjectBudgetImport(projectNumber, payload) {
  const formData = new FormData();
  formData.append("file", payload.file);
  formData.append("source_kind", payload.source_kind || "csv");
  formData.append("target_version_stage", payload.target_version_stage || "original_approved_budget");
  formData.append("version_name", payload.version_name || "");
  const { data } = await api.post(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/budget/imports`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function reviewPmProjectBudgetImportRow(projectNumber, importId, rowId, payload) {
  const { data } = await api.post(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/budget/imports/${encodeURIComponent(importId)}/rows/${encodeURIComponent(rowId)}/review`, payload);
  return data;
}

export async function activatePmProjectBudgetImport(projectNumber, importId) {
  const { data } = await api.post(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/budget/imports/${encodeURIComponent(importId)}/activate`, {});
  return data;
}

export async function downloadPmBudgetExport(projectNumber, versionId) {
  return api.get(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/budget/export/budget?version_id=${encodeURIComponent(versionId)}`, {
    responseType: "blob",
  });
}

export async function downloadPmBudgetComparison(projectNumber, leftVersionId, rightVersionId) {
  return api.get(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/budget/export/comparison?left_version_id=${encodeURIComponent(leftVersionId)}&right_version_id=${encodeURIComponent(rightVersionId)}`, {
    responseType: "blob",
  });
}

export async function fetchAdminProjectScheduleOverview(projectNumber = "") {
  const suffix = projectNumber ? `?project_number=${encodeURIComponent(projectNumber)}` : "";
  const { data } = await api.get(`/admin/governance/project-controls/schedule/overview${suffix}`);
  return data;
}

export async function runAdminProjectScheduleBackfill() {
  const { data } = await api.post("/admin/governance/project-controls/schedule/backfill/run", {});
  return data;
}

export async function fetchAdminProjectScheduleReviewQueue(projectNumber = "") {
  const suffix = projectNumber ? `?project_number=${encodeURIComponent(projectNumber)}` : "";
  const { data } = await api.get(`/admin/governance/project-controls/schedule/review-queue${suffix}`);
  return data;
}

export async function fetchAdminProjectScheduleVersions(projectNumber) {
  const { data } = await api.get(`/admin/governance/project-controls/schedule/versions?project_number=${encodeURIComponent(projectNumber)}`);
  return data;
}

export async function fetchAdminProjectScheduleActivities(projectNumber, versionId) {
  const { data } = await api.get(`/admin/governance/project-controls/schedule/versions/${encodeURIComponent(versionId)}/activities?project_number=${encodeURIComponent(projectNumber)}`);
  return data;
}

export async function fetchAdminProjectScheduleWorkPackages(projectNumber, versionId = "") {
  const suffix = versionId ? `&version_id=${encodeURIComponent(versionId)}` : "";
  const { data } = await api.get(`/admin/governance/project-controls/schedule/work-packages?project_number=${encodeURIComponent(projectNumber)}${suffix}`);
  return data;
}

export async function fetchAdminProjectScheduleImports(projectNumber) {
  const { data } = await api.get(`/admin/governance/project-controls/schedule/imports?project_number=${encodeURIComponent(projectNumber)}`);
  return data;
}

export async function fetchAdminProjectScheduleImportDetail(projectNumber, importId) {
  const { data } = await api.get(`/admin/governance/project-controls/schedule/imports/${encodeURIComponent(importId)}?project_number=${encodeURIComponent(projectNumber)}`);
  return data;
}

export async function downloadAdminScheduleExport(projectNumber, versionId, exportKind = "master_schedule_csv") {
  return api.get(`/admin/governance/project-controls/schedule/export?project_number=${encodeURIComponent(projectNumber)}&version_id=${encodeURIComponent(versionId)}&export_kind=${encodeURIComponent(exportKind)}`, {
    responseType: "blob",
  });
}

export async function fetchAdminProjectScheduleActualsOverview(projectNumber = "") {
  const suffix = projectNumber ? `?project_number=${encodeURIComponent(projectNumber)}` : "";
  const { data } = await api.get(`/admin/governance/project-controls/schedule/actuals/overview${suffix}`);
  return data;
}

export async function fetchPmProjectScheduleOverview(projectNumber) {
  const { data } = await api.get(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/schedule/overview`);
  return data;
}

export async function fetchPmProjectScheduleVersions(projectNumber) {
  const { data } = await api.get(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/schedule/versions`);
  return data;
}

export async function fetchPmProjectScheduleActivities(projectNumber, versionId) {
  const { data } = await api.get(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/schedule/versions/${encodeURIComponent(versionId)}/activities`);
  return data;
}

export async function fetchPmProjectScheduleWorkPackages(projectNumber, versionId = "") {
  const suffix = versionId ? `?version_id=${encodeURIComponent(versionId)}` : "";
  const { data } = await api.get(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/schedule/work-packages${suffix}`);
  return data;
}

export async function fetchPmProjectScheduleReviewQueue(projectNumber) {
  const { data } = await api.get(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/schedule/review-queue`);
  return data;
}

export async function fetchPmProjectScheduleImports(projectNumber) {
  const { data } = await api.get(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/schedule/imports`);
  return data;
}

export async function fetchPmProjectScheduleImportDetail(projectNumber, importId) {
  const { data } = await api.get(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/schedule/imports/${encodeURIComponent(importId)}`);
  return data;
}

export async function createPmProjectScheduleImport(projectNumber, payload) {
  const formData = new FormData();
  formData.append("file", payload.file);
  formData.append("source_kind", payload.source_kind || "csv");
  formData.append("target_version_kind", payload.target_version_kind || "master_schedule");
  formData.append("version_name", payload.version_name || "");
  const { data } = await api.post(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/schedule/imports`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function reviewPmProjectScheduleImportRow(projectNumber, importId, rowId, payload) {
  const { data } = await api.post(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/schedule/imports/${encodeURIComponent(importId)}/rows/${encodeURIComponent(rowId)}/review`, payload);
  return data;
}

export async function activatePmProjectScheduleImport(projectNumber, importId) {
  const { data } = await api.post(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/schedule/imports/${encodeURIComponent(importId)}/activate`, {});
  return data;
}

export async function fetchPmProjectScheduleLookahead(projectNumber) {
  const { data } = await api.get(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/schedule/lookahead`);
  return data;
}

export async function savePmProjectScheduleLookahead(projectNumber, payload) {
  const { data } = await api.put(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/schedule/lookahead`, payload);
  return data;
}

export async function fetchPmProjectScheduleActualsOverview(projectNumber, workDate = "") {
  const suffix = workDate ? `?work_date=${encodeURIComponent(workDate)}` : "";
  const { data } = await api.get(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/schedule/actuals/overview${suffix}`);
  return data;
}

export async function fetchPmProjectScheduleActualCandidates(projectNumber, status = "") {
  const suffix = status ? `?status=${encodeURIComponent(status)}` : "";
  const { data } = await api.get(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/schedule/actuals/candidates${suffix}`);
  return data;
}

export async function reviewPmProjectScheduleActualCandidate(projectNumber, candidateId, payload) {
  const { data } = await api.post(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/schedule/actuals/candidates/${encodeURIComponent(candidateId)}/review`, payload);
  return data;
}

export async function fetchPmProjectScheduleDailyWorkPlan(projectNumber, workDate = "") {
  const suffix = workDate ? `?work_date=${encodeURIComponent(workDate)}` : "";
  const { data } = await api.get(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/schedule/daily-work-plan${suffix}`);
  return data;
}

export async function savePmProjectScheduleDailyWorkPlan(projectNumber, payload) {
  const { data } = await api.put(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/schedule/daily-work-plan`, payload);
  return data;
}

export async function downloadPmScheduleExport(projectNumber, versionId, exportKind = "master_schedule_csv") {
  return api.get(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/schedule/export?version_id=${encodeURIComponent(versionId)}&export_kind=${encodeURIComponent(exportKind)}`, {
    responseType: "blob",
  });
}

export async function queuePmScheduleEmailExport(projectNumber, payload) {
  const { data } = await api.post(`/pm/project-controls/projects/${encodeURIComponent(projectNumber)}/schedule/export/email`, payload);
  return data;
}
