// Dispatch Portal · Sidebar V2 · iter437 / Phase IV-BETA.5A-P5B
//
// 4-domain governance navigation behind `?dispatchSidebarV2=1`.
// Mirrors HR / Safety / PM V2 patterns while honouring Dispatch's
// real-time velocity discipline (the live-board domain owns red).
//
// Governance contracts honoured:
//   • OPERATIONAL_VERBIAGE_DOCTRINE.md (no marketing slop)
//   • CROSS_PORTAL_COACHING_STANDARD.md (≤14-word coaching sublines)
//   • DISPATCH_INFORMATION_PRIORITY_MAP.json (canonical 4-domain map)
//   • DISPATCH_OPERATIONAL_VOLATILITY_MAP.md (NO slowdown of operator scan)

import React from "react";
import { NavLink, useLocation } from "react-router-dom";
import {
  AlertOctagon, ClipboardCheck, Plus, Truck, IdCard, KeyRound,
  Activity, FileClock, BarChart3, GraduationCap, ShieldEllipsis,
} from "lucide-react";

// Domain groups · ordered by operational velocity (highest first).
// `stripe` colour communicates the domain; red is the ONE live-board domain.
export const DISPATCH_DOMAINS_V2 = [
  {
    id: "live-board",
    label: "Live Board",
    subline: "Haul-board, escalations, breakdowns. Real-time scan.",
    stripe: "#b91c1c", // red-700 — the only red domain (live operations)
    icon: AlertOctagon,
    routes: [
      { to: "/dispatch-portal/board",           label: "Haul Board",         desc: "Five-second silent refresh. Severity-first.",        icon: AlertOctagon },
      { to: "/dispatch-portal",                 label: "Dispatch Hub",       desc: "Operational moments and primary actions.",            icon: ClipboardCheck, end: true },
      { to: "/dispatch-portal/assignments/new", label: "Create Assignment",  desc: "Issue a new haul to a truck and driver.",            icon: Plus },
    ],
  },
  {
    id: "driver-coordination",
    label: "Driver Coordination",
    subline: "Drivers, qualifications, magic-link sessions.",
    stripe: "#0e7490", // cyan-700 — Dispatch chrome
    icon: Truck,
    routes: [
      { to: "/dispatch-portal/drivers",                label: "Drivers Directory",     desc: "Active roster, contact, status.",               icon: Truck },
      { to: "/dispatch-portal/driver-qualification",   label: "Driver Qualification",  desc: "Eligibility, qualifications, MVR windows.",     icon: IdCard },
      { to: "/dispatch-portal/sessions",                label: "Active Sessions",       desc: "Live magic-link sessions and revocations.",     icon: KeyRound },
    ],
  },
  {
    id: "lifecycle-records",
    label: "Lifecycle & Records",
    subline: "Truck lifecycle, history, transition trails.",
    stripe: "#7c3aed", // violet-600
    icon: Activity,
    routes: [
      { to: "/dispatch-portal/lifecycle",   label: "Truck Lifecycle",   desc: "Current state and per-truck transitions.",       icon: Activity },
      { to: "/dispatch-portal/history",     label: "Assignment History", desc: "Past assignments, cancellations, outcomes.",     icon: FileClock },
      { to: "/dispatch-portal/reports",     label: "Reports & Exports", desc: "Utilization, dwell, deadhead summaries.",        icon: BarChart3 },
    ],
  },
  {
    id: "guidance-support",
    label: "Guidance & Support",
    subline: "Operator guides, password rotation, training center.",
    stripe: "#475569", // slate-600
    icon: ShieldEllipsis,
    routes: [
      { to: "/guidance?from=dispatch",            label: "Training Center",   desc: "Step-by-step Dispatch operator guides.",      icon: GraduationCap },
      { to: "/dispatch-portal/change-password",   label: "Change Password",   desc: "Update your Dispatch Portal password.",       icon: KeyRound },
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
          isActive ? "bg-slate-800 text-white" : "text-slate-300 hover:bg-slate-800/60 hover:text-white"
        }`
      }
      data-testid={`dispatch-side-nav-link-${to.replace(/[^a-z0-9]+/gi, "-")}`}
    >
      {({ isActive }) => (
        <div className="flex items-start gap-2.5">
          <Icon
            className={`w-4 h-4 mt-0.5 flex-shrink-0 ${isActive ? "text-white" : "text-slate-400"}`}
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
  <div className="mb-5" data-testid={`dispatch-side-nav-domain-${domain.id}`}>
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

export default function DispatchSideNavV2({ className = "" }) {
  return (
    <nav
      className={`bg-slate-900 border-r border-slate-800 overflow-y-auto py-5 ${className}`}
      data-testid="dispatch-side-nav-desktop"
      aria-label="Dispatch sidebar"
    >
      {DISPATCH_DOMAINS_V2.map((d) => (
        <DomainGroup key={d.id} domain={d} />
      ))}
    </nav>
  );
}

// Helper · reads the ?dispatchSidebarV2=1 query flag.
// Defaults to OFF this iteration (sub-pass 1 is foundation only; the
// flip-to-default decision belongs to a later sub-pass).
export function useDispatchSidebarV2Enabled() {
  const loc = useLocation();
  return /[?&]dispatchSidebarV2=1\b/.test(loc.search || "");
}
