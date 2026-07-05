// Phase IV.A.1 — Admin Sidebar V2 domain map
//
// Derived from /app/memory/ADMIN_INFORMATION_PRIORITY_MAP.json but using ONLY
// routes that exist in the current SECTIONS list of AdminShell.jsx. No new
// routes are introduced this phase; this is a pure visual re-grouping.
//
// Each domain follows the SIDEBAR_REARCHITECTURE.md two-tier shape:
//   - Tier 1 · domain row (always visible)
//   - Tier 2 · child entries (revealed when expanded)
//
// Stripes and ordering follow the operator's daily rhythm rule
// (operations first, system & governance last) from ADMIN_UX_GOVERNANCE.md §III.

import {
  Activity, Users, Wrench, Mail, ClipboardCheck, Shield,
  Building2, Truck, BookOpen, GraduationCap, History, Database,
  ListChecks, ChartBar, Cable, Film, Map, NotebookPen, ListTodo,
  AlertTriangle, KeyRound, FileText, Sparkles,
} from "lucide-react";

export const DOMAINS_V2 = [
  {
    id: "operations",
    label: "Operations",
    subline: "Field activity across all active projects.",
    stripe: "#dc2626", // red-600
    icon: Activity,
    routes: [
      { to: "/admin",                   label: "Overview",            desc: "KPIs, search, snapshot",                     icon: Activity, end: true },
      { to: "/admin/command-center",    label: "Command Center",      desc: "Executive single-glass · cross-portal.",     icon: Activity },
      { to: "/admin/jobs",              label: "Jobs & Field",        desc: "Job master · posters · banners",             icon: Building2 },
      { to: "/admin/operations-events", label: "Operations Events",   desc: "Append-only operational record",             icon: Activity },
      { to: "/admin/daily-reports",     label: "Daily Reports",       desc: "Cross-portal daily reports · admin view.",  icon: FileText },
      { to: "/odr/center",              label: "Operational Daily Records", desc: "Field-day system of record · FLL-aware",      icon: NotebookPen },
      { to: "/operational-records",     label: "Operational Records", desc: "Cross-portal field-day records · Phase V.1", icon: NotebookPen },
      { to: "/operations-actions",      label: "Operations Actions",  desc: "Cross-portal operational tasks · owners",   icon: ListTodo },
      { to: "/admin/dispatch",          label: "Dispatch",            desc: "Transfers · holds · utilization",            icon: Truck },
      { to: "/project-health",          label: "Project Health",      desc: "Operational friction by job",                icon: Activity },
      { to: "/asset-transfers",         label: "Asset Transfers",     desc: "Equipment movement · receiving",             icon: Truck },
    ],
  },
  {
    id: "workforce",
    label: "Workforce",
    subline: "People, certifications, time-off, onboarding.",
    stripe: "#2563eb", // blue-600
    icon: Users,
    routes: [
      { to: "/admin/people",          label: "People & Access",       desc: "PM · Shop · HR · employee master",           icon: Users },
      { to: "/admin/asset-admin",     label: "Asset Admin Console",   desc: "Asset Administrators · governance.",        icon: KeyRound },
      { to: "/admin/training",        label: "Training & Forms",      desc: "Training resources · safety forms",          icon: BookOpen },
      { to: "/document-expirations",  label: "Document Expirations",  desc: "OSHA · TWIC · CDL · registrations",          icon: ClipboardCheck },
      { to: "/admin/sessions",        label: "Sessions",              desc: "Last 50 portal sessions · forensic",         icon: Activity },
    ],
  },
  {
    id: "equipment-fleet",
    label: "Equipment & Fleet",
    subline: "Asset lifecycle, maintenance, pre-op, suppliers.",
    stripe: "#d97706", // amber-600
    icon: Wrench,
    routes: [
      { to: "/admin/equipment",              label: "Equipment & Suppliers", desc: "Status board · master · parts",        icon: Wrench },
      { to: "/admin/operational-inventory",  label: "Operational Inventory", desc: "Coverage matrix · drift detection",    icon: Map },
    ],
  },
  {
    id: "communications",
    label: "Communications",
    subline: "Email routing, notifications, escalation flow.",
    stripe: "#7c3aed", // violet-600
    icon: Mail,
    routes: [
      { to: "/admin/email",         label: "Email & Routing",   desc: "Auto-routing · distribution lists",                icon: Mail },
      { to: "/admin/digest-config", label: "Weekly Digest",     desc: "Recipients · schedule · preview · send",           icon: Mail },
    ],
  },
  {
    id: "safety-compliance",
    label: "Safety & Compliance",
    subline: "Incidents, audits, certifications, OSHA.",
    stripe: "#ea580c", // orange-600
    icon: ClipboardCheck,
    routes: [
      { to: "/admin/compliance",            label: "Compliance & Audits",  desc: "Exports · date audit",                  icon: ClipboardCheck },
      { to: "/admin/compliance-findings",   label: "Compliance Findings",  desc: "Open governance findings · severity",   icon: AlertTriangle },
      { to: "/admin/incidents",             label: "Incidents",            desc: "Safety incidents · admin review.",      icon: AlertTriangle },
      { to: "/admin/inspections",           label: "Site Inspections",     desc: "Job-site safety inspections.",          icon: ClipboardCheck },
      { to: "/admin/governance",            label: "Governance Health",    desc: "Cross-portal contradictions · score",   icon: Shield },
      { to: "/admin/project-identity",      label: "Project Identity Governance", desc: "Detect drift · project numbers/names.", icon: Shield },
      { to: "/admin/operational-language",  label: "Operational Language", desc: "Shared glossary · EN + ES",             icon: BookOpen },
    ],
  },
  {
    id: "system-governance",
    label: "System & Governance",
    subline: "Storage, backups, deploy health, observability.",
    stripe: "#475569", // slate-600
    icon: Shield,
    routes: [
      { to: "/admin/system",            label: "System & Backups",   desc: "Backups · R2 · restore · recovery",            icon: Shield },
      { to: "/admin/ai-configuration",  label: "AI Configuration",   desc: "Optional intelligence · tenant switchboard",  icon: Sparkles },
      { to: "/admin/system-health",     label: "System Health",      desc: "Green/yellow/red operational probe",           icon: Activity },
      { to: "/admin/database",          label: "Database",           desc: "Atlas capacity · 30-day storage trend",        icon: Database },
      { to: "/admin/audit-log",         label: "Audit Log",          desc: "Unified merged timeline",                      icon: History },
      { to: "/admin/deploy-readiness",  label: "Deploy Readiness",   desc: "Pre-deploy QA · gates",                        icon: ListChecks },
      { to: "/admin/deploy-recovery",   label: "Deploy Recovery",    desc: "Rollback playbook · backup chain",             icon: Shield },
      { to: "/admin/analytics",         label: "Usage Analytics",    desc: "Routes · portals · friction",                  icon: ChartBar },
      { to: "/admin/integrations",      label: "Integrations",       desc: "Motive · MaintainX · CSV",                     icon: Cable },
      { to: "/admin/promo-assets",      label: "Promo Assets",       desc: "Cinematic clips · hero loops",                 icon: Film },
    ],
  },
];

export const FOOTER_RAIL_V2 = [
  { to: "/tasks",        label: "My Tasks",     desc: "Action items across all domains",  icon: ClipboardCheck },
  { to: "/po-requests",  label: "PO Requests",  desc: "Field POs · approvals · receipts", icon: ClipboardCheck },
  { to: "/guidance",     label: "Guidance",     desc: "Doctrine · SOPs · training",       icon: GraduationCap },
];

// Returns the domain id whose routes contain the given pathname, or null.
// Used to auto-expand the active domain on first render.
export function findActiveDomainId(pathname) {
  if (!pathname) return null;
  const exact = DOMAINS_V2.find((d) =>
    d.routes.some((r) => (r.end ? pathname === r.to : pathname.startsWith(r.to)))
  );
  return exact ? exact.id : null;
}
