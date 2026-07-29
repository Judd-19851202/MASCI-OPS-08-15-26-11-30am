import { api } from "@/lib/api";

export async function fetchGovernanceOverview() {
  const { data } = await api.get("/admin/governance/overview");
  return data;
}

export async function fetchGovernanceRegistry() {
  const { data } = await api.get("/admin/governance/registry");
  return data;
}

export async function fetchGovernanceIdentities() {
  const { data } = await api.get("/admin/governance/identities");
  return data;
}

export async function fetchGovernanceOrganization() {
  const { data } = await api.get("/admin/governance/organization");
  return data;
}

export async function fetchGovernancePolicies() {
  const { data } = await api.get("/admin/governance/policies");
  return data;
}

export async function fetchGovernancePermissions() {
  const { data } = await api.get("/admin/governance/permissions");
  return data;
}

export async function fetchGovernanceRoles() {
  const { data } = await api.get("/admin/governance/roles");
  return data;
}

export async function fetchGovernanceApprovalFlows() {
  const { data } = await api.get("/admin/governance/approval-flows");
  return data;
}

export async function approveGovernanceRequest(requestId, payload = {}) {
  const { data } = await api.post(`/admin/governance/approval-flows/requests/${encodeURIComponent(requestId)}/approve`, payload);
  return data;
}

export async function fetchGovernanceDelegations() {
  const { data } = await api.get("/admin/governance/delegations");
  return data;
}

export async function createGovernanceDelegation(payload) {
  const { data } = await api.post("/admin/governance/delegations", payload);
  return data;
}

export async function fetchGovernanceSod() {
  const { data } = await api.get("/admin/governance/separation-of-duties");
  return data;
}

export async function fetchGovernanceAuthority() {
  const { data } = await api.get("/admin/governance/authority");
  return data;
}

export async function fetchGovernanceOverrides() {
  const { data } = await api.get("/admin/governance/emergency-overrides");
  return data;
}

export async function createGovernanceOverride(payload) {
  const { data } = await api.post("/admin/governance/emergency-overrides", payload);
  return data;
}

export async function fetchGovernanceDecisions() {
  const { data } = await api.get("/admin/governance/decisions");
  return data;
}

export async function fetchGovernanceAudit() {
  const { data } = await api.get("/admin/governance/audit");
  return data;
}

export async function fetchGovernanceVersions() {
  const { data } = await api.get("/admin/governance/versions");
  return data;
}

export async function fetchGovernanceHealth() {
  const { data } = await api.get("/admin/governance/health");
  return data;
}
