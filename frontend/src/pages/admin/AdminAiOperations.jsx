// TRACK 25 · SPRINT 4 · Admin OS · AI Operations Domain.
import React from "react";
import { Sparkles, ShieldCheck, ListChecks } from "lucide-react";
import DomainLandingShell, { unknownCard } from "@/components/admin/trust/DomainLandingShell";

// Card evaluators — each takes probes map -> normalized evaluated card.
function _ai_gateway(probes) {
  const p = probes.gateway;
  if (!p?.ok) return { status: "unknown", summary: "AI gateway status unreachable.", evidence: { error: p?.error }, checked_at: null };
  const b = p.body || {};
  const enabled = !!b.gateway_enabled;
  const resolved = !!b.resolved_provider_available;
  const provider = b.resolved_selected_provider || b.default_provider || "—";
  const status = !enabled ? "yellow" : (resolved ? "green" : "red");
  const summary = !enabled
    ? `Gateway OFF · tenant default ${b.tenant_ai_default_enabled ? "ON" : "OFF"}.`
    : resolved
    ? `Gateway ON · provider ${provider} available.`
    : `Gateway ON · resolved provider ${provider} UNAVAILABLE.`;
  const action = !enabled ? "Enable in AI configuration only if platform requires AI."
    : !resolved ? "Rotate provider key or switch failover provider." : "";
  return { status, summary, recommended_action: action,
    checked_at: b.checked_at || null,
    evidence: { gateway_enabled: enabled, tenant_default: b.tenant_ai_default_enabled,
      resolved_provider: provider, resolved_provider_available: resolved,
      transport: b.transport } };
}
function _ai_dr(probes) {
  const p = probes.dr_meta;
  if (!p?.ok) return { status: "unknown", summary: "Daily Report AI meta unreachable.", evidence: { error: p?.error } };
  const b = p.body || {};
  const available = !!b.ai_available;
  const flag = b.feature_flag;
  const status = available ? "green" : (flag ? "yellow" : "yellow");
  const summary = available
    ? `Daily Report AI ONLINE · provider=${b.provider} model=${b.model}`
    : `Daily Report AI OFFLINE · feature_flag=${flag} · deterministic fallback in use.`;
  return { status, summary, recommended_action: available ? "" : "Enable AI_DAILY_REPORT_SUMMARY_ENABLED to activate.",
    checked_at: null,
    evidence: { feature_flag: flag, ai_available: available, provider: b.provider, model: b.model,
      agents: b.agents, envelope_schema: b.envelope_schema } };
}
function _ai_modules(probes) {
  const p = probes.gateway;
  if (!p?.ok) return { status: "unknown", summary: "AI modules unreachable.", evidence: { error: p?.error } };
  const modules = p.body?.modules || {};
  const rows = Object.entries(modules).map(([k, v]) => ({
    module: k,
    deployment: v.deployment_enabled ? "ON" : "OFF",
    tenant: v.tenant_default_enabled ? "ON" : "OFF",
  }));
  const enabled = rows.filter((r) => r.deployment === "ON").length;
  const status = enabled === 0 ? "yellow" : (enabled < rows.length / 2 ? "yellow" : "green");
  const summary = `${enabled}/${rows.length} AI modules enabled at deployment level.`;
  return { status, summary, evidence: { modules: rows },
    recommended_action: enabled === 0 ? "Enable at least one AI module OR keep gateway OFF." : "",
    checked_at: null };
}
function _ai_prod_cert(probes) {
  const p = probes.prod_cert;
  if (!p?.ok) return { status: "unknown", summary: "Production certification unreachable.", evidence: { error: p?.error } };
  const b = p.body || {};
  const wfs = (b.workflows || []).filter((w) => /ai|summary|vision/i.test(w.id || w.name || ""));
  const failed = wfs.filter((w) => (w.status || "").toLowerCase() === "failed").length;
  const status = failed > 0 ? "red" : wfs.length ? "green" : "unknown";
  return { status,
    summary: `${wfs.length} AI-tagged workflow(s) in production cert · ${failed} failed`,
    evidence: { workflows: wfs, counters: b.counters },
    checked_at: b.generated_at, recommended_action: failed ? "Rerun the failed AI workflow cert." : "" };
}

const manifest = {
  id: "ai-operations",
  label: "AI Operations",
  subtitle: "AI gateway · providers · modules · Daily Report AI health.",
  probes: [
    { id: "gateway", path: "/ai/gateway/status" },
    { id: "dr_meta", path: "/dr-v2/meta" },
    { id: "prod_cert", path: "/admin/production-certification" },
  ],
  cards: [
    { id: "ai-gateway", section: "provider", title: "AI Gateway",
      endpoint: "/api/ai/gateway/status", drilldown: "/admin/ai-configuration", evaluator: _ai_gateway },
    { id: "ai-daily-report", section: "provider", title: "Daily Report AI",
      endpoint: "/api/dr-v2/meta", drilldown: "/admin/ai-configuration", evaluator: _ai_dr },
    { id: "ai-modules", section: "modules", title: "AI Modules · Deployment Flags",
      endpoint: "/api/ai/gateway/status (modules)", drilldown: "/admin/ai-configuration", evaluator: _ai_modules },
    { id: "ai-prod-cert", section: "modules", title: "AI Workflows · Production Cert",
      endpoint: "/api/admin/production-certification", drilldown: "/admin/governance-trust", evaluator: _ai_prod_cert },
  ],
  sections: [
    { id: "provider", label: "Provider & Gateway", icon: Sparkles, cards: ["ai-gateway", "ai-daily-report"] },
    { id: "modules", label: "Modules & Certification", icon: ListChecks, cards: ["ai-modules", "ai-prod-cert"] },
  ],
  maintenance_actions: [
    { id: "ai-configuration", title: "Open AI Configuration",
      deep_link: "/admin/ai-configuration",
      description: "Tune provider selection, per-module tenant flags, failover.",
      never_touches: "Read-only until you save." },
  ],
  trust_gaps: [
    { id: "gap-ai-recent-failures", title: "Recent AI provider failure log surfaced in OCC",
      severity: "P1", owner: "platform-ai", target_track: "27.09", risk: "medium",
      current_status: "Per-call errors in logs only — no aggregate surface.", blocks_production: false },
    { id: "gap-ai-latency", title: "AI call latency histogram",
      severity: "P2", owner: "platform-observability", target_track: "27.09", risk: "low",
      current_status: "Not measured.", blocks_production: false },
    { id: "gap-ai-cost", title: "AI cost & token budget surface",
      severity: "P2", owner: "platform-ai", target_track: "27.10", risk: "low",
      current_status: "Universal LLM key balance not surfaced in admin UI.", blocks_production: false },
  ],
  source_endpoints_line: "/api/ai/gateway/status · /api/dr-v2/meta · /api/admin/production-certification",
};

export default function AdminAiOperations() {
  return <DomainLandingShell manifest={manifest} testidPrefix="admin-ai-ops" />;
}
