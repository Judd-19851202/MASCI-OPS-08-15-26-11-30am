// Admin OS · Domain Map
//
// One calm map for the entire Admin OS sidebar. Every visible admin
// destination lives under one of the sections below.
//
// Contract:
//   - `visibleRoutes`   → shown in the sidebar tree
//   - `hiddenRoutes`    → detail pages / dynamic segments; still
//                         indexed by the command palette so nothing
//                         becomes unreachable via search.
//   - `keywords`        → extra search tokens beyond label + desc so
//                         operators can find pages by intent.
//   - `purpose`         → the section's one-line business reason.
//
// Zero-drift: this map ONLY lists routes that already exist in
// AppRoutes.jsx. Adding a nav entry never invents a new page.

import {
  Home,
  Activity,      // OCC
  Building2,     // Jobs & Projects
  Wrench,        // Fleet & Equipment
  ShieldAlert,   // Safety & Compliance
  Users,         // People & Access
  GraduationCap, // Training
  Sparkles,      // AI & Intelligence
  Mail,          // Communications
  BarChart3,     // Reporting
  History,       // Audit Log
  Archive,       // Historical Records
  HardDrive,     // Storage & Recovery
  ShieldCheck,   // Governance & Trust
  Cog,           // Platform Configuration
  Database,      // Diagnostics
  Compass,       // Admin OS
  ClipboardCheck, FileText, Truck, MapPin, KeyRound, AlertTriangle,
  BookOpen, Film, Cable, NotebookPen,
} from "lucide-react";

export const DOMAINS_V3 = [
  // ────────────────────────────────────────────────────────────────
  // ADMIN OS · 10 canonical domains. Every operator command starts
  // here. This is the platform's operating system view.
  {
    id: "admin-os",
    label: "Admin OS",
    subline: "Platform command center.",
    purpose:
      "Review system health, investigate risks, and open the right " +
      "operational area from one screen.",
    stripe: "#0ea5e9",
    icon: Compass,
    visibleRoutes: [
      { to: "/admin",                          label: "Dashboard",              desc: "Cross-domain posture · live health.",                   end: true, icon: Compass,       keywords: ["dashboard", "landing", "overview", "posture", "domains", "home"] },
      { to: "/admin/operations-control",       label: "Operations Control",     desc: "Platform overview · case activity · admin tools.",       icon: Activity,      keywords: ["occ", "operations", "control", "overview", "cases", "admin"] },
      { to: "/admin/storage-recovery",         label: "Storage & Recovery",     desc: "Disk · object storage · backups · restore.",             icon: HardDrive,     keywords: ["storage", "backup", "recovery", "restore", "disk", "r2"] },
      { to: "/admin/ai-operations",            label: "AI Operations",          desc: "Providers · gateways · AI-powered modules.",             icon: Sparkles,      keywords: ["ai", "gateway", "provider", "openai", "anthropic", "gemini"] },
      { to: "/admin/communications",           label: "Communications",         desc: "Email routing · providers · digests.",                    icon: Mail,          keywords: ["email", "notifications", "routing", "digest"] },
      { to: "/admin/identity-security",        label: "Identity & Security",    desc: "Sessions · access · protection.",                         icon: Users,         keywords: ["sessions", "auth", "mfa", "security"] },
      { to: "/admin/governance-trust",         label: "Standards & Readiness",  desc: "Release reviews · go-live readiness · rules.",            icon: ShieldCheck,   keywords: ["standards", "readiness", "compliance", "rules"] },
      { to: "/admin/platform-readiness",       label: "Platform Readiness",     desc: "Reviews · evidence · blockers.",                          icon: ShieldCheck,   keywords: ["readiness", "review", "blockers", "evidence"] },
      { to: "/admin/platform-configuration",   label: "Platform Configuration", desc: "Branding · integrations · AI · version.",                icon: Cog,           keywords: ["configuration", "settings", "branding", "integrations", "version"] },
      { to: "/admin/diagnostics",              label: "Diagnostics",            desc: "System health · scheduler · database.",                   icon: Database,      keywords: ["diagnostics", "system", "health", "logs", "latency"] },
      { to: "/admin/maintenance",              label: "Maintenance",            desc: "Every safe operation grouped by domain.",                 icon: Archive,       keywords: ["maintenance", "cleanup", "history", "operations"] },
    ],
    hiddenRoutes: [
      { to: "/admin/platform-overview", label: "Platform Overview" },
      { to: "/admin/system", label: "System Recovery" },
    ],
  },

  // ────────────────────────────────────────────────────────────────
  // PLATFORM TOOLS · deep tools not covered by an Admin OS domain.
  {
    id: "platform-tools",
    label: "Platform Tools",
    subline: "Deep tools that support the domains above.",
    purpose:
      "Deep tools that support the Admin OS domains but do not " +
      "warrant a top-level domain of their own. Every action here " +
      "follows the review-changes-then-apply process.",
    stripe: "#dc2626",
    icon: Activity,
    visibleRoutes: [
      { to: "/admin/database",                   label: "Database Capacity",       desc: "Storage trend and capacity forecast.",                     icon: Database, keywords: ["mongo", "atlas", "capacity", "storage", "trend"] },
      { to: "/admin/mfa",                        label: "Multi-Factor Auth",       desc: "Super-admin MFA enrollment and recovery.",                icon: KeyRound, keywords: ["mfa", "totp", "2fa", "security", "auth"] },
      { to: "/admin/governance/self-protection", label: "Platform Self-Protection",desc: "Guardrails that keep the platform safe from itself.",     icon: ShieldAlert, keywords: ["governance", "guardrail", "safety", "protection"] },
      { to: "/admin/profile",                    label: "My Profile",              desc: "Account settings and preferences.",                       icon: Users, keywords: ["account", "settings", "password"] },
      { to: "/admin/guide",                      label: "Admin Guide",             desc: "Where things live and how to run them.",                  icon: BookOpen, keywords: ["help", "docs", "reference", "manual"] },
    ],
    hiddenRoutes: [],
  },

  // ────────────────────────────────────────────────────────────────
  // BUSINESS OPERATIONS · the operational areas the admin manages.
  // Not part of the Admin OS itself, but frequently accessed.
  {
    id: "business-operations",
    label: "Business Operations",
    subline: "Jobs · fleet · safety · people · training.",
    purpose:
      "The operational records the platform is built around. " +
      "Every business area is one click away.",
    stripe: "#2563eb",
    icon: Building2,
    visibleRoutes: [
      { to: "/admin/command-center",   label: "Command Center",       desc: "Cross-portal single-glass view.",                            icon: Activity, keywords: ["cross-portal", "single-glass", "cockpit"] },
      { to: "/admin/executive-overview", label: "Executive Overview", desc: "One-page executive summary.",                                icon: BarChart3, keywords: ["executive", "leadership", "summary"] },
      { to: "/admin/pnl",              label: "P&L",                   desc: "Profit-and-loss by job and division.",                       icon: BarChart3, keywords: ["profit", "loss", "financials", "pnl", "margin"] },
      { to: "/admin/jobs",             label: "Jobs & Projects",       desc: "Every active project · posters · banners.",                  icon: Building2, keywords: ["projects", "jobs", "master", "list"] },
      { to: "/admin/daily-reports",    label: "Daily Reports",         desc: "Cross-portal daily reports · evidence.",                     icon: FileText, keywords: ["daily", "reports", "dr", "evidence"] },
      { to: "/admin/equipment",        label: "Fleet & Equipment",     desc: "Assets · inspections · vendors · drivers.",                 icon: Wrench, keywords: ["equipment", "master", "assets", "fleet"] },
      { to: "/admin/dispatch",         label: "Dispatch",              desc: "Transfers · holds · equipment utilization.",                 icon: Truck, keywords: ["dispatch", "transfer", "hold", "utilization"] },
      { to: "/admin/transportation",   label: "Transportation",        desc: "Trucks · trailers · driver logs.",                           icon: Truck, keywords: ["transportation", "trucks", "trailers", "hauling"] },
      { to: "/admin/incidents",        label: "Safety & Compliance",   desc: "Incidents · JHAs · trench · findings.",                     icon: ShieldAlert, keywords: ["safety", "incidents", "capa", "compliance", "jha"] },
      { to: "/admin/people",           label: "People & Access",       desc: "Employees · sessions · terminations.",                       icon: Users, keywords: ["people", "employees", "access", "master"] },
      { to: "/admin/training",         label: "Training",              desc: "Training resources · videos · forms.",                       icon: GraduationCap, keywords: ["training", "forms", "resources"] },
      { to: "/admin/audit-log",        label: "Activity History",      desc: "Every action · every change · saved.",                      icon: History, keywords: ["history", "log", "activity", "timeline"] },
      { to: "/admin/legacy-imports",   label: "Historical Records",    desc: "Reviewed imports from prior systems.",                       icon: Archive, keywords: ["imports", "historic", "migration"] },
      { to: "/admin/operational-language", label: "Operational Language", desc: "Shared glossary · EN + ES.",                              icon: BookOpen, keywords: ["language", "glossary", "spanish"] },
    ],
    hiddenRoutes: [
      { to: "/admin/daily/:id",                       label: "Daily Report · detail" },
      { to: "/admin/meetings/:id",                    label: "Meeting · detail" },
      { to: "/admin/qaqc/:id",                        label: "QA/QC · detail" },
      { to: "/admin/jobs/:projectNumber/team",        label: "Project Team · detail" },
      { to: "/admin/leadership/records/:id",          label: "Leadership Record · detail" },
      { to: "/admin/equipment/:id",                   label: "Equipment · detail" },
      { to: "/admin/equipment/:id/history",           label: "Equipment · history" },
      { to: "/admin/assets/:assetId",                 label: "Asset · detail" },
      { to: "/admin/employees/:id/history",           label: "Employee · history" },
      { to: "/admin/incidents/:id",                   label: "Incident · detail" },
      { to: "/admin/inspections/:id",                 label: "Inspection · detail" },
      { to: "/admin/asset-mapping",                   label: "Asset Mapping" },
      { to: "/admin/asset-admin",                     label: "Asset Administration" },
      { to: "/admin/asset-spine",                     label: "Asset Spine" },
      { to: "/admin/geofence-reconciliation",         label: "Geofence Reconciliation" },
      { to: "/admin/operational-inventory",           label: "Operational Inventory" },
      { to: "/admin/operational-intelligence",        label: "Operational Intelligence" },
      { to: "/admin/promo-assets",                    label: "Promo Assets" },
      { to: "/admin/analytics",                       label: "Usage Analytics" },
      { to: "/admin/integrations",                    label: "Integrations" },
      { to: "/admin/ai-configuration",                label: "AI Configuration" },
      { to: "/admin/digest-config",                   label: "Digest Schedule" },
      { to: "/admin/email",                           label: "Email & Routing" },
      { to: "/admin/sessions",                        label: "Sessions" },
      { to: "/admin/governance",                      label: "Standards Status" },
    ],
  },
];

// ── Helpers ─────────────────────────────────────────────────────────

export function findActiveDomainIdV3(pathname) {
  if (!pathname) return null;
  for (const d of DOMAINS_V3) {
    for (const r of d.visibleRoutes) {
      if (r.end ? pathname === r.to : pathname === r.to) return d.id;
    }
    for (const r of d.visibleRoutes) {
      if (!r.end && pathname.startsWith(r.to + "/")) return d.id;
    }
    for (const r of d.hiddenRoutes) {
      const base = r.to.split("/:")[0];
      if (base && pathname.startsWith(base)) return d.id;
    }
  }
  return null;
}

export function buildSearchIndex(localize = (value) => value) {
  const items = [];
  for (const domain of DOMAINS_V3) {
    for (const r of domain.visibleRoutes) {
      items.push({
        id: `nav:${r.to}`,
        kind: "page",
        domain: domain.id,
        domainLabel: localize(domain.label),
        stripe: domain.stripe,
        label: localize(r.label),
        description: r.desc ? localize(r.desc) : r.desc,
        route: r.to,
        keywords: r.keywords || [],
        hidden: false,
      });
    }
    for (const r of domain.hiddenRoutes) {
      items.push({
        id: `nav-hidden:${r.to}`,
        kind: "page",
        domain: domain.id,
        domainLabel: localize(domain.label),
        stripe: domain.stripe,
        label: localize(r.label),
        description: `${localize(domain.label)} · ${localize("detail page")}`,
        route: r.to,
        keywords: [],
        hidden: true,
      });
    }
  }
  return items;
}

export function listVisibleRoutesV3() {
  const out = [];
  for (const d of DOMAINS_V3) {
    for (const r of d.visibleRoutes) out.push(r.to);
  }
  return out;
}

export function listAllRoutesV3() {
  const out = [];
  for (const d of DOMAINS_V3) {
    for (const r of d.visibleRoutes) out.push(r.to);
    for (const r of d.hiddenRoutes) out.push(r.to);
  }
  return out;
}
