// TRACK 25.02 · Admin Operating System — Phase D · Domain Map V3.
//
// The approved 12-domain rebuild of the admin nav. Rendered by
// `components/admin/sidebar/SideNavV3.jsx` and consumed by the
// `components/admin/CommandPalette.jsx` universal search.
//
// Governed by `masci.admin.nav.v3` feature flag — defaults OFF. The
// legacy 6-domain SideNavV2 remains the default until certified.
//
// Contract:
//   - `visibleRoutes`   → shown in the sidebar tree
//   - `hiddenRoutes`    → detail pages / dynamic segments; still
//                         indexed by the command palette so nothing
//                         becomes unreachable-via-search.
//   - `keywords`        → extra search tokens beyond label+desc so
//                         operators can find pages by intent rather
//                         than by internal route name.
//   - `purpose`         → the domain's one-line business reason
//                         (shown in the sidebar + as palette group).
//
// Zero-drift rule: this map ONLY lists routes that already exist
// in AppRoutes.jsx. Adding a nav entry never invents a new page.
//
// Legacy consolidation: routes redirected via LegacyMovedBanner
// (see `app/routing/legacyRedirects.js`) are NOT listed here — the
// canonical destination (OCC) is listed instead. Old URLs still
// resolve and render their original page with the banner on top.

import {
  Home,          // Home
  Activity,      // OCC / operations
  Building2,     // Jobs & Projects
  Wrench,        // Fleet & Equipment
  ShieldAlert,   // Safety & Compliance
  Users,         // People & Access
  GraduationCap, // Training
  Sparkles,      // AI & Intelligence
  Mail,          // Communications
  BarChart3,     // Reporting
  History,       // Audit Log
  Archive,       // Legacy Imports
  // Admin OS domain icons
  HardDrive,     // Storage & Recovery
  ShieldCheck,   // Governance & Trust
  Cog,           // Platform Configuration
  Database,      // Diagnostics
  Compass,       // Admin OS root
  // sub-icons
  ClipboardCheck, FileText, Truck, MapPin, KeyRound, AlertTriangle,
  BookOpen, Film, Cable, ListChecks, NotebookPen,
} from "lucide-react";

export const DOMAINS_V3 = [
  // ────────────────────────────────────────────────────────────────
  // TRACK 25 · SPRINT 7/8 · Admin OS one-click reachability section.
  // Every one of the 10 canonical Admin OS domain landings is
  // reachable from the sidebar with a single click. Sits at the top
  // of the nav so operators land on the trusted, unified surface
  // instead of scattered legacy admin pages.
  {
    id: "admin-os",
    label: "Admin OS",
    subline: "The 10 canonical operational domains.",
    purpose:
      "Every Admin OS domain landing is one click away. Read-only " +
      "trust cards on the left · dry-run maintenance in OCC on the right.",
    stripe: "#0ea5e9", // sky-500 — signals the unified Admin OS surface
    icon: Compass,
    visibleRoutes: [
      { to: "/admin",                          label: "Admin OS Landing",       desc: "10-domain executive posture · live probes.",             end: true, icon: Compass,       keywords: ["adminos", "landing", "overview", "posture", "domains", "hub"] },
      { to: "/admin/operations-control",       label: "Operations Control",     desc: "OCC Trust Center + maintenance console.",                icon: Activity,      keywords: ["occ", "operations", "control", "trust", "maintenance", "dry-run", "apply"] },
      { to: "/admin/storage-recovery",         label: "Storage & Recovery",     desc: "Disk · R2 · backups · restore drills.",                  icon: HardDrive,     keywords: ["storage", "backup", "r2", "recovery", "restore", "disk"] },
      { to: "/admin/ai-operations",            label: "AI Operations",          desc: "Gateway · providers · modules · Daily Report AI.",       icon: Sparkles,      keywords: ["ai", "gateway", "provider", "openai", "anthropic", "gemini", "daily report ai"] },
      { to: "/admin/communications",           label: "Communications",         desc: "Email routing · providers · audit · dead-letters.",       icon: Mail,          keywords: ["email", "resend", "notifications", "routing", "digest", "communications"] },
      { to: "/admin/identity-security",        label: "Identity & Security",    desc: "Sessions · hardening · audit · self-protection.",         icon: Users,         keywords: ["sessions", "auth", "mfa", "passkeys", "security", "hardening"] },
      { to: "/admin/governance-trust",         label: "Governance & Trust",     desc: "Production cert · deploy readiness · governance rules.", icon: ShieldCheck,   keywords: ["governance", "trust", "certification", "deploy", "readiness", "compliance"] },
      { to: "/admin/platform-configuration",   label: "Platform Configuration", desc: "Brand · integrations · AI config · email · version.",   icon: Cog,           keywords: ["configuration", "settings", "branding", "integrations", "version", "feature flags"] },
      { to: "/admin/diagnostics",              label: "Diagnostics",            desc: "API · system health · OCC · scheduler · deploy.",         icon: Database,      keywords: ["diagnostics", "system", "health", "logs", "latency", "sentry", "errors"] },
      { to: "/admin/maintenance",              label: "Maintenance",            desc: "Every safe operation grouped by domain.",                 icon: Archive,       keywords: ["maintenance", "cleanup", "audit", "safe operations"] },
    ],
    hiddenRoutes: [
      { to: "/admin/platform-overview", label: "Platform Overview (redirects)" },
    ],
  },

  // ────────────────────────────────────────────────────────────────
  {
    id: "home",
    label: "Home",
    subline: "What needs attention now.",
    purpose:
      "Executive landing. The one page an operator opens first to see " +
      "the day's priorities across every portal.",
    stripe: "#0f172a", // slate-900 for calm authority
    icon: Home,
    visibleRoutes: [
      { to: "/admin",                   label: "Executive Home",       desc: "Today's attention queue · cross-portal signals.", end: true, icon: Home, keywords: ["landing", "overview", "today", "priorities", "attention"] },
      { to: "/admin/command-center",    label: "Command Center",       desc: "Single-glass across dispatch · safety · jobs · fleet.",  icon: Activity, keywords: ["cross-portal", "single-glass", "cockpit"] },
      { to: "/admin/executive-overview",label: "Executive Overview",   desc: "One-page executive summary of the platform.",              icon: BarChart3, keywords: ["executive", "leadership", "summary"] },
      { to: "/admin/pnl",               label: "P&L",                  desc: "Profit-and-loss snapshot by job and division.",           icon: BarChart3, keywords: ["profit", "loss", "financials", "pnl", "margin"] },
      { to: "/admin/profile",           label: "My Profile",           desc: "Account settings and preferences.",                       icon: Users, keywords: ["account", "settings", "password"] },
      { to: "/admin/guide",             label: "Admin Guide",          desc: "Where things live and how to run them.",                  icon: BookOpen, keywords: ["help", "docs", "reference", "manual"] },
    ],
    hiddenRoutes: [],
  },

  // ────────────────────────────────────────────────────────────────
  // TRACK 25B · Platform Tools — deep tools not directly exposed as
  // a top-level Admin OS domain. Never duplicates the Admin OS
  // section above; the duplicate 'Operations Console' link has been
  // removed (OCC is one-click reachable via `Admin OS → Operations
  // Control`). This section only carries capabilities that would
  // otherwise be orphaned in the nav.
  {
    id: "platform-tools",
    label: "Platform Tools",
    subline: "Deep tools — database · MFA · self-protection.",
    purpose:
      "Deep-tool routes that support the Admin OS domains but do " +
      "not warrant a top-level domain of their own. Every action " +
      "here is read-only or governed by the OCC dry-run/apply " +
      "contract.",
    stripe: "#dc2626",
    icon: Activity,
    visibleRoutes: [
      { to: "/admin/database",           label: "Database Capacity",  desc: "Mongo storage trend and capacity forecast.",           icon: Activity, keywords: ["mongo", "atlas", "capacity", "storage", "trend"] },
      { to: "/admin/mfa",                label: "Multi-Factor Auth",  desc: "Super-admin MFA enrollment and recovery.",             icon: KeyRound, keywords: ["mfa", "totp", "2fa", "security", "auth"] },
      { to: "/admin/governance/self-protection", label: "Platform Self-Protection", desc: "Guardrails that prevent the platform from harming itself.", icon: ShieldAlert, keywords: ["governance", "guardrail", "safety", "protection"] },
    ],
    hiddenRoutes: [],
  },

  // ────────────────────────────────────────────────────────────────
  {
    id: "jobs-projects",
    label: "Jobs & Projects",
    subline: "Every active job · daily reports · meetings · QA/QC.",
    purpose:
      "The operational record for every job. Daily reports, meetings, " +
      "site QA/QC, staffing, and daily-leadership shifts.",
    stripe: "#2563eb", // blue-600
    icon: Building2,
    visibleRoutes: [
      { to: "/admin/jobs",              label: "Jobs Master",         desc: "Every active project · posters · banners.",            icon: Building2, keywords: ["projects", "jobs", "master", "list"] },
      { to: "/admin/project-identity",  label: "Project Identity",    desc: "Detect drift in project numbers or names.",             icon: ShieldAlert, keywords: ["identity", "drift", "project number"] },
      { to: "/admin/project-staffing",  label: "Project Staffing",    desc: "Cross-project team roster · 17 roles.",                 icon: Users, keywords: ["staffing", "roster", "team", "assignments"] },
      { to: "/admin/daily-reports",     label: "Daily Reports",       desc: "Cross-portal daily reports · evidence · exports.",      icon: FileText, keywords: ["daily", "reports", "dr", "evidence", "safety walk"] },
      { to: "/admin/meetings",          label: "Meetings",            desc: "Preconstruction · progress · closeout meetings.",       icon: NotebookPen, keywords: ["meetings", "preconstruction", "progress"] },
      { to: "/admin/qaqc",              label: "QA / QC",             desc: "Site quality control records.",                          icon: ClipboardCheck, keywords: ["qa", "qc", "quality", "inspection"] },
      { to: "/admin/photos",            label: "Job Photos",          desc: "Photo evidence across every project.",                   icon: FileText, keywords: ["photos", "images", "evidence"] },
      { to: "/admin/dispatch",          label: "Dispatch",            desc: "Transfers · holds · equipment utilization.",             icon: Truck, keywords: ["dispatch", "transfer", "hold", "utilization"] },
      { to: "/admin/dls/day-1-debrief", label: "Day-1 Debrief",       desc: "Daily Leadership Sessions · day-1 debrief.",             icon: NotebookPen, keywords: ["dls", "day 1", "debrief", "leadership"] },
      { to: "/admin/dls/week-1-debrief",label: "Week-1 Debrief",      desc: "Daily Leadership Sessions · week-1 debrief.",            icon: NotebookPen, keywords: ["dls", "week 1", "debrief", "leadership"] },
      { to: "/admin/dls/shift-qr",      label: "DLS Shift QR",        desc: "Field QR poster for shift check-ins.",                   icon: FileText, keywords: ["dls", "qr", "shift", "poster"] },
      { to: "/admin/posters/print-all", label: "Print All Posters",   desc: "One-page print of every field poster.",                  icon: FileText, keywords: ["posters", "print", "field"] },
      { to: "/admin/operations-events", label: "Operations Events",   desc: "Append-only operational record.",                        icon: History, keywords: ["events", "operations log"] },
    ],
    hiddenRoutes: [
      { to: "/admin/daily/:id",                       label: "Daily Report · detail" },
      { to: "/admin/meetings/:id",                    label: "Meeting · detail" },
      { to: "/admin/qaqc/:id",                        label: "QA/QC · detail" },
      { to: "/admin/jobs/:projectNumber/team",        label: "Project Team · detail" },
      { to: "/admin/leadership/records/:id",          label: "Leadership Record · detail" },
    ],
  },

  // ────────────────────────────────────────────────────────────────
  {
    id: "fleet-equipment",
    label: "Fleet & Equipment",
    subline: "Assets · maintenance · geofences · vendors · drivers.",
    purpose:
      "The asset lifecycle — from onboarding through inspection, " +
      "transfer, and retirement. Includes drivers, vendors, geofences.",
    stripe: "#d97706", // amber-600
    icon: Wrench,
    visibleRoutes: [
      { to: "/admin/equipment",              label: "Equipment Master",    desc: "Every asset · status · parts · suppliers.",          icon: Wrench, keywords: ["equipment", "master", "assets", "parts"] },
      { to: "/admin/equipment-inspections",  label: "Equipment Inspections", desc: "Pre-op inspections · issues · escalations.",        icon: ClipboardCheck, keywords: ["preop", "pre-op", "inspection", "equipment check"] },
      { to: "/admin/leadership-equipment",   label: "Leadership Equipment",desc: "Field leadership assigned equipment.",                icon: Wrench, keywords: ["leadership", "equipment", "assigned"] },
      { to: "/admin/transportation",         label: "Transportation",      desc: "Trucks · trailers · driver logs.",                    icon: Truck, keywords: ["transportation", "trucks", "trailers", "hauling"] },
      { to: "/admin/asset-admin",            label: "Asset Administration",desc: "Asset Administrators · governance.",                  icon: KeyRound, keywords: ["asset admin", "governance", "administrators"] },
      { to: "/admin/asset-mapping",          label: "Asset Mapping",       desc: "Motive ↔ MASCI equipment mapping.",                    icon: MapPin, keywords: ["mapping", "motive", "reconcile"] },
      { to: "/admin/asset-spine",            label: "Asset Spine",         desc: "Master asset spine · conflict resolution.",            icon: KeyRound, keywords: ["spine", "master", "conflicts"] },
      { to: "/admin/geofence-reconciliation",label: "Geofence Reconciliation", desc: "Approve · reject · reassign Motive geofences.",  icon: MapPin, keywords: ["geofence", "motive", "reconciliation", "gps"] },
      { to: "/admin/operational-inventory",  label: "Operational Inventory", desc: "Coverage matrix · drift detection.",                 icon: MapPin, keywords: ["inventory", "coverage", "drift"] },
    ],
    hiddenRoutes: [
      { to: "/admin/equipment/:id",           label: "Equipment · detail" },
      { to: "/admin/equipment/:id/history",   label: "Equipment · history" },
      { to: "/admin/assets/:assetId",         label: "Asset · detail" },
      { to: "/admin/assets/:assetRef/thread", label: "Asset · comment thread" },
      { to: "/admin/vendors/:vendorId/thread",label: "Vendor · thread" },
      { to: "/admin/driver-intel/:driverKey", label: "Driver · intelligence" },
    ],
  },

  // ────────────────────────────────────────────────────────────────
  {
    id: "safety-compliance",
    label: "Safety & Compliance",
    subline: "Incidents · JHAs · trench · site inspections · findings.",
    purpose:
      "Everything that keeps crews safe and the company OSHA-compliant.",
    stripe: "#ea580c", // orange-600
    icon: ShieldAlert,
    visibleRoutes: [
      { to: "/admin/incidents",             label: "Incidents",              desc: "Safety incidents · CAPAs · admin review.",         icon: AlertTriangle, keywords: ["incidents", "safety", "capa", "corrective"] },
      { to: "/admin/inspections",           label: "Site Inspections",       desc: "Job-site safety inspections.",                       icon: ClipboardCheck, keywords: ["inspection", "site", "walk"] },
      { to: "/admin/jha",                   label: "JHAs",                   desc: "Job Hazard Analyses across every crew.",             icon: ClipboardCheck, keywords: ["jha", "hazard", "analysis"] },
      { to: "/admin/jha-plans",             label: "JHA Plans",              desc: "Reusable JHA plan library.",                          icon: ClipboardCheck, keywords: ["jha plans", "library", "hazard plans"] },
      { to: "/admin/jha-plans/poster",      label: "JHA Plans Poster",       desc: "Poster export for the JHA plan library.",             icon: FileText, keywords: ["jha", "poster", "print"] },
      { to: "/admin/jha-acknowledgements",  label: "JHA Acknowledgements",   desc: "Crew acknowledgements · signatures.",                 icon: ClipboardCheck, keywords: ["jha", "acknowledge", "signatures"] },
      { to: "/admin/trench-safety",         label: "Trench Safety",          desc: "Trench safety program overview.",                     icon: ShieldAlert, keywords: ["trench", "safety", "excavation"] },
      { to: "/admin/trench-boxes",          label: "Trench Boxes",           desc: "Box inventory · certifications · assignments.",       icon: ShieldAlert, keywords: ["trench boxes", "shielding"] },
      { to: "/admin/trench-boxes/poster",   label: "Trench Boxes Poster",    desc: "Poster export for the trench box library.",           icon: FileText, keywords: ["trench boxes", "poster", "print"] },
      { to: "/admin/compliance",            label: "Compliance & Audits",    desc: "Compliance exports · date audits.",                   icon: ClipboardCheck, keywords: ["compliance", "audit", "export"] },
      { to: "/admin/compliance-findings",   label: "Compliance Findings",    desc: "Open governance findings · severity.",                icon: AlertTriangle, keywords: ["findings", "governance", "compliance"] },
      { to: "/admin/material-ledger-quality", label: "Material Ledger Quality", desc: "Missing-proof queue · haul cycles · CSV export.",  icon: ClipboardCheck, keywords: ["material", "ledger", "haul", "tickets"] },
      { to: "/admin/governance",            label: "Governance Health",      desc: "Cross-portal contradictions · score.",                icon: ShieldAlert, keywords: ["governance", "contradictions", "health"] },
    ],
    hiddenRoutes: [
      { to: "/admin/incidents/:id",                          label: "Incident · detail" },
      { to: "/admin/inspections/:id",                        label: "Inspection · detail" },
      { to: "/admin/jha/:id",                                label: "JHA · detail" },
      { to: "/admin/trench-safety-assets",                   label: "Trench safety assets" },
      { to: "/admin/trench-safety/assets",                   label: "Trench safety · assets" },
      { to: "/admin/trench-safety/assets/:assetId",          label: "Trench safety · asset detail" },
      { to: "/admin/trench-safety/excavations",              label: "Trench safety · excavations" },
      { to: "/admin/trench-safety/field-reports",            label: "Trench safety · field reports" },
      { to: "/admin/trench-safety/repair-review",            label: "Trench safety · repair review" },
      { to: "/admin/trench-safety/reports",                  label: "Trench safety · reports" },
      { to: "/admin/trench-safety/tabulated-data",           label: "Trench safety · tabulated data" },
      { to: "/admin/safety/issuance/:id",                    label: "Safety issuance · detail" },
      { to: "/admin/safety/training/:id",                    label: "Safety training · detail" },
    ],
  },

  // ────────────────────────────────────────────────────────────────
  {
    id: "people-access",
    label: "People & Access",
    subline: "Employees · sessions · terminations · language.",
    purpose:
      "Who works here, who can access what, and how the platform " +
      "speaks to them.",
    stripe: "#0891b2", // cyan-600
    icon: Users,
    visibleRoutes: [
      { to: "/admin/people",                        label: "People & Access",      desc: "PM · Shop · HR · employee master.",          icon: Users, keywords: ["people", "employees", "access", "master"] },
      { to: "/admin/sessions",                      label: "Sessions",             desc: "Last 50 portal sessions · forensic view.",    icon: History, keywords: ["sessions", "audit", "login", "forensic"] },
      { to: "/admin/terminations",                  label: "Terminations",         desc: "Off-boarding queue · access revocation.",     icon: Users, keywords: ["terminations", "offboarding", "revoke"] },
      { to: "/admin/preview-validation-identities", label: "Preview Identities",   desc: "Preview-only test users for validation.",     icon: Users, keywords: ["preview", "test users", "validation"] },
      { to: "/admin/guidance-coverage",             label: "Guidance Coverage",    desc: "Which crews have been trained on which SOPs.",icon: ClipboardCheck, keywords: ["guidance", "coverage", "sop", "training"] },
      { to: "/admin/operational-language",          label: "Operational Language", desc: "Shared glossary · EN + ES.",                   icon: BookOpen, keywords: ["language", "glossary", "spanish", "translation"] },
    ],
    hiddenRoutes: [
      { to: "/admin/employees/:id/history", label: "Employee · history" },
    ],
  },

  // ────────────────────────────────────────────────────────────────
  {
    id: "training",
    label: "Training",
    subline: "Training resources · videos · forms.",
    purpose:
      "The library of training materials the field uses every day.",
    stripe: "#059669", // emerald-600
    icon: GraduationCap,
    visibleRoutes: [
      { to: "/admin/training",        label: "Training & Forms",     desc: "Training resources · safety forms library.",       icon: GraduationCap, keywords: ["training", "forms", "resources"] },
      { to: "/admin/training-videos", label: "Training Videos",      desc: "Video library · assignments · watch counts.",      icon: Film, keywords: ["training", "videos", "library"] },
    ],
    hiddenRoutes: [],
  },

  // ────────────────────────────────────────────────────────────────
  {
    id: "ai-intelligence",
    label: "AI & Intelligence",
    subline: "Operational intelligence · digests · AI configuration.",
    purpose:
      "The AI-driven insights the platform generates and the switches " +
      "that control them.",
    stripe: "#7c3aed", // violet-600
    icon: Sparkles,
    visibleRoutes: [
      { to: "/admin/ai-configuration",                   label: "AI Configuration",       desc: "Optional intelligence · tenant switchboard.",         icon: Sparkles, keywords: ["ai", "gpt", "claude", "configuration"] },
      { to: "/admin/operational-intelligence",           label: "Operational Intelligence", desc: "Cross-portal AI briefs · digests.",                   icon: Sparkles, keywords: ["oi", "intelligence", "briefs", "digest"] },
      { to: "/admin/operational-intelligence/recipients",label: "OI Recipients",           desc: "Who receives which intelligence brief.",              icon: Mail, keywords: ["oi", "recipients", "briefs"] },
      { to: "/admin/ods-intelligence",                   label: "ODS Intelligence",        desc: "Operational Daily System AI signals.",                icon: Sparkles, keywords: ["ods", "intelligence", "daily"] },
    ],
    hiddenRoutes: [],
  },

  // ────────────────────────────────────────────────────────────────
  {
    id: "communications",
    label: "Communications",
    subline: "Email · digests · integrations · promo assets.",
    purpose:
      "How the platform reaches the outside world — email routing, " +
      "digest scheduling, third-party feeds, and marketing assets.",
    stripe: "#0284c7", // sky-600
    icon: Mail,
    visibleRoutes: [
      { to: "/admin/email",         label: "Email & Routing",   desc: "Auto-routing · distribution lists · providers.",         icon: Mail, keywords: ["email", "routing", "distribution"] },
      { to: "/admin/digest-config", label: "Digest Schedule",   desc: "Weekly digest recipients · schedule · preview · send.",  icon: Mail, keywords: ["digest", "weekly", "schedule"] },
      { to: "/admin/integrations",  label: "Integrations",      desc: "Motive · MaintainX · CSV feeds.",                        icon: Cable, keywords: ["integrations", "motive", "maintainx", "csv"] },
      { to: "/admin/promo-assets",  label: "Promo Assets",      desc: "Cinematic clips · hero loops · public marketing.",        icon: Film, keywords: ["promo", "marketing", "hero", "clips"] },
    ],
    hiddenRoutes: [],
  },

  // ────────────────────────────────────────────────────────────────
  {
    id: "reporting",
    label: "Reporting",
    subline: "Analytics · P&L · executive · usage.",
    purpose:
      "Where numbers become insight. Analytics, executive summaries, " +
      "and P&L views.",
    stripe: "#4338ca", // indigo-700
    icon: BarChart3,
    visibleRoutes: [
      { to: "/admin/analytics",          label: "Usage Analytics",     desc: "Routes · portals · friction · adoption.",          icon: BarChart3, keywords: ["analytics", "usage", "routes", "adoption"] },
      { to: "/admin/executive-overview", label: "Executive Overview",  desc: "One-page executive summary of the platform.",       icon: BarChart3, keywords: ["executive", "leadership", "summary"] },
      { to: "/admin/pnl",                label: "P&L Reporting",       desc: "Profit-and-loss by job and division.",              icon: BarChart3, keywords: ["pnl", "profit", "loss", "financials"] },
    ],
    hiddenRoutes: [],
  },

  // ────────────────────────────────────────────────────────────────
  {
    id: "audit-log",
    label: "Audit Log",
    subline: "Every action · every change · every hour.",
    purpose:
      "The immutable, cross-system record of everything that happened.",
    stripe: "#334155", // slate-700
    icon: History,
    visibleRoutes: [
      { to: "/admin/audit-log", label: "Unified Audit Log", desc: "Cross-portal merged timeline of every action.", icon: History, keywords: ["audit", "log", "history", "timeline"] },
    ],
    hiddenRoutes: [],
  },

  // ────────────────────────────────────────────────────────────────
  {
    id: "legacy-imports",
    label: "Legacy Imports",
    subline: "Historic data brought in from prior systems.",
    purpose:
      "Where data imported from legacy systems is reviewed and " +
      "reconciled — kept separate so live operations aren't confused " +
      "with historic imports.",
    stripe: "#78716c", // stone-500
    icon: Archive,
    visibleRoutes: [
      { to: "/admin/legacy-imports", label: "Historical Imports", desc: "Reviewed imports from prior systems.", icon: Archive, keywords: ["imports", "historic", "legacy data", "migration"] },
    ],
    hiddenRoutes: [],
  },
];

// ── Helpers ─────────────────────────────────────────────────────────

export function findActiveDomainIdV3(pathname) {
  if (!pathname) return null;
  for (const d of DOMAINS_V3) {
    for (const r of d.visibleRoutes) {
      if (r.end ? pathname === r.to : pathname === r.to) return d.id;
    }
    // startsWith match (allow /admin/jobs to match /admin/jobs/123/team)
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

// Flat list of all searchable items for the Command Palette.
// Each item carries a stable id, a domain classification, and the
// route to navigate to (dynamic segments are replaced with a
// human-facing placeholder pattern the palette does not render).
export function buildSearchIndex() {
  const items = [];
  for (const domain of DOMAINS_V3) {
    for (const r of domain.visibleRoutes) {
      items.push({
        id: `nav:${r.to}`,
        kind: "page",
        domain: domain.id,
        domainLabel: domain.label,
        stripe: domain.stripe,
        label: r.label,
        description: r.desc,
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
        domainLabel: domain.label,
        stripe: domain.stripe,
        label: r.label,
        description: `${domain.label} · detail page`,
        route: r.to,
        keywords: [],
        hidden: true,
      });
    }
  }
  return items;
}

// Every visible route flattened — useful for tests that assert
// "every admin route is discoverable from the sidebar".
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
