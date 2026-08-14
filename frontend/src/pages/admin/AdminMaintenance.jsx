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
//
// TD-0007: the matcher now supports id-prefix selection and exclusion in
// addition to category. The "Deployment Maintenance" card previously filtered
// by category "deployment", which does not exist in OperationCategory (deploy
// ops are registered under category "health"), so it always rendered a false
// UNKNOWN. Governance maintenance ops had no card at all and were invisible.
export function matchMaintenanceOps(probes, opts = {}) {
  const { categories = [], idPrefixes = [], excludePrefixes = [] } = opts;
  const p = probes.occ;
  if (!p?.ok) return { status: "unknown", summary: "OCC overview unreachable.", evidence: { error: p?.error } };
  const all = p.body?.operations || [];
  const ops = all.filter((o) => {
    const id = String(o.id || "");
    if (excludePrefixes.some((pre) => id.startsWith(pre))) return false;
    const catMatch = categories.length ? categories.includes(o.category) : false;
    const idMatch = idPrefixes.some((pre) => id.startsWith(pre));
    return catMatch || idMatch;
  });
  const critical = ops.filter((o) => (o.status_snapshot?.status || "") === "critical").length;
  const warning = ops.filter((o) => (o.status_snapshot?.status || "") === "warning").length;
  const status = critical > 0 ? "red" : warning > 0 ? "yellow" : ops.length ? "green" : "unknown";
  return { status,
    summary: `${ops.length} operation(s) · ${critical} critical · ${warning} attention`,
    recommended_action: critical || warning ? "Open OCC to run the affected operation." : "",
    evidence: { operations_summary: ops.map((o) => ({ id: o.id, status: (o.status_snapshot||{}).status })) } };
}

function _byCategory(probes, categories) {
  return matchMaintenanceOps(probes, { categories });
}

const manifest = {
  id: "maintenance",
  label: "Maintenance",
  subtitle: "Every safe maintenance operation, grouped by domain. Actions run in Operations Control after a review step.",
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
      endpoint: "/api/admin/operations-control/overview (deploy.* operations)",
      drilldown: "/admin/governance-trust",
      evaluator: (p) => matchMaintenanceOps(p, { idPrefixes: ["deploy."] }) },
    { id: "health-maint", section: "trust-security", title: "Health / Diagnostics Maintenance",
      endpoint: "/api/admin/operations-control/overview (category=health, excl. deploy.*)",
      drilldown: "/admin/diagnostics",
      evaluator: (p) => matchMaintenanceOps(p, { categories: ["health"], excludePrefixes: ["deploy."] }) },
    { id: "governance-maint", section: "data-governance", title: "Governance Maintenance",
      endpoint: "/api/admin/operations-control/overview (category=governance)",
      drilldown: "/admin/governance-trust",
      evaluator: (p) => _byCategory(p, ["governance"]) },
    { id: "queues-maint", section: "data-governance", title: "Queues & Schedulers Maintenance",
      endpoint: "/api/admin/operations-control/overview (category=queues)",
      drilldown: "/admin/operations-control",
      evaluator: (p) => _byCategory(p, ["queues"]) },
  ],
  sections: [
    { id: "storage-backups", label: "Storage · Backups · R2", icon: Archive,
      cards: ["storage-maint", "backup-maint", "r2-maint"] },
    { id: "communications-ai", label: "Communications · AI · Daily Reports", icon: Mail,
      cards: ["email-maint", "ai-maint", "daily-report-maint"] },
    { id: "trust-security", label: "Security · Deployment · Health", icon: ShieldCheck,
      cards: ["security-maint", "deployment-maint", "health-maint"] },
    { id: "data-governance", label: "Governance · Queues", icon: Users,
      cards: ["governance-maint", "queues-maint"] },
  ],
  maintenance_actions: [
    { id: "occ-console", title: "Full Maintenance Operations Console",
      deep_link: "/admin/operations-control",
      description: "Every registered maintenance task with review → apply → verify.",
      never_touches: "Read-only until you review + confirm." },
    { id: "storage.safe_cleanup", title: "Run Safe Cleanup (review first)",
      description: "Highlights the storage safe-cleanup card in OCC.",
      never_touches: "Review first until you enter the phrase and apply." },
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
      current_status: "Per-op review only; no cross-domain roll-up.", blocks_production: false },
  ],
  source_endpoints_line: "/api/admin/operations-control/overview (grouped by category)",
};

export default function AdminMaintenance() {
  return <DomainLandingShell manifest={manifest} testidPrefix="admin-maintenance" />;
}
