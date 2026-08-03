import React from "react";
import AdminGovernanceListPage from "@/pages/admin/AdminGovernanceListPage";
import AdminGovernanceHierarchyFoundation from "@/pages/admin/AdminGovernanceHierarchyFoundation";
import {
  fetchGovernanceApprovalFlows,
  fetchGovernanceAudit,
  fetchGovernanceAuthority,
  fetchGovernanceDecisions,
  fetchGovernanceDelegations,
  fetchGovernanceHealth,
  fetchGovernanceIdentities,
  fetchGovernanceOrganization,
  fetchGovernanceOverrides,
  fetchGovernancePermissions,
  fetchGovernancePolicies,
  fetchGovernanceRoles,
  fetchGovernanceSod,
  fetchGovernanceVersions,
} from "@/lib/enterpriseGovernanceApi";

export function AdminGovernanceOrganizationPage() {
  return <AdminGovernanceHierarchyFoundation />;
}
export function AdminGovernanceIdentitiesPage() {
  return <AdminGovernanceListPage title="Identity Projections" subtitle="Policy-ready identity context derived from canonical auth owners." breadcrumb={[{ label: "Enterprise Governance", to: "/admin/governance" }, { label: "Identities" }]} testidPrefix="gov-identities" loader={fetchGovernanceIdentities} />;
}
export function AdminGovernanceRolesPage() {
  return <AdminGovernanceListPage title="Roles" subtitle="Configurable enterprise roles." breadcrumb={[{ label: "Enterprise Governance", to: "/admin/governance" }, { label: "Roles" }]} testidPrefix="gov-roles" loader={fetchGovernanceRoles} transform={(data) => ({ items: data.items || {} })} />;
}
export function AdminGovernancePermissionsPage() {
  return <AdminGovernanceListPage title="Permissions" subtitle="Registry-controlled permissions." breadcrumb={[{ label: "Enterprise Governance", to: "/admin/governance" }, { label: "Permissions" }]} testidPrefix="gov-permissions" loader={fetchGovernancePermissions} transform={(data) => ({ items: data.items || {} })} />;
}
export function AdminGovernancePoliciesPage() {
  return <AdminGovernanceListPage title="Policies" subtitle="Versioned governance policies." breadcrumb={[{ label: "Enterprise Governance", to: "/admin/governance" }, { label: "Policies" }]} testidPrefix="gov-policies" loader={fetchGovernancePolicies} transform={(data) => ({ items: data.items || {} })} />;
}
export function AdminGovernanceApprovalFlowsPage() {
  return <AdminGovernanceListPage title="Approval Flows" subtitle="Reusable approval definitions and requests." breadcrumb={[{ label: "Enterprise Governance", to: "/admin/governance" }, { label: "Approval Flows" }]} testidPrefix="gov-approval-flows" loader={fetchGovernanceApprovalFlows} transform={(data) => ({ items: [...Object.entries(data.items || {}).map(([id, value]) => ({ id, ...(value || {}) })), ...(data.requests || [])] })} />;
}
export function AdminGovernanceDelegationsPage() {
  return <AdminGovernanceListPage title="Delegations" subtitle="Temporary and auditable delegated authority." breadcrumb={[{ label: "Enterprise Governance", to: "/admin/governance" }, { label: "Delegations" }]} testidPrefix="gov-delegations" loader={fetchGovernanceDelegations} />;
}
export function AdminGovernanceSodPage() {
  return <AdminGovernanceListPage title="Separation of Duties" subtitle="Conflict-prevention governance rules." breadcrumb={[{ label: "Enterprise Governance", to: "/admin/governance" }, { label: "Separation of Duties" }]} testidPrefix="gov-sod" loader={fetchGovernanceSod} transform={(data) => ({ items: data.items || {} })} />;
}
export function AdminGovernanceAuthorityPage() {
  return <AdminGovernanceListPage title="Authority Levels" subtitle="Authority hierarchy for policy enforcement." breadcrumb={[{ label: "Enterprise Governance", to: "/admin/governance" }, { label: "Authority" }]} testidPrefix="gov-authority" loader={fetchGovernanceAuthority} transform={(data) => ({ items: data.items || {} })} />;
}
export function AdminGovernanceOverridesPage() {
  return <AdminGovernanceListPage title="Emergency Overrides" subtitle="Preview-safe, fully auditable override records." breadcrumb={[{ label: "Enterprise Governance", to: "/admin/governance" }, { label: "Emergency Overrides" }]} testidPrefix="gov-overrides" loader={fetchGovernanceOverrides} />;
}
export function AdminGovernanceDecisionsPage() {
  return <AdminGovernanceListPage title="Governance Decisions" subtitle="Allow / deny / approval outcomes." breadcrumb={[{ label: "Enterprise Governance", to: "/admin/governance" }, { label: "Decisions" }]} testidPrefix="gov-decisions" loader={fetchGovernanceDecisions} />;
}
export function AdminGovernanceAuditPage() {
  return <AdminGovernanceListPage title="Governance Audit" subtitle="Governance audit history." breadcrumb={[{ label: "Enterprise Governance", to: "/admin/governance" }, { label: "Audit" }]} testidPrefix="gov-audit" loader={fetchGovernanceAudit} />;
}
export function AdminGovernanceVersionsPage() {
  return <AdminGovernanceListPage title="Governance Versions" subtitle="Registry and baseline version references." breadcrumb={[{ label: "Enterprise Governance", to: "/admin/governance" }, { label: "Versions" }]} testidPrefix="gov-versions" loader={fetchGovernanceVersions} transform={(data) => ({ items: [data] })} />;
}
export function AdminGovernanceHealthPage() {
  return <AdminGovernanceListPage title="Governance Health" subtitle="Enterprise governance health summary." breadcrumb={[{ label: "Enterprise Governance", to: "/admin/governance" }, { label: "Health" }]} testidPrefix="gov-health" loader={fetchGovernanceHealth} transform={(data) => ({ items: [data] })} />;
}
