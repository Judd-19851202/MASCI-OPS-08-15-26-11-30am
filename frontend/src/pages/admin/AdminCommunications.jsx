// TRACK 25 · SPRINT 4 · Admin OS · Communications Domain.
import React from "react";
import { Mail, Send, AlertTriangle } from "lucide-react";
import DomainLandingShell from "@/components/admin/trust/DomainLandingShell";

function _email_v2(probes) {
  const p = probes.email;
  if (!p?.ok) return { status: "unknown", summary: "Email routing status unreachable.", evidence: { error: p?.error } };
  const b = p.body || {};
  const empty = b.critical_empty_route_keys || [];
  const band = String(b.band || "").toLowerCase();
  const status = empty.length > 0 || band === "red" ? "red"
    : ["yellow", "amber"].includes(band) ? "yellow" : "green";
  const counts = b.route_counts || {};
  const summary = `${counts.total || 0} routes configured · ${empty.length} critical empty`;
  const action = empty.length > 0 ? "Fill or reroute the missing critical route keys."
    : status === "yellow" ? (b.band_reason || "Investigate email routing degradation.") : "";
  return { status, summary, recommended_action: action, checked_at: b.ts,
    evidence: { mode: b.mode, band, route_counts: counts, critical_empty_route_keys: empty,
      audit_counters: b.audit_counters, last_v2_audit_age_minutes: b.last_v2_audit_age_minutes,
      band_reason: b.band_reason } };
}
function _email_provider(probes) {
  const p = probes.integrations;
  if (!p?.ok) return { status: "unknown", summary: "Integration probes unreachable.", evidence: { error: p?.error } };
  const resend = (p.body?.probes || []).find((x) => x.id === "resend");
  if (!resend) return { status: "unknown", summary: "No Resend probe available.", evidence: p.body };
  const auto = resend.auto_email_enabled;
  const ok = resend.status === "ok";
  const status = ok ? (auto ? "green" : "yellow") : "red";
  const summary = ok
    ? `Resend key present · auto-email ${auto ? "ON" : "OFF (SAFETY MODE)"}`
    : `Resend probe FAILED · ${resend.message}`;
  const action = !ok ? "Verify Resend API key and pod egress."
    : !auto ? "Auto-email is intentionally OFF in preview — enable in production only." : "";
  return { status, summary, recommended_action: action, checked_at: resend.checked_at,
    evidence: resend };
}
function _email_audit_freshness(probes) {
  const p = probes.email;
  if (!p?.ok) return { status: "unknown", summary: "Audit freshness unreachable." };
  const b = p.body || {};
  const ageMin = Number(b.last_v2_audit_age_minutes ?? -1);
  const status = ageMin < 0 ? "unknown"
    : ageMin > 240 ? "yellow" : "green";
  const summary = ageMin < 0
    ? "No email audit rows observed."
    : `Last email audit row is ${ageMin.toFixed(0)} min old.`;
  const action = status === "yellow" ? "Scheduler may be slow — check /admin/scheduler-runs." : "";
  return { status, summary, recommended_action: action, checked_at: b.ts,
    evidence: { last_v2_audit_age_minutes: ageMin, audit_counters: b.audit_counters,
      latest_audit_rows: b.latest_audit_rows } };
}
function _email_deadletter(probes) {
  const p = probes.email;
  if (!p?.ok) return { status: "unknown", summary: "Dead-letter / delivery-forensics endpoint not wired.", evidence: null,
    recommended_action: "Track 27.10 will expose /api/admin/email-routing/dead-letters." };
  const b = p.body || {};
  const errors24 = Number(b.audit_counters?.errors_last_24h || 0);
  const status = errors24 > 0 ? "yellow" : "unknown";
  const summary = errors24 > 0
    ? `${errors24} email audit errors in last 24h — investigate.`
    : "No dedicated dead-letter endpoint — audit-counter proxy only.";
  return { status, summary,
    recommended_action: errors24 > 0 ? "Open Communications → Email Routing." : "Wire a dedicated dead-letter surface (Track 27.10).",
    checked_at: b.ts, evidence: { audit_counters: b.audit_counters } };
}

const manifest = {
  id: "communications",
  label: "Communications",
  subtitle: "Email routing · providers · audit freshness · dead-letters.",
  probes: [
    { id: "email", path: "/admin/email-routing/v2/status" },
    { id: "integrations", path: "/admin/integrations/health" },
  ],
  cards: [
    { id: "email-routing-v2", section: "routing", title: "Email Routing",
      endpoint: "/api/admin/email-routing/v2/status", drilldown: "/admin/email", evaluator: _email_v2 },
    { id: "email-provider", section: "routing", title: "Email Provider · Resend",
      endpoint: "/api/admin/integrations/health (resend)", drilldown: "/admin/integrations", evaluator: _email_provider },
    { id: "email-audit-freshness", section: "delivery", title: "Audit Freshness",
      endpoint: "/api/admin/email-routing/v2/status (audit)", drilldown: "/admin/email", evaluator: _email_audit_freshness },
    { id: "email-deadletter", section: "delivery", title: "Dead-Letter / Failures",
      endpoint: "/api/admin/email-routing/v2/status (audit_counters.errors_last_24h)",
      drilldown: "/admin/email", evaluator: _email_deadletter },
  ],
  sections: [
    { id: "routing", label: "Routing & Providers", icon: Mail, cards: ["email-routing-v2", "email-provider"] },
    { id: "delivery", label: "Delivery Health", icon: Send, cards: ["email-audit-freshness", "email-deadletter"] },
  ],
  maintenance_actions: [
    { id: "email-config", title: "Open Email Routing Admin",
      deep_link: "/admin/email",
      description: "Route templates, tenant branding, mode switch, audit log.",
      never_touches: "Read-only until you save a change." },
    { id: "digest-config", title: "Digest Configuration",
      deep_link: "/admin/digest-config",
      description: "Weekly / daily digest windows, recipients, categories.",
      never_touches: "Read-only until you save." },
  ],
  trust_gaps: [
    { id: "gap-comm-dead-letter", title: "Dedicated dead-letter surface for failed sends",
      severity: "P1", owner: "platform-comms", target_track: "27.10", risk: "medium",
      current_status: "audit_counters.errors_last_24h is a proxy — no per-message DLQ view.", blocks_production: false },
    { id: "gap-comm-delivery-latency", title: "Delivery latency percentiles",
      severity: "P2", owner: "platform-observability", target_track: "27.10", risk: "low",
      current_status: "Not measured.", blocks_production: false },
    { id: "gap-comm-notification-queue", title: "In-app notification queue health surface",
      severity: "P2", owner: "platform-comms", target_track: "27.11", risk: "low",
      current_status: "Digest counters only — no in-app queue admin view.", blocks_production: false },
  ],
  source_endpoints_line: "/api/admin/email-routing/v2/status · /api/admin/integrations/health",
};

export default function AdminCommunications() {
  return <DomainLandingShell manifest={manifest} testidPrefix="admin-communications" />;
}
