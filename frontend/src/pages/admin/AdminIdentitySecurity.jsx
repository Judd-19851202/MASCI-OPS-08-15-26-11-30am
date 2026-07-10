// TRACK 25 · SPRINT 4 · Admin OS · Identity & Security Domain.
import React from "react";
import { Users, KeyRound, ShieldAlert } from "lucide-react";
import DomainLandingShell from "@/components/admin/trust/DomainLandingShell";

function _sessions(probes) {
  const p = probes.sessions;
  if (!p?.ok) return { status: "unknown", summary: "Session inventory unreachable.", evidence: { error: p?.error } };
  const b = p.body || {};
  const count = Number(b.count || 0);
  const to = !!b.timeouts_enabled;
  const status = to ? "green" : "yellow";
  return { status,
    summary: `${count} active session(s) · timeouts ${to ? "on" : "OFF"}`,
    recommended_action: to ? "" : "Enable session timeouts before production.",
    checked_at: b.server_now,
    evidence: { count, timeouts_enabled: to, tiers: b.tiers } };
}
function _timeout_tiers(probes) {
  const p = probes.sessions;
  if (!p?.ok) return { status: "unknown", summary: "Timeout tiers unreachable." };
  const tiers = p.body?.tiers || {};
  const names = Object.keys(tiers);
  const status = names.length ? "green" : "yellow";
  return { status,
    summary: `${names.length} timeout tier(s) declared: ${names.join(" · ") || "—"}`,
    checked_at: p.body?.server_now,
    evidence: { tiers } };
}
function _governance_selfprotection(probes) {
  const p = probes.selfprotection;
  if (!p?.ok) return { status: "unknown", summary: "Self-protection endpoint unreachable.", evidence: { error: p?.error } };
  const b = p.body || {};
  const findings = b.findings || [];
  const critical = findings.filter((f) => (f.severity || "").toLowerCase() === "critical").length;
  const high = findings.filter((f) => (f.severity || "").toLowerCase() === "high").length;
  const status = critical > 0 ? "red" : high > 0 ? "yellow" : "green";
  return { status,
    summary: `${critical} critical · ${high} high self-protection finding(s)`,
    recommended_action: critical || high ? "Open Governance · Self-Protection to triage." : "",
    checked_at: b.last_scan,
    evidence: { findings_sample: findings.slice(0, 3), counters: b.counters, last_scan: b.last_scan } };
}
function _audit_freshness(probes) {
  const p = probes.audit;
  if (!p?.ok) return { status: "unknown", summary: "Admin audit endpoint unreachable.", evidence: { error: p?.error } };
  const entries = p.body?.entries || [];
  if (!entries.length) return { status: "yellow", summary: "No audit entries visible in the recent window.", evidence: { entries } };
  const latest = entries[0];
  return { status: "green",
    summary: `Most recent audit event: ${latest.action || latest.mode || latest.event_type || "activity"}`,
    checked_at: latest.ts || latest.at || null,
    evidence: { latest, count: entries.length } };
}
function _auth_failures(probes) {
  const p = probes.trust_events;
  if (!p?.ok) return { status: "unknown", summary: "Trust events aggregator unreachable.", evidence: { error: p?.error } };
  const b = p.body || {};
  const n = Number(b.auth_failures_in_window || 0);
  const authKind = (b.by_kind || {}).auth || 0;
  const status = n > 5 ? "red" : n > 0 ? "yellow" : "green";
  const summary = n > 0
    ? `${n} auth failure/lock event(s) in the recent window`
    : `No auth failures in the recent window · ${authKind} auth event(s) total`;
  const action = n > 0 ? "Open Audit Log to inspect the failed attempts." : "";
  const authEvents = (b.events || []).filter((e) => e.kind === "auth").slice(0, 5);
  return { status, summary, recommended_action: action, checked_at: b.generated_at,
    evidence: { auth_failures_in_window: n, recent_auth_events: authEvents } };
}

const manifest = {
  id: "identity-security",
  label: "Identity & Security",
  subtitle: "Sessions · authentication · admin hardening · security posture.",
  probes: [
    { id: "sessions", path: "/admin/sessions/recent" },
    { id: "selfprotection", path: "/admin/governance/self-protection" },
    { id: "audit", path: "/admin/audit?limit=5" },
    { id: "trust_events", path: "/admin/occ/trust-events?limit=25" },
  ],
  cards: [
    { id: "active-sessions", section: "sessions", title: "Active Sessions",
      endpoint: "/api/admin/sessions/recent", drilldown: "/admin/sessions", evaluator: _sessions },
    { id: "timeout-tiers", section: "sessions", title: "Session Timeout Tiers",
      endpoint: "/api/admin/sessions/recent (tiers)", drilldown: "/admin/sessions", evaluator: _timeout_tiers },
    { id: "auth-failures", section: "hardening", title: "Recent Auth Failures",
      endpoint: "/api/admin/occ/trust-events",
      drilldown: "/admin/audit-log", evaluator: _auth_failures },
    { id: "self-protection", section: "hardening", title: "Platform Self-Protection",
      endpoint: "/api/admin/governance/self-protection",
      drilldown: "/admin/governance/self-protection", evaluator: _governance_selfprotection },
    { id: "admin-audit-freshness", section: "hardening", title: "Admin Audit Freshness",
      endpoint: "/api/admin/audit", drilldown: "/admin/audit-log", evaluator: _audit_freshness },
  ],
  sections: [
    { id: "sessions", label: "Sessions & Timeouts", icon: Users, cards: ["active-sessions", "timeout-tiers"] },
    { id: "hardening", label: "Hardening & Audit", icon: ShieldAlert, cards: ["auth-failures", "self-protection", "admin-audit-freshness"] },
  ],
  maintenance_actions: [
    { id: "sessions-admin", title: "Sessions Admin",
      deep_link: "/admin/sessions",
      description: "Inspect and revoke active sessions across all portals.",
      never_touches: "Only revokes when you confirm each row." },
    { id: "mfa-admin", title: "Multi-Factor Auth",
      deep_link: "/admin/mfa",
      description: "Super-admin MFA enrollment and recovery.",
      never_touches: "Read-only until you enroll or revoke." },
    { id: "people-admin", title: "People & Access",
      deep_link: "/admin/people",
      description: "Admin / PM / HR / Safety / Dispatch / Shop directories.",
      never_touches: "Read-only until you save a change." },
  ],
  trust_gaps: [
    { id: "gap-sec-locked-users", title: "Locked users / brute-force lock list",
      severity: "P2", owner: "platform-security", target_track: "27.11", risk: "low",
      current_status: "Not surfaced.", blocks_production: false },
    { id: "gap-sec-passkey-status", title: "Passkey enrollment stats",
      severity: "P2", owner: "platform-security", target_track: "27.11", risk: "low",
      current_status: "Prompt exists but no aggregate roster surface.", blocks_production: false },
    { id: "gap-sec-rbac-matrix", title: "RBAC role → permission matrix admin view",
      severity: "P2", owner: "platform-security", target_track: "27.12", risk: "low",
      current_status: "Enforced in backend — no admin visualization.", blocks_production: false },
  ],
  source_endpoints_line: "/api/admin/sessions/recent · /api/admin/governance/self-protection · /api/admin/audit · /api/admin/occ/trust-events",
};

export default function AdminIdentitySecurity() {
  return <DomainLandingShell manifest={manifest} testidPrefix="admin-identity-security" />;
}
