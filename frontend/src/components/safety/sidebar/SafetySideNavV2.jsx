// Safety Portal · Sidebar V2 · iter437 / Phase IV-BETA.5A
//
// Mirrors HR Sidebar V2 discipline (HrSideNavV2.jsx). 4-domain layout
// driven by SAFETY_INFORMATION_PRIORITY_MAP.json.
//
// iter437 IV-BETA.5A-P6 · Safety Sidebar V2 is now the DEFAULT layout
// after a clean stabilization review (28 consecutive trendline records
// at calmness=72.41 / direction=stable / delta=0.0). The flag resolves
// cleanly so operators can opt out via `?safetySidebarV2=0` (or
// localStorage `masci.safety.sidebar.v2=0`, or env
// `REACT_APP_SAFETY_SIDEBAR_V2=0`) without redeploying. Legacy Safety
// chrome stays one keystroke away.
//
// Governance contracts honoured:
//   • OPERATIONAL_VERBIAGE_DOCTRINE.md §IV (no marketing slop)
//   • CROSS_PORTAL_COACHING_STANDARD.md §V (≤14-word coaching sublines)
//   • SAFETY_ESCALATION_HIERARCHY_MAP.md §VI (red ONLY for incidents domain)
//   • VISUAL_LOUDNESS_REDUCTION_PLAN.md §I (single stripe per domain)
//   • HR Sidebar V2 reference (frontend/src/components/hr/sidebar/HrSideNavV2.jsx)

import React from "react";
import { NavLink, useLocation } from "react-router-dom";
import {
  AlertOctagon, ClipboardCheck, ListChecks, Award, FolderArchive,
  Package, Users, FileText, Flame, Mail, BarChart3, ShieldAlert,
  BookOpen, Truck, GraduationCap, NotebookPen,
} from "lucide-react";

// Domain groups · ordered by escalation severity (highest first).
// `stripe` colour communicates the domain; red is the ONE incidents domain.
export const SAFETY_DOMAINS_V2 = [
  {
    id: "incidents-escalation",
    label: "Incidents & Escalation",
    subline: "Active incidents, near misses, corrective action closure.",
    stripe: "#b91c1c", // red-700 — the only red domain
    icon: AlertOctagon,
    routes: [
      { to: "/safety-portal/incidents",          label: "Incidents & Near Misses", desc: "Severity-tagged review and follow-up.",    icon: AlertOctagon },
      { to: "/safety-portal/corrective-actions", label: "Corrective Actions",      desc: "Open, investigate, verify, close out.",     icon: ClipboardCheck },
      { to: "/tasks",                            label: "Tasks & Actions",         desc: "Cross-portal accountability and approvals.", icon: ListChecks },
    ],
  },
  {
    id: "documents-training",
    label: "Documents & Training",
    subline: "Library, certifications, accountability, PPE issuance.",
    stripe: "#0e7490", // cyan-700 — Safety brand chrome
    icon: Award,
    routes: [
      { to: "/safety-portal/training",      label: "Training & Certifications",     desc: "Records, renewals, sign-in sheets.",          icon: Award },
      { to: "/safety-portal/documents",     label: "Safety Document Library",       desc: "OSHA, SDS, EAPs, fall protection.",            icon: FolderArchive },
      { to: "/safety-portal/forms-records", label: "Equipment & PPE Accountability", desc: "Issuance, returns, use and care training.", icon: Package },
      { to: "/safety-portal/employees",     label: "Employee Safety Profiles",      desc: "Per-employee training, incidents, PPE.",      icon: Users },
    ],
  },
  {
    // TRACK 14.0-DISCOVERABILITY · Wave B — net-new domain group surfacing
    // three Safety records that were Wave A defects (D-A2/A4/A5):
    // toolbox / tailgate meetings, site inspections, JHA plans. All
    // three were reachable only via Admin namespace (wrong shell) or
    // not reachable at all from the Safety Hub. Adding them here puts
    // them inside the cyan Safety chrome with one click.
    id: "field-records",
    label: "Field Records & Plans",
    subline: "Toolbox talks, site inspections, JHA plans.",
    stripe: "#0e7490", // cyan-700 — Safety brand
    icon: ClipboardCheck,
    routes: [
      { to: "/safety-portal/meetings",     label: "Safety Meetings",   desc: "Toolbox talks and pre-shift huddles.",      icon: Users },
      { to: "/safety-portal/inspections",  label: "Site Inspections",  desc: "Job-site walkthroughs and grading.",        icon: ClipboardCheck },
      { to: "/safety-portal/jha-plans",    label: "JHA / JHP Plans",   desc: "Job hazard analyses and crew sign-offs.",   icon: FileText },
    ],
  },
  {
    id: "compliance-records",
    label: "Compliance & Records",
    subline: "Expirations, fire extinguishers, weekly digest, reports.",
    stripe: "#7c3aed", // violet-600
    icon: FileText,
    routes: [
      { to: "/document-expirations",             label: "Document Expirations", desc: "Cert and qualification windows.",        icon: FileText },
      { to: "/safety-portal/fire-extinguishers", label: "Fire Extinguishers",   desc: "Monthly inspections and unit history.",   icon: Flame },
      { to: "/safety-portal/digest",             label: "Weekly Digest",        desc: "Monday email of open and overdue items.", icon: Mail },
      { to: "/safety-portal/reports",            label: "Reports & Exports",    desc: "OSHA 300, trend, executive roll-ups.",    icon: BarChart3 },
      { to: "/hr/historical-records/intake",     label: "Safety Records Intake", desc: "Upload legacy safety records for an employee.", icon: FileText },
      { to: "/hr/historical-records/queue",      label: "Safety Records Queue",  desc: "Approve or reject staged Safety-lane records.", icon: FileText },
      { to: "/hr/historical-records/batches",    label: "Bulk Historical Intake", desc: "Many files · one session · Safety lane.",       icon: FileText },
    ],
  },
  {
    id: "audits-guidance",
    label: "Training Center & Systems",
    subline: "Inspections, topic prep, fleet visibility, and how-to guides.",
    stripe: "#475569", // slate-600
    icon: ShieldAlert,
    routes: [
      { to: "/safety-portal/audits",  label: "Audits & Inspections", desc: "Job-site safety inspection review.",      icon: ShieldAlert },
      { to: "/odr/center",            label: "Operational Daily Records", desc: "Field-day events · readiness signals.", icon: NotebookPen },
      { to: "/safety-portal/library", label: "Topic Library",        desc: "Filter and pack safety topics for prep.", icon: BookOpen },
      { to: "/safety-portal/fleet",   label: "Trucking · Fleet",     desc: "Defects, driver notes, severity context.", icon: Truck },
      { to: "/guidance?from=safety",  label: "Training Center",      desc: "How-to guides and troubleshooting.",     icon: GraduationCap },
    ],
  },
];

const SideNavLink = ({ to, label, desc, icon: Icon, end = false, stripe }) => {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        `block px-3 py-2.5 rounded-xl transition-colors glass-blur glass-bg glass-dark ${
          isActive
            ? "bg-slate-800 text-white"
            : "text-slate-300 hover:bg-slate-800/60 hover:text-white"
        }`
      }
      data-testid={`safety-side-nav-link-${to.replace(/[^a-z0-9]+/gi, "-")}`}
    >
      {({ isActive }) => (
        <div className="flex items-start gap-2.5">
          <Icon
            className={`w-4 h-4 mt-0.5 flex-shrink-0 ${
              isActive ? "text-white" : "text-slate-400"
            }`}
            style={isActive ? { color: stripe } : undefined}
          />
          <div className="min-w-0">
            <div className="font-mono text-[11px] uppercase tracking-wide font-bold leading-tight glass-text-light">
              {label}
            </div>
            <div className="text-[10.5px] leading-snug mt-0.5 glass-text-muted-light">
              {desc}
            </div>
          </div>
        </div>
      )}
    </NavLink>
  );
};

const DomainGroup = ({ domain }) => (
  <div className="mb-5" data-testid={`safety-side-nav-domain-${domain.id}`}>
    <div className="flex items-center gap-2 px-3 mb-2">
      <span
        className="inline-block w-1 h-4 rounded-sm"
        style={{ backgroundColor: domain.stripe }}
      />
      <span
        className="font-mono text-[10px] uppercase tracking-[0.22em] font-bold glass-text-light"
        style={{ color: domain.stripe }}
      >
        {domain.label}
      </span>
    </div>
    <p className="px-3 text-[10.5px] leading-snug mb-2 glass-text-muted-light">
      {domain.subline}
    </p>
    <div className="space-y-0.5">
      {domain.routes.map((r) => (
        <SideNavLink key={r.to} {...r} stripe={domain.stripe} />
      ))}
    </div>
  </div>
);

export default function SafetySideNavV2({ className = "" }) {
  return (
    <nav
      className={`space-y-3 p-3 bg-slate-900 border border-slate-800 overflow-y-auto glass-blur glass-bg glass-dark elite-glass-sidebar rounded-[1.75rem] ${className}`}
      data-testid="safety-side-nav-desktop"
      aria-label="Safety sidebar"
    >
      {SAFETY_DOMAINS_V2.map((d) => (
        <DomainGroup key={d.id} domain={d} />
      ))}
    </nav>
  );
}

// Helper · iter437 IV-BETA.5A-P6 · Safety Sidebar V2 is now the DEFAULT
// layout. Operators can opt out without a redeploy. Resolution order
// mirrors the PM `isPmSidebarV2Enabled` pattern exactly:
//
//   1. URL query `?safetySidebarV2=0|1` (sticky · writes to localStorage)
//   2. localStorage `masci.safety.sidebar.v2` ("0" → force OFF · "1" → on)
//   3. env `REACT_APP_SAFETY_SIDEBAR_V2` ("0" / "false" → off)
//   4. default: **ON** (V2 default · iter437 IV-BETA.5A-P6)
export function useSafetySidebarV2Enabled() {
  const loc = useLocation();
  // URL flag (sticky · writes through to localStorage so it persists
  // across the rest of the Safety session).
  const search = loc.search || "";
  if (/[?&]safetySidebarV2=0\b/.test(search)) {
    try { localStorage.setItem("masci.safety.sidebar.v2", "0"); } catch { /* ignore */ }
    return false;
  }
  if (/[?&]safetySidebarV2=1\b/.test(search)) {
    try { localStorage.setItem("masci.safety.sidebar.v2", "1"); } catch { /* ignore */ }
    return true;
  }
  // localStorage override (set once, persists until cleared).
  try {
    const ls = localStorage.getItem("masci.safety.sidebar.v2");
    if (ls === "0") return false;
    if (ls === "1") return true;
  } catch { /* ignore */ }
  // Env-level kill-switch (rarely needed in preview, but available for
  // emergency rollback without touching code).
  const env = (process.env.REACT_APP_SAFETY_SIDEBAR_V2 || "").toLowerCase();
  if (env === "0" || env === "false") return false;
  // Default · V2 default posture (iter437 IV-BETA.5A-P6)
  return true;
}
