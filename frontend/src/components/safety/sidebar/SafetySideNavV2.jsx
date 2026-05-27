// Safety Portal · Sidebar V2 · iter437 / Phase IV-BETA.5A
//
// Mirrors HR Sidebar V2 discipline (HrSideNavV2.jsx). 4-domain layout
// driven by SAFETY_INFORMATION_PRIORITY_MAP.json. Mounted behind
// `?safetySidebarV2=1` so legacy Safety chrome stays untouched when
// the flag is off — pure additive change, zero regression risk.
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
  BookOpen, Truck, GraduationCap,
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
    ],
  },
  {
    id: "audits-guidance",
    label: "Audits & Guidance",
    subline: "Inspections, topic prep, fleet visibility, operator guides.",
    stripe: "#475569", // slate-600
    icon: ShieldAlert,
    routes: [
      { to: "/safety-portal/audits",  label: "Audits & Inspections", desc: "Job-site safety inspection review.",      icon: ShieldAlert },
      { to: "/safety-portal/library", label: "Topic Library",        desc: "Filter and pack safety topics for prep.", icon: BookOpen },
      { to: "/safety-portal/fleet",   label: "Trucking · Fleet",     desc: "Defects, driver notes, severity context.", icon: Truck },
      { to: "/guidance?from=safety",  label: "Training Center",      desc: "Step-by-step Safety operator guides.",     icon: GraduationCap },
    ],
  },
];

const SideNavLink = ({ to, label, desc, icon: Icon, end = false, stripe }) => {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        `block px-3 py-2.5 rounded-md transition-colors ${
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
            <div className="font-mono text-[11px] uppercase tracking-wide font-bold leading-tight">
              {label}
            </div>
            <div className="text-[10.5px] text-slate-400 leading-snug mt-0.5">
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
        className="font-mono text-[10px] uppercase tracking-[0.22em] font-bold"
        style={{ color: domain.stripe }}
      >
        {domain.label}
      </span>
    </div>
    <p className="px-3 text-[10.5px] text-slate-500 leading-snug mb-2">
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
      className={`bg-slate-900 border-r border-slate-800 overflow-y-auto py-5 ${className}`}
      data-testid="safety-side-nav-desktop"
      aria-label="Safety sidebar"
    >
      {SAFETY_DOMAINS_V2.map((d) => (
        <DomainGroup key={d.id} domain={d} />
      ))}
    </nav>
  );
}

// Helper · reads the ?safetySidebarV2=1 query flag (mirrors HR/PM pattern).
export function useSafetySidebarV2Enabled() {
  const loc = useLocation();
  return /[?&]safetySidebarV2=1\b/.test(loc.search || "");
}
