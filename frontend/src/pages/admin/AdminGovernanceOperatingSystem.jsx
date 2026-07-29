import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle, ArrowRight, Ban, GitBranch, RefreshCw, ShieldCheck, Users, Zap } from "lucide-react";
import { toast } from "sonner";
import LegacyAdminModernShell from "@/components/admin/LegacyAdminModernShell";
import { usePageTitle } from "@/lib/usePageTitle";
import { formatPlatformTime } from "@/lib/platformTime";
import { operationalError } from "@/lib/errors";
import { approveGovernanceRequest, fetchGovernanceApprovalFlows, fetchGovernanceDecisions, fetchGovernanceDelegations, fetchGovernanceHealth, fetchGovernanceOverview, fetchGovernanceOverrides } from "@/lib/enterpriseGovernanceApi";

function StatCard({ label, value, icon: Icon, testId }) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm" data-testid={testId}>
      <div className="flex items-center gap-2 text-slate-500"><Icon className="h-4 w-4" /><span className="text-[11px] uppercase tracking-[0.22em]">{label}</span></div>
      <div className="mt-3 text-3xl font-black text-slate-950">{value}</div>
    </div>
  );
}

export default function AdminGovernanceOperatingSystem() {
  usePageTitle("Enterprise Governance · Admin");
  const [overview, setOverview] = useState(null);
  const [health, setHealth] = useState(null);
  const [approvalFlows, setApprovalFlows] = useState(null);
  const [overrides, setOverrides] = useState(null);
  const [delegations, setDelegations] = useState(null);
  const [decisions, setDecisions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [ov, hl, flows, ovs, dels, dec] = await Promise.all([
        fetchGovernanceOverview(),
        fetchGovernanceHealth(),
        fetchGovernanceApprovalFlows(),
        fetchGovernanceOverrides(),
        fetchGovernanceDelegations(),
        fetchGovernanceDecisions(),
      ]);
      setOverview(ov);
      setHealth(hl);
      setApprovalFlows(flows);
      setOverrides(ovs);
      setDelegations(dels);
      setDecisions(dec);
    } catch (e) {
      setError(operationalError(e, "Could not load Enterprise Governance."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const pendingRequest = useMemo(() => (approvalFlows?.requests || []).find((item) => item.status === "pending"), [approvalFlows]);

  const approvePending = useCallback(async () => {
    if (!pendingRequest?.id) return;
    setActing(true);
    try {
      await approveGovernanceRequest(pendingRequest.id, { note: "Approved from Enterprise Governance admin surface." });
      toast.success("Approval request approved.");
      await load();
    } catch (e) {
      toast.error(operationalError(e, "Approval failed."));
    } finally {
      setActing(false);
    }
  }, [load, pendingRequest]);

  const counts = overview?.counts || {};
  const recentDecisions = decisions?.items || health?.recent_decisions || [];
  const recentOverrides = overrides?.items || [];
  const recentDelegations = delegations?.items || [];

  const delegationState = (row) => {
    if (!row?.expires_at) return "Active";
    return new Date(row.expires_at).getTime() <= Date.now() ? "Expired" : "Active";
  };

  return (
    <LegacyAdminModernShell
      title="Enterprise Governance"
      subtitle="Identity projection, policy evaluation, approval control, delegation, overrides, and audit governance."
      breadcrumb={[{ label: "Governance" }, { label: "Enterprise Governance" }]}
      testidPrefix="admin-governance-os"
    >
      <div className="mb-4 flex flex-wrap gap-2">
        <Link to="/admin/governance/roles" className="rounded-full border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50" data-testid="gov-nav-roles">Roles</Link>
        <Link to="/admin/governance/permissions" className="rounded-full border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50" data-testid="gov-nav-permissions">Permissions</Link>
        <Link to="/admin/governance/policies" className="rounded-full border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50" data-testid="gov-nav-policies">Policies</Link>
        <Link to="/admin/governance/approval-flows" className="rounded-full border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50" data-testid="gov-nav-approval-flows">Approval Flows</Link>
        <Link to="/admin/governance/emergency-overrides" className="rounded-full border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50" data-testid="gov-nav-overrides">Overrides</Link>
        <button type="button" onClick={load} className="inline-flex items-center gap-2 rounded-full border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50" data-testid="gov-refresh-button"><RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />Refresh</button>
      </div>

      {error ? <div className="mb-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800" data-testid="gov-error-banner">{error}</div> : null}
      {loading ? <div className="mb-4 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600" data-testid="gov-loading-banner">Refreshing governed state…</div> : null}

      <div className="grid gap-4 lg:grid-cols-3 xl:grid-cols-6" data-testid="gov-overview-stats">
        <StatCard label="Identity Projections" value={counts.identity_projections || 0} icon={Users} testId="gov-stat-identities" />
        <StatCard label="Roles" value={counts.roles || 0} icon={ShieldCheck} testId="gov-stat-roles" />
        <StatCard label="Permissions" value={counts.permissions || 0} icon={GitBranch} testId="gov-stat-permissions" />
        <StatCard label="Pending Approvals" value={counts.pending_approvals || 0} icon={AlertTriangle} testId="gov-stat-approvals" />
        <StatCard label="Active Delegations" value={counts.active_delegations || 0} icon={ArrowRight} testId="gov-stat-delegations" />
        <StatCard label="Pending Overrides" value={counts.pending_overrides || 0} icon={Zap} testId="gov-stat-overrides" />
      </div>

      <div className="mt-6 grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" data-testid="gov-decision-panel">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-[11px] uppercase tracking-[0.24em] text-slate-500">Governed decisions</div>
              <h2 className="mt-2 text-2xl font-black text-slate-950">Recent allow / deny outcomes</h2>
            </div>
            <div className={`rounded-full px-3 py-1 text-xs font-semibold ${health?.status === "healthy" ? "bg-emerald-100 text-emerald-900" : "bg-amber-100 text-amber-900"}`} data-testid="gov-health-pill">{health?.status || "unknown"}</div>
          </div>
          <div className="mt-4 space-y-3" data-testid="gov-decision-list">
            {recentDecisions.slice(0, 12).map((row) => (
              <div key={row.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-3" data-testid={`gov-decision-${row.id}`}>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="text-sm font-semibold text-slate-950">{row.action_key}</div>
                  <div className={`rounded-full px-2.5 py-1 text-xs font-semibold ${row.decision === "allow" ? "bg-emerald-100 text-emerald-900" : "bg-rose-100 text-rose-900"}`}>{row.decision}</div>
                </div>
                <div className="mt-1 text-sm text-slate-600" data-testid={`gov-decision-reason-${row.id}`}>{row.explanation?.decision_reason || row.reason}</div>
                <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-slate-600" data-testid={`gov-decision-meta-${row.id}`}>
                  <span className="rounded-full bg-white px-2 py-1">Policy {row.policy_id || row.policy_snapshot?.policy_id || "—"} v{row.policy_version || row.policy_snapshot?.version || "—"}</span>
                  <span className="rounded-full bg-white px-2 py-1">Decision {row.decision_id || row.id}</span>
                  <span className="rounded-full bg-white px-2 py-1">Approval {row.explanation?.approval?.status || (row.approval_required ? "pending" : "not_required")}</span>
                  <span className="rounded-full bg-white px-2 py-1">Delegation {row.explanation?.delegation?.status || "none"}</span>
                  <span className="rounded-full bg-white px-2 py-1">Project {row.explanation?.project_assignment?.status || "not_required"}</span>
                </div>
                <div className="mt-2 text-xs text-slate-500">{row.actor_email} · {row.decided_at ? formatPlatformTime(row.decided_at) : "—"}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" data-testid="gov-approval-panel">
            <div className="text-[11px] uppercase tracking-[0.24em] text-slate-500">Approval framework</div>
            <h2 className="mt-2 text-xl font-black text-slate-950">Pending reusable approvals</h2>
            {pendingRequest ? (
              <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 p-4" data-testid={`gov-pending-request-${pendingRequest.id}`}>
                <div className="text-sm font-semibold text-slate-950">{pendingRequest.approval_flow_id}</div>
                <div className="mt-1 text-sm text-slate-600">{pendingRequest.action_key} · {pendingRequest.resource_type}</div>
                <div className="mt-1 text-xs text-slate-500">Requested by {pendingRequest.requested_by?.email || "—"}</div>
                <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-slate-600" data-testid="gov-pending-request-meta">
                  <span className="rounded-full bg-white px-2 py-1">Required roles: {(pendingRequest.required_roles || []).join(", ") || "—"}</span>
                  <span className="rounded-full bg-white px-2 py-1">Communications: {(pendingRequest.communications || []).length}</span>
                </div>
                <button type="button" onClick={approvePending} disabled={acting} className="mt-3 rounded-full border border-emerald-300 bg-emerald-50 px-3 py-2 text-sm font-semibold text-emerald-900 hover:bg-emerald-100 disabled:opacity-60" data-testid="gov-approve-request-button">Approve request</button>
              </div>
            ) : <div className="mt-4 text-sm text-slate-500" data-testid="gov-no-pending-approvals">No pending approval requests.</div>}
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" data-testid="gov-delegation-panel">
            <div className="flex items-center gap-2 text-slate-500"><ArrowRight className="h-4 w-4" /><span className="text-[11px] uppercase tracking-[0.24em]">Delegated authority</span></div>
            <div className="mt-4 space-y-3" data-testid="gov-delegation-list">
              {recentDelegations.slice(0, 4).map((row) => {
                const state = delegationState(row);
                return (
                  <div key={row.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-3" data-testid={`gov-delegation-${row.id}`}>
                    <div className="flex items-center justify-between gap-2">
                      <div className="text-sm font-semibold text-slate-950">{row.delegate_email || row.delegate_user_id}</div>
                      <div className={`rounded-full px-2.5 py-1 text-xs font-semibold ${state === "Expired" ? "bg-rose-100 text-rose-900" : "bg-emerald-100 text-emerald-900"}`}>{state}</div>
                    </div>
                    <div className="mt-1 text-sm text-slate-600">{(row.permissions || []).join(", ") || "No delegated permissions"}</div>
                    <div className="mt-1 text-xs text-slate-500">Delegated by {row.delegator_email || row.delegator_user_id} · Expires {row.expires_at ? formatPlatformTime(row.expires_at) : "—"}</div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" data-testid="gov-override-panel">
            <div className="flex items-center gap-2 text-slate-500"><Ban className="h-4 w-4" /><span className="text-[11px] uppercase tracking-[0.24em]">Emergency overrides</span></div>
            <div className="mt-4 space-y-3">
              {recentOverrides.slice(0, 6).map((row) => (
                <div key={row.id} className="rounded-2xl border border-amber-200 bg-amber-50 p-3" data-testid={`gov-override-${row.id}`}>
                  <div className="text-sm font-semibold text-slate-950">{row.requested_capability}</div>
                  <div className="mt-1 text-sm text-slate-600">{row.module_key} · {row.status}</div>
                  <div className="mt-1 text-xs text-slate-500">{row.justification}</div>
                  <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-slate-600" data-testid={`gov-override-meta-${row.id}`}>
                    <span className="rounded-full bg-white px-2 py-1">Policy {row.policy_snapshot?.policy_id || row.denied_policy_id || "—"}</span>
                    <span className="rounded-full bg-white px-2 py-1">Comms {(row.communications || []).length}</span>
                    <span className="rounded-full bg-white px-2 py-1">Expires {row.expires_at ? formatPlatformTime(row.expires_at) : "—"}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </LegacyAdminModernShell>
  );
}
