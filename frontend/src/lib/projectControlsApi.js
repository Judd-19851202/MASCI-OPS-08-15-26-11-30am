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
