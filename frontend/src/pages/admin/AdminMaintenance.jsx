// TRACK 25 · SPRINT 6 · Admin OS · Maintenance Domain.
//
// Deep-link only. Every maintenance operation lives in the OCC
// operations console (dry-run → apply → audit). This page groups
// them into user-friendly clusters so admins do not need to hunt
// through the OCC console to find the right operation.
import React from "react";
import { Archive, Cloud, ShieldCheck, Sparkles, Mail, Users, Activity } from "lucide-react";
import DomainLandingShell from "@/components/admin/trust/DomainLandingShell";

// Small helper: each maintenance card is really a "shortcut" whose
// status is derived from the OCC overview endpoint. We map card ->
// list of operation-id prefixes to summarise health.
function _byCategory(probes, categories) {
  const p = probes.occ;
  if (!p?.ok) return { status: "unknown", summary: "OCC overview unreachable.", evidence: { error: p?.error } };
  const ops = (p.body?.operations || []).filter((o) => categories.includes(o.category));
  const critical = ops.filter((o) => (o.status_snapshot?.status || "") === "critical").length;
  const warning = ops.filter((o) => (o.status_snapshot?.status || "") === "warning").length;
  const status = critical > 0 ? "red" : warning > 0 ? "yellow" : ops.length ? "green" : "unknown";
  return { status,
    summary: `${ops.length} operation(s) · ${critical} critical · ${warning} attention`,
    recommended_action: critical || warning ? "Open OCC to run the affected operation." : "",
    evidence: { operations_summary: ops.map((o) => ({ id: o.id, status: (o.status_snapshot||{}).status })) } };
}

const manifest = {
  id: "maintenance",
  label: "Maintenance",
  subtitle: "Every safe maintenance operation, grouped by domain. Actions run in OCC (dry-run first).",
  probes: [
    { id: "occ", path: "/admin/operations-control/overview" },
  ],
  cards: [
    { id: "storage-maint", section: "storage-backups", title: "Storage Maintenance",
      endpoint: "/api/admin/operations-control/overview (category=storage)",
      drilldown: "/admin/storage-recovery",
      evaluator: (p) => _byCategory(p, ["storage"]) },
    { id: "backup-maint", section: "storage-backups", title: "Backup Maintenance",
      endpoint: "/api/admin/operations-control/overview (category=backups)",
      drilldown: "/admin/storage-recovery",
      evaluator: (p) => _byCategory(p, ["backups"]) },
    { id: "r2-maint", section: "storage-backups", title: "R2 Maintenance",
      endpoint: "/api/admin/operations-control/overview (category=r2)",
      drilldown: "/admin/storage-recovery",
      evaluator: (p) => _byCategory(p, ["r2"]) },
    { id: "email-maint", section: "communications-ai", title: "Email Maintenance",
      endpoint: "/api/admin/operations-control/overview (category=email)",
      drilldown: "/admin/communications",
      evaluator: (p) => _byCategory(p, ["email"]) },
    { id: "ai-maint", section: "communications-ai", title: "AI Maintenance",
      endpoint: "/api/admin/operations-control/overview (category=ai)",
      drilldown: "/admin/ai-operations",
      evaluator: (p) => _byCategory(p, ["ai"]) },
    { id: "daily-report-maint", section: "communications-ai", title: "Daily Report Maintenance",
      endpoint: "/api/admin/operations-control/overview (category=daily_reports)",
      drilldown: "/admin/daily",
      evaluator: (p) => _byCategory(p, ["daily_reports"]) },
    { id: "security-maint", section: "trust-security", title: "Security Maintenance",
      endpoint: "/api/admin/operations-control/overview (category=security)",
      drilldown: "/admin/identity-security",
      evaluator: (p) => _byCategory(p, ["security"]) },
    { id: "deployment-maint", section: "trust-security", title: "Deployment Maintenance",
      endpoint: "/api/admin/operations-control/overview (category=deployment)",
      drilldown: "/admin/governance-trust",
      evaluator: (p) => _byCategory(p, ["deployment"]) },
    { id: "health-maint", section: "trust-security", title: "Health / Diagnostics Maintenance",
      endpoint: "/api/admin/operations-control/overview (category=health)",
      drilldown: "/admin/diagnostics",
      evaluator: (p) => _byCategory(p, ["health"]) },
  ],
  sections: [
    { id: "storage-backups", label: "Storage · Backups · R2", icon: Archive,
      cards: ["storage-maint", "backup-maint", "r2-maint"] },
    { id: "communications-ai", label: "Communications · AI · Daily Reports", icon: Mail,
      cards: ["email-maint", "ai-maint", "daily-report-maint"] },
    { id: "trust-security", label: "Security · Deployment · Health", icon: ShieldCheck,
      cards: ["security-maint", "deployment-maint", "health-maint"] },
  ],
  maintenance_actions: [
    { id: "occ-console", title: "Full Maintenance Operations Console",
      deep_link: "/admin/operations-control",
      description: "Every registered maintenance op with dry-run → apply → audit.",
      never_touches: "Read-only until you dry-run + confirm." },
    { id: "storage.safe_cleanup", title: "Run Safe Cleanup (dry-run)",
      description: "Highlights the storage safe-cleanup card in OCC.",
      never_touches: "Dry-run only until you enter the phrase and apply." },
    { id: "backups.health", title: "Refresh Backup Health",
      description: "Highlights the backups.health probe in OCC.",
      never_touches: "Read-only probe." },
    { id: "r2.health", title: "Refresh R2 Health",
      description: "Highlights the r2.health probe in OCC.",
      never_touches: "Read-only probe." },
  ],
  trust_gaps: [
    { id: "gap-maint-queue-admin", title: "Background queue / worker admin UI",
      severity: "P2", owner: "platform-workers", target_track: "27.13", risk: "low",
      current_status: "Scheduler runs surfaced; general queue admin not.", blocks_production: false },
    { id: "gap-maint-history-summary", title: "Cross-domain maintenance history summary",
      severity: "P2", owner: "platform-trust", target_track: "27.13", risk: "low",
      current_status: "Per-op audit only; no cross-domain roll-up.", blocks_production: false },
  ],
  source_endpoints_line: "/api/admin/operations-control/overview (grouped by category)",
};

export default function AdminMaintenance() {
  return <DomainLandingShell manifest={manifest} testidPrefix="admin-maintenance" />;
}
