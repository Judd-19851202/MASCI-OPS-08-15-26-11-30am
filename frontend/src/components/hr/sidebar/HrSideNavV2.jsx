// HR Portal · Sidebar V2 · iter437 / Phase IV-BETA.3B
//
// Mirrors the PM V2 pattern (domain-grouped, calm, executive-grade)
// behind a feature flag (?hrSidebarV2=1). When the flag is off, the
// HR portal renders exactly as before — pure additive change, zero
// regression risk for legacy users.
//
// Governance contracts honoured:
//   • OPERATIONAL_VERBIAGE_DOCTRINE.md §IV (no marketing slop)
//   • CROSS_PORTAL_COACHING_STANDARD.md §V (≤14-word coaching sublines)
//   • VISUAL_LOUDNESS_REDUCTION_PLAN.md §I (single accent stripe per
//     domain · no rainbow palette · slate-900 chrome)
//   • PM Sidebar V2 reference (frontend/src/components/pm/sidebar/)

import React from "react";
import { NavLink, useLocation } from "react-router-dom";
import {
  Activity, Users, Search, Clock, GraduationCap, Calculator,
  CalendarOff, Receipt, Truck, ClipboardList, ShieldCheck, BookOpen,
  KeyRound, FileText, AlertTriangle, Inbox, Upload,
} from "lucide-react";

// Domain groups · ordered by operational frequency (highest first).
// `stripe` colour communicates the domain; routes share the same colour.
export const HR_DOMAINS_V2 = [
  {
    id: "people-operations",
    label: "People Operations",
    subline: "Day-to-day employee lifecycle and field accountability.",
    stripe: "#16a34a", // green-600
    icon: Users,
    routes: [
      { to: "/hr",                        label: "Overview",            desc: "Today's HR signal across the field.",                 icon: Activity, end: true },
      { to: "/hr/daily-reports",          label: "Daily Reports",       desc: "Read-only HR audit of crew daily reports.",            icon: ClipboardList },
      { to: "/hr/employees",              label: "Employee Lifecycle",  desc: "Add, status, offboarding, termination playbook.",     icon: Users },
      { to: "/hr/employee-accountability", label: "Employee Accountability", desc: "Per-employee records, history, equipment, clearance.", icon: Search },
      { to: "/hr/incidents",              label: "Incidents",            desc: "Read-only OSHA-relevant list · CSV export.",          icon: AlertTriangle },
      { to: "/hr/field-leadership-users", label: "Field Leadership Users",   desc: "Create, disable, reset passwords for Field Leadership logins.", icon: KeyRound },
      { to: "/hr/field-leadership",       label: "Field Leadership Records", desc: "Crew docs, coaching, recognition, evaluations.",  icon: Users },
    ],
  },
  {
    id: "time-payroll",
    label: "Time & Payroll",
    subline: "Time verification, payroll variance, expense visibility.",
    stripe: "#0284c7", // sky-600
    icon: Clock,
    routes: [
      { to: "/hr/time-verification", label: "Time Verification", desc: "Daily report labor, lunch, payroll cross-check.",  icon: Clock },
      { to: "/hr/payroll-variance",  label: "Payroll Variance",  desc: "Reconcile Exact CSV against MASCI hours.",          icon: Calculator },
      { to: "/hr/time-off",          label: "Time Off Requests", desc: "Vacation, sick, medical, bereavement approvals.",   icon: CalendarOff },
      { to: "/po-requests",          label: "PO Requests",       desc: "Pending approvals, receipts, employee-linked spend.", icon: Receipt },
    ],
  },
  {
    id: "compliance-records",
    label: "Compliance & Records",
    subline: "Certifications, driver qualification, safety overlap.",
    stripe: "#7c3aed", // violet-600
    icon: ShieldCheck,
    routes: [
      { to: "/document-expirations",     label: "Document Expirations", desc: "OSHA, TWIC, CDL, training cert windows.",         icon: FileText },
      { to: "/hr/qualifications",        label: "Professional Qualifications", desc: "Competent Person + all OSHA / MSHA / trade credentials.", icon: ShieldCheck },
      { to: "/hr/training-records",      label: "Training Records",     desc: "Completed tracks and certification roster.",      icon: GraduationCap },
      { to: "/hr/driver-qualification",  label: "Driver Qualification", desc: "CDL holders, endorsements, tanker capability.",   icon: Truck },
      { to: "/hr/safety-records",        label: "Safety Records",       desc: "Read-only Safety document library and per-employee training.", icon: ShieldCheck },
      { to: "/hr/historical-records/intake", label: "Historical Records Intake", desc: "Upload legacy records — HR, Safety, Asset lanes.", icon: Upload },
      { to: "/hr/historical-records/queue",  label: "Historical Records Queue",  desc: "Review, approve, reject staged records.",         icon: Inbox },
      { to: "/hr/historical-records/batches", label: "Bulk Historical Intake",   desc: "Many files · one session · classify · approve.", icon: ClipboardList },
    ],
  },
  {
    id: "guidance",
    label: "Guidance",
    subline: "Operator guides and supporting documentation.",
    stripe: "#475569", // slate-600
    icon: BookOpen,
    routes: [
      { to: "/guidance?from=hr", label: "Training Center", desc: "Step-by-step HR operator guides.", icon: BookOpen },
      { to: "/hr/change-password", label: "Change Password", desc: "Rotate your sign-in credentials.", icon: KeyRound },
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
      data-testid={`hr-side-nav-link-${to.replace(/[^a-z0-9]+/gi, "-")}`}
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
  <div className="mb-5" data-testid={`hr-side-nav-domain-${domain.id}`}>
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

export default function HrSideNavV2({ className = "" }) {
  return (
    <nav
      className={`bg-slate-900 border-r border-slate-800 overflow-y-auto py-5 ${className}`}
      data-testid="hr-side-nav-desktop"
      aria-label="HR sidebar"
    >
      {HR_DOMAINS_V2.map((d) => (
        <DomainGroup key={d.id} domain={d} />
      ))}
    </nav>
  );
}

// Helper · iter437 IV-BETA.5A-P2B · HR Sidebar V2 is now the DEFAULT
// layout. Returns FALSE only when `?hrSidebarV2=0` is explicitly present
// in the URL (operator escape hatch · matches PM V2 pattern).
export function useHrSidebarV2Enabled() {
  const loc = useLocation();
  // Explicit force-off escape hatch
  if (/[?&]hrSidebarV2=0\b/.test(loc.search || "")) return false;
  // Explicit force-on (still supported for clarity in tests / URLs)
  if (/[?&]hrSidebarV2=1\b/.test(loc.search || "")) return true;
  // Default · V2 default posture (iter437 IV-BETA.5A-P2B)
  return true;
}
