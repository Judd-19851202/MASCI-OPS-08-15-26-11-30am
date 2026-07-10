// TRACK 25 · SPRINT 5 · Admin OS · Platform Configuration Domain.
//
// Shows configured / missing / warning / unknown status for every
// major configurable surface — brand · integrations · AI · email ·
// build/version. Deep-links to the existing configuration pages;
// never renders secrets, only presence/status.
import React from "react";
import { Palette, Plug, Sparkles, Mail, Cog } from "lucide-react";
import DomainLandingShell from "@/components/admin/trust/DomainLandingShell";

function _branding(probes) {
  const p = probes.branding;
  if (!p?.ok) return { status: "unknown", summary: "Branding endpoint unreachable.", evidence: { error: p?.error } };
  const b = p.body || {};
  const name = b.name || b.display_name || b.tenant_name || "—";
  const hasLogo = !!(b.logo_url || b.logo);
  const hasColor = !!(b.primary_color || b.brand_color || b.theme_color);
  const status = name !== "—" && hasLogo && hasColor ? "green"
    : name !== "—" ? "yellow" : "unknown";
  const missing = [!hasLogo && "logo", !hasColor && "brand color"].filter(Boolean);
  return { status,
    summary: name !== "—"
      ? `Tenant "${name}"${missing.length ? ` · missing ${missing.join(" / ")}` : " · fully branded"}`
      : "Branding not configured.",
    recommended_action: missing.length ? `Open Branding admin to configure ${missing.join(" / ")}.` : "",
    checked_at: b.updated_at || null,
    evidence: { name, has_logo: hasLogo, has_color: hasColor, keys: Object.keys(b) } };
}
function _integrations_config(probes) {
  const p = probes.integrations;
  if (!p?.ok) return { status: "unknown", summary: "Integration probes unreachable.", evidence: { error: p?.error } };
  const probesList = p.body?.probes || [];
  const configured = probesList.filter((x) => x.status === "ok" || x.status === "healthy").length;
  const missing = probesList.filter((x) => x.status === "missing_config" || x.status === "not_configured").length;
  const status = missing > 0 ? "yellow" : configured === probesList.length ? "green" : "yellow";
  return { status,
    summary: `${configured}/${probesList.length} integrations configured${missing ? ` · ${missing} missing config` : ""}`,
    recommended_action: missing ? "Open Integrations to complete missing configuration." : "",
    checked_at: p.body?.checked_at,
    evidence: { probes: probesList } };
}
function _ai_config(probes) {
  const p = probes.gateway;
  if (!p?.ok) return { status: "unknown", summary: "AI configuration unreachable.", evidence: { error: p?.error } };
  const b = p.body || {};
  const gwOn = !!b.gateway_enabled;
  const provOK = !!b.resolved_provider_available;
  const status = gwOn && provOK ? "green" : gwOn ? "yellow" : "yellow";
  return { status,
    summary: `Gateway ${gwOn ? "ON" : "OFF"} · provider=${b.resolved_selected_provider || b.default_provider || "—"} · resolved ${provOK ? "OK" : "UNAVAILABLE"}`,
    recommended_action: gwOn && !provOK ? "Configure a working AI provider key." : "",
    evidence: { gateway_enabled: gwOn, provider: b.resolved_selected_provider,
      default: b.default_provider, transport: b.transport } };
}
function _email_config(probes) {
  const p = probes.email;
  if (!p?.ok) return { status: "unknown", summary: "Email configuration unreachable.", evidence: { error: p?.error } };
  const b = p.body || {};
  const missing = (b.critical_empty_route_keys || []).length;
  const total = b.route_counts?.total || 0;
  const status = missing > 0 ? "red" : total ? "green" : "yellow";
  return { status,
    summary: `Mode ${b.mode || "—"} · ${total} routes configured${missing ? ` · ${missing} critical empty` : ""}`,
    recommended_action: missing ? "Fill missing critical email routes." : "",
    checked_at: b.ts,
    evidence: { mode: b.mode, band: b.band, route_counts: b.route_counts,
      critical_empty_route_keys: b.critical_empty_route_keys } };
}
function _version_config(probes) {
  const p = probes.version;
  if (!p?.ok) return { status: "unknown", summary: "Version endpoint unreachable." };
  const b = p.body || {};
  return { status: "green",
    summary: `Build ${String(b.commit || "—").slice(0, 8)} · release ${b.release || "—"} · service ${b.service || "—"}`,
    checked_at: b.started_at,
    evidence: { commit: b.commit, release: b.release, started_at: b.started_at,
      service: b.service, session_timeouts: b.session_timeouts,
      auto_email_enabled: b.auto_email_enabled } };
}
function _notifications(probes) {
  const p = probes.notifications;
  if (!p?.ok) return { status: "unknown", summary: "Notifications digest unreachable.", evidence: { error: p?.error } };
  const b = p.body || {};
  const sections = b.sections || {};
  const secCount = Object.keys(sections).length;
  return { status: secCount ? "green" : "yellow",
    summary: secCount ? `${secCount} notification sections configured for role ${b.role}` : "No notification sections configured.",
    checked_at: b.generated_at,
    evidence: { summary: b.summary, sections_keys: Object.keys(sections) } };
}

const manifest = {
  id: "platform-configuration",
  label: "Platform Configuration",
  subtitle: "Branding · integrations · AI · email · version · notifications.",
  probes: [
    { id: "branding", path: "/branding/current" },
    { id: "integrations", path: "/admin/integrations/health" },
    { id: "gateway", path: "/ai/gateway/status" },
    { id: "email", path: "/admin/email-routing/v2/status" },
    { id: "version", path: "/version" },
    { id: "notifications", path: "/admin/notifications/digest" },
  ],
  cards: [
    { id: "branding", section: "identity", title: "Branding",
      endpoint: "/api/branding/current", drilldown: "/admin/branding", evaluator: _branding },
    { id: "notifications", section: "identity", title: "Notifications Digest",
      endpoint: "/api/admin/notifications/digest", drilldown: "/admin/digest-config", evaluator: _notifications },
    { id: "integrations", section: "integrations", title: "Integrations",
      endpoint: "/api/admin/integrations/health", drilldown: "/admin/integrations", evaluator: _integrations_config },
    { id: "ai-config", section: "integrations", title: "AI Configuration",
      endpoint: "/api/ai/gateway/status", drilldown: "/admin/ai-configuration", evaluator: _ai_config },
    { id: "email-config", section: "runtime", title: "Email Configuration",
      endpoint: "/api/admin/email-routing/v2/status", drilldown: "/admin/email", evaluator: _email_config },
    { id: "version-config", section: "runtime", title: "Build / Version",
      endpoint: "/api/version", drilldown: "/admin/system-health", evaluator: _version_config },
  ],
  sections: [
    { id: "identity", label: "Brand & Notifications", icon: Palette, cards: ["branding", "notifications"] },
    { id: "integrations", label: "Integrations & AI", icon: Plug, cards: ["integrations", "ai-config"] },
    { id: "runtime", label: "Runtime & Build", icon: Cog, cards: ["email-config", "version-config"] },
  ],
  maintenance_actions: [
    { id: "branding-open", title: "Branding Admin", deep_link: "/admin/branding",
      description: "Logos, colors, contact info, tenant metadata.", never_touches: "Read-only until you save." },
    { id: "integrations-open", title: "Integrations Admin", deep_link: "/admin/integrations",
      description: "Motive, Resend, R2, MaintainX credentials.", never_touches: "Never displays secrets." },
    { id: "ai-open", title: "AI Configuration", deep_link: "/admin/ai-configuration",
      description: "Provider · per-module flags · failover.", never_touches: "Read-only until you save." },
    { id: "digest-open", title: "Digest Configuration", deep_link: "/admin/digest-config",
      description: "Notification schedule + audience.", never_touches: "Read-only until you save." },
  ],
  trust_gaps: [
    { id: "gap-cfg-feature-flags", title: "Feature-flag admin surface",
      severity: "P1", owner: "platform-config", target_track: "27.12", risk: "medium",
      current_status: "Flags exist in code (masci.admin.nav.v3 etc) but no admin UI to toggle.", blocks_production: false },
    { id: "gap-cfg-tenant-settings", title: "Tenant settings admin (business hours · timezone default)",
      severity: "P2", owner: "platform-config", target_track: "27.12", risk: "low",
      current_status: "Hard-coded defaults; no per-tenant override UI.", blocks_production: false },
    { id: "gap-cfg-secret-rotation", title: "Secret rotation workflow (Resend / R2 / provider keys)",
      severity: "P1", owner: "platform-security", target_track: "27.13", risk: "medium",
      current_status: "Manual .env edit only.", blocks_production: false },
  ],
  source_endpoints_line: "/api/branding/current · /api/admin/integrations/health · /api/ai/gateway/status · /api/admin/email-routing/v2/status · /api/version · /api/admin/notifications/digest",
};

export default function AdminPlatformConfiguration() {
  return <DomainLandingShell manifest={manifest} testidPrefix="admin-platform-config" />;
}
