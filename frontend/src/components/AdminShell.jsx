// AdminShell.jsx — TRACK 25C · Pre-Deployment Certification.
//
// This wrapper used to render a competing red top-bar + its own
// left-side sidebar. That created a nested / duplicate persistent
// sidebar every time an operator opened a Business-Operations detail
// page (Jobs, Fleet, Dispatch, Compliance, …). The certification
// contract requires ONE persistent Admin OS shell and ONE persistent
// sidebar (SideNavV3). So AdminShell now delegates entirely to
// `LegacyAdminModernShell` (which composes PortalShell + SideNavV3 +
// AdminBreadcrumb). Every page that already imports AdminShell keeps
// working — the props are unchanged — but the chrome is now the
// modern Admin OS chrome.
//
// Backwards-compatible props (all existing callers keep working):
//   - title      → passed through as the page title
//   - section    → mapped to a breadcrumb parent
//   - intro      → rendered above `children`, inside the content well
//   - kicker     → currently ignored (was a small eyebrow label,
//                  replaced by the modern subtitle)
//   - active     → alias of `section`; ignored downstream
//
// The `SECTIONS` named export is preserved because a few call sites
// import it for their own nav rendering.

import React from "react";
import LegacyAdminModernShell from "@/components/admin/LegacyAdminModernShell";
import {
  LayoutDashboard, Users, Building2, Wrench, Mail, BookOpen, ClipboardCheck,
  ShieldCheck, Cable, Truck, Activity, Rocket, History, GraduationCap,
  ListChecks, ChartBar, Map, Film, Database, NotebookPen, ListTodo, Sparkles, KeyRound,
} from "lucide-react";

// Retained for legacy imports (a couple of pages still import SECTIONS).
// New code should use `/app/frontend/src/app/admin/domainMapV3.js` instead.
export const SECTIONS = [
  { key: "overview",   to: "/admin",            icon: LayoutDashboard, label: "Overview",     desc: "KPIs, search, snapshot" },
  { key: "command-center", to: "/admin/command-center", icon: Activity, label: "Command Center", desc: "Executive single-glass" },
  { key: "people",     to: "/admin/people",     icon: Users,           label: "People & Access", desc: "Employees & directory" },
  { key: "jobs",       to: "/admin/jobs",       icon: Building2,       label: "Jobs & Field",    desc: "Job master · posters · banners" },
  { key: "equipment",  to: "/admin/equipment",  icon: Wrench,          label: "Equipment & Suppliers", desc: "Assets · inspections" },
  { key: "asset-admin", to: "/admin/asset-admin", icon: ShieldCheck,   label: "Asset Administration", desc: "Taxonomy · review queue" },
  { key: "email",      to: "/admin/email",      icon: Mail,            label: "Email & Routing", desc: "Auto-routing · lists" },
  { key: "training",   to: "/admin/training",   icon: BookOpen,        label: "Training & Forms",desc: "Training resources · safety forms" },
  { key: "compliance", to: "/admin/compliance", icon: ClipboardCheck,  label: "Compliance & Audits", desc: "Exports · date audit" },
  { key: "dispatch",   to: "/admin/dispatch",   icon: Truck,           label: "Transportation Ops", desc: "Transfers · holds · utilization" },
  { key: "events",     to: "/admin/operations-events", icon: Activity, label: "Operations Events", desc: "Append-only log" },
  { key: "integrations", to: "/admin/integrations", icon: Cable,       label: "Integrations",    desc: "Motive · MaintainX" },
  { key: "operations-control", to: "/admin/operations-control", icon: Activity, label: "Operations Control Center", desc: "Unified maintenance" },
  { key: "system",     to: "/admin/system",     icon: ShieldCheck,     label: "System & Backups",desc: "Backups · R2 · restore" },
  { key: "ai-configuration", to: "/admin/ai-configuration", icon: Sparkles, label: "AI Configuration", desc: "Tenant AI switchboard" },
  { key: "system-health", to: "/admin/system-health", icon: Activity,  label: "System Health",   desc: "Operational probe" },
  { key: "database", to: "/admin/database", icon: Database, label: "Database Capacity", desc: "Atlas capacity trend" },
  { key: "digest-config", to: "/admin/digest-config", icon: Mail,      label: "Digest Schedule", desc: "Recipients · preview · send" },
  { key: "audit-log",  to: "/admin/audit-log",  icon: History,         label: "Audit Log",       desc: "Unified timeline" },
  { key: "sessions",   to: "/admin/sessions",   icon: Activity,        label: "Sessions",        desc: "Forensic view" },
  { key: "deploy-recovery", to: "/admin/deploy-recovery", icon: Rocket, label: "Deploy Recovery", desc: "Rollback playbook" },
  { key: "deploy-readiness", to: "/admin/deploy-readiness", icon: ListChecks, label: "Deploy Readiness", desc: "Pre-deploy QA" },
  { key: "analytics", to: "/admin/analytics", icon: ChartBar, label: "Usage Analytics", desc: "Operational insight" },
  { key: "operational-inventory", to: "/admin/operational-inventory", icon: Map, label: "Operational Inventory", desc: "Governance coverage" },
  { key: "governance", to: "/admin/governance", icon: ShieldCheck, label: "Governance Health", desc: "Cross-portal contradictions" },
  { key: "operational-language", to: "/admin/operational-language", icon: BookOpen, label: "Operational Language", desc: "Shared glossary" },
  { key: "promo-assets", to: "/admin/promo-assets", icon: Film, label: "Promo Assets", desc: "Cinematic library" },
  { key: "master-history", to: "/admin/master-history", icon: History, label: "Master History", desc: "Immutable snapshots" },
];

// Map a legacy `section` prop → modern breadcrumb parent so operator
// context ("where am I?") is always answered. Any section not listed
// here is silently omitted — the breadcrumb still shows "Admin OS ›
// <title>" which is honest and unambiguous.
const SECTION_TO_DOMAIN = {
  people:              { label: "Identity & Security",    to: "/admin/identity-security" },
  jobs:                { label: "Business Operations" },
  equipment:           { label: "Business Operations" },
  dispatch:            { label: "Business Operations" },
  compliance:          { label: "Business Operations" },
  training:            { label: "Business Operations" },
  "asset-admin":       { label: "Business Operations" },
  email:               { label: "Communications",         to: "/admin/communications" },
  system:              { label: "Storage & Recovery",     to: "/admin/storage-recovery" },
  database:            { label: "Diagnostics",            to: "/admin/diagnostics" },
  "system-health":     { label: "Diagnostics",            to: "/admin/diagnostics" },
  analytics:           { label: "Diagnostics",            to: "/admin/diagnostics" },
  governance:          { label: "Governance & Trust",     to: "/admin/governance-trust" },
  "audit-log":         { label: "Governance & Trust",     to: "/admin/governance-trust" },
  "deploy-recovery":   { label: "Governance & Trust",     to: "/admin/governance-trust" },
  "deploy-readiness":  { label: "Governance & Trust",     to: "/admin/governance-trust" },
  "ai-configuration":  { label: "AI Operations",          to: "/admin/ai-operations" },
  integrations:        { label: "Platform Configuration", to: "/admin/platform-configuration" },
  "operations-control":{ label: "Operations Control",     to: "/admin/operations-control" },
  events:              { label: "Diagnostics",            to: "/admin/diagnostics" },
  "digest-config":     { label: "Communications",         to: "/admin/communications" },
  "master-history":    { label: "Maintenance",            to: "/admin/maintenance" },
  "operational-language":{ label: "Governance & Trust",   to: "/admin/governance-trust" },
  "operational-inventory":{ label: "Diagnostics",         to: "/admin/diagnostics" },
  "promo-assets":      { label: "Business Operations" },
};

export default function AdminShell({
  title,
  section,
  active,          // deprecated alias
  children,
  intro,
  kicker,          // ignored — replaced by modern subtitle
  ...rest
}) {
  const key = section || active;
  const parent = key ? SECTION_TO_DOMAIN[key] : null;
  const breadcrumb = parent
    ? [parent, { label: title || "" }]
    : [{ label: title || "" }];

  return (
    <LegacyAdminModernShell
      title={title}
      subtitle={typeof kicker === "string" ? kicker : null}
      breadcrumb={breadcrumb}
      testidPrefix={`admin-shell${key ? "-" + key : ""}`}
      {...rest}
    >
      {intro && (
        <div className="mb-5 rounded-lg border border-slate-200 bg-white p-4">
          {intro}
        </div>
      )}
      {children}
    </LegacyAdminModernShell>
  );
}
