// TRACK 25 · SPRINT 4 · Admin OS · Governance & Trust Domain.
import React from "react";
import { ShieldCheck, ClipboardCheck, History } from "lucide-react";
import DomainLandingShell from "@/components/admin/trust/DomainLandingShell";

function _governance(probes) {
  const p = probes.governance;
  if (!p?.ok) return { status: "unknown", summary: "Governance summary unreachable.", evidence: { error: p?.error } };
  const b = p.body || {};
  const sev = b.severity_counts || {};
  const highs = Number(sev.high || 0) + Number(sev.critical || 0);
  const health = String(b.health_label || "").toLowerCase();
  const status = health === "critical" || highs > 20 ? "red"
    : health === "warning" || highs > 0 ? "yellow" : "green";
  const scanStamp = typeof b.last_scan === "string" ? b.last_scan : null;
  return { status,
    summary: `${highs} high/critical rules · health: ${b.health_label || "unknown"}`,
    recommended_action: highs ? "Open Governance & Trust to triage high-severity rules." : "",
    checked_at: scanStamp,
    evidence: { severity_counts: sev, status_counts: b.status_counts,
      health_label: b.health_label, convergence_score: b.convergence_score,
      rule_counts: b.rule_counts, last_scan: b.last_scan } };
}
function _prod_cert(probes) {
  const p = probes.prod_cert;
  if (!p?.ok) return { status: "unknown", summary: "Production certification unreachable.", evidence: { error: p?.error } };
  const b = p.body || {};
  const band = String(b.platform_band || "").toLowerCase();
  const status = band === "green" || band === "healthy" ? "green"
    : band === "yellow" || band === "warning" ? "yellow"
    : band === "red" || band === "critical" ? "red" : "unknown";
  const counters = b.counters || {};
  return { status,
    summary: `Platform band: ${band || "unknown"} · verified=${counters.verified || 0} failed=${counters.failed || 0} not-yet=${counters.not_yet_exercised || 0}`,
    checked_at: b.generated_at,
    evidence: { platform_band: band, counters, workflows_summary_len: (b.workflows || []).length,
      track: b.track } };
}
function _deploy(probes) {
  const p = probes.deploy;
  if (!p?.ok) return { status: "unknown", summary: "Deploy readiness unreachable.", evidence: { error: p?.error } };
  const b = p.body || {};
  const overall = String(b.overall_status || "").toLowerCase();
  const blockers = Number(b.blocker_count || 0);
  const warns = Number(b.warn_count || 0);
  const status = blockers > 0 || overall === "blocked" ? "red"
    : warns > 0 || overall === "warning" ? "yellow"
    : overall === "ready" ? "green" : "unknown";
  return { status,
    summary: `${b.total_checks || 0} readiness checks · ${blockers} blockers · ${warns} warnings`,
    recommended_action: blockers ? "Resolve blocker(s) before deploy." : "",
    checked_at: b.checked_at,
    evidence: { checks: (b.checks || []).slice(0, 8), overall_status: overall,
      total: b.total_checks } };
}
function _version(probes) {
  const p = probes.version;
  if (!p?.ok) return { status: "unknown", summary: "Version endpoint unreachable.", evidence: { error: p?.error } };
  const b = p.body || {};
  const up = Number(b.uptime_s || 0);
  const h = Math.floor(up / 3600); const m = Math.floor((up % 3600) / 60);
  return { status: "green",
    summary: `Build ${String(b.commit || "").slice(0, 8)} · uptime ${h}h ${m}m`,
    checked_at: b.started_at,
    evidence: { commit: b.commit, release: b.release, started_at: b.started_at, session_timeouts: b.session_timeouts } };
}
function _audit(probes) {
  const p = probes.audit;
  if (!p?.ok) return { status: "unknown", summary: "Admin audit unreachable.", evidence: { error: p?.error } };
  const entries = p.body?.entries || [];
  if (!entries.length) return { status: "yellow", summary: "No admin audit entries in the recent window.", evidence: { entries } };
  const latest = entries[0];
  return { status: "green",
    summary: `Audit chain has recent activity · ${entries.length} entries in window`,
    checked_at: latest.ts || latest.at || null,
    evidence: { latest, count: entries.length } };
}

const manifest = {
  id: "governance-trust",
  label: "Governance & Trust",
  subtitle: "Production certification · governance rules · deploy readiness · audit trail.",
  probes: [
    { id: "governance", path: "/admin/governance/summary" },
    { id: "prod_cert", path: "/admin/production-certification" },
    { id: "deploy", path: "/admin/deploy-readiness" },
    { id: "version", path: "/version" },
    { id: "audit", path: "/admin/audit?limit=5" },
  ],
  cards: [
    { id: "prod-certification", section: "certification", title: "Production Certification",
      endpoint: "/api/admin/production-certification",
      drilldown: "/admin/governance", evaluator: _prod_cert },
    { id: "deploy-readiness", section: "certification", title: "Deploy Readiness",
      endpoint: "/api/admin/deploy-readiness",
      drilldown: "/admin/deploy-recovery", evaluator: _deploy },
    { id: "governance-summary", section: "rules", title: "Governance Rules",
      endpoint: "/api/admin/governance/summary",
      drilldown: "/admin/governance", evaluator: _governance },
    { id: "platform-version", section: "rules", title: "Platform Build & Uptime",
      endpoint: "/api/version", drilldown: "/admin/system-health", evaluator: _version },
    { id: "admin-audit", section: "audit", title: "Admin Audit Freshness",
      endpoint: "/api/admin/audit", drilldown: "/admin/audit-log", evaluator: _audit },
  ],
  sections: [
    { id: "certification", label: "Certification & Deploy", icon: ShieldCheck,
      cards: ["prod-certification", "deploy-readiness"] },
    { id: "rules", label: "Governance Rules & Version", icon: ClipboardCheck,
      cards: ["governance-summary", "platform-version"] },
    { id: "audit", label: "Audit Trail", icon: History, cards: ["admin-audit"] },
  ],
  maintenance_actions: [
    { id: "governance-admin", title: "Governance Admin",
      deep_link: "/admin/governance",
      description: "Rule library, findings triage, convergence trend.",
      never_touches: "Read-only until you resolve a finding." },
    { id: "audit-log", title: "Audit Log",
      deep_link: "/admin/audit-log",
      description: "Full admin audit chain (immutable, append-only).",
      never_touches: "Read-only." },
    { id: "deploy-recovery", title: "Deploy Recovery Playbook",
      deep_link: "/admin/deploy-recovery",
      description: "Deploy readiness checklist + rollback playbook.",
      never_touches: "Read-only until you run a checklist action." },
  ],
  trust_gaps: [
    { id: "gap-gov-regression-status", title: "Regression / Pytest status surface",
      severity: "P1", owner: "platform-trust", target_track: "27.11", risk: "medium",
      current_status: "Local pytest only — CI status not surfaced in admin UI.", blocks_production: false },
    { id: "gap-gov-trust-events", title: "Recent Trust events (cert · deploy · governance) unified log",
      severity: "P2", owner: "platform-trust", target_track: "27.11", risk: "low",
      current_status: "Split across governance summary + audit log.", blocks_production: false },
    { id: "gap-gov-unresolved-blockers", title: "Unresolved production blockers register",
      severity: "P1", owner: "platform-trust", target_track: "27.11", risk: "medium",
      current_status: "Tracked in deploy-readiness only; not surfaced here.", blocks_production: false },
  ],
  source_endpoints_line: "/api/admin/production-certification · /api/admin/deploy-readiness · /api/admin/governance/summary · /api/version · /api/admin/audit",
};

export default function AdminGovernanceTrust() {
  return <DomainLandingShell manifest={manifest} testidPrefix="admin-governance-trust" />;
}
