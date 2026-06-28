/**
 * TRACK 16.06 · Transportation Experience Layer
 * Shared utilities, side nav, and API helpers for the Transportation
 * Compliance Center.
 *
 * All transportation pages share this shell so typography, spacing,
 * chip colors, and side-nav layout stay native to the rest of MASCI
 * Admin. New surface · zero new patterns.
 */
import React from "react";
import { NavLink, useLocation } from "react-router-dom";
import {
  LayoutDashboard, Building2, UserRound, Truck, ShieldCheck,
  FileText, ClipboardCheck, DollarSign, History, BarChart3,
  GraduationCap, ListChecks, Activity,
} from "lucide-react";
import { api } from "@/lib/api";
import { getAdminToken } from "@/lib/adminAuth";

export const TENANT = "masci";

export function adminHeaders() {
  return { "X-Admin-Token": getAdminToken() || "" };
}

export const STATE_LABEL = {
  eligible: "Eligible",
  pending_review: "Pending Review",
  needs_correction: "Needs Correction",
  expired: "Expired",
  suspended: "Suspended",
  not_dispatchable: "Not Dispatchable",
  ready: "Ready",
  pending_correction: "Pending Correction",
  not_ready: "Not Ready",
  accepted: "Accepted",
  draft: "Draft",
  sent: "Sent",
  opened: "Opened",
  in_progress: "In Progress",
  submitted: "Submitted",
  approved: "Approved",
  active: "Active",
  inactive: "Inactive",
  retired: "Retired",
};

export const STATE_BADGE = {
  eligible: "bg-emerald-100 text-emerald-800 border-emerald-200",
  approved: "bg-emerald-100 text-emerald-800 border-emerald-200",
  ready: "bg-emerald-100 text-emerald-800 border-emerald-200",
  active: "bg-emerald-100 text-emerald-800 border-emerald-200",
  accepted: "bg-emerald-100 text-emerald-800 border-emerald-200",
  pending_review: "bg-amber-100 text-amber-800 border-amber-200",
  pending_correction: "bg-amber-100 text-amber-800 border-amber-200",
  needs_correction: "bg-amber-100 text-amber-800 border-amber-200",
  in_progress: "bg-blue-100 text-blue-800 border-blue-200",
  submitted: "bg-blue-100 text-blue-800 border-blue-200",
  sent: "bg-blue-100 text-blue-800 border-blue-200",
  opened: "bg-blue-100 text-blue-800 border-blue-200",
  draft: "bg-slate-100 text-slate-700 border-slate-200",
  retired: "bg-slate-100 text-slate-600 border-slate-200",
  inactive: "bg-slate-200 text-slate-700 border-slate-300",
  expired: "bg-rose-100 text-rose-800 border-rose-200",
  suspended: "bg-rose-100 text-rose-800 border-rose-200",
  not_ready: "bg-rose-100 text-rose-800 border-rose-200",
  not_dispatchable: "bg-slate-200 text-slate-700 border-slate-300",
  unknown: "bg-slate-100 text-slate-600 border-slate-200",
};

export function Chip({ value, testid }) {
  const v = (value || "unknown").toLowerCase();
  const cls = STATE_BADGE[v] || STATE_BADGE.unknown;
  return (
    <span
      data-testid={testid || `chip-${v}`}
      className={`inline-flex items-center px-2 py-0.5 rounded border text-xs font-medium ${cls}`}
    >
      {STATE_LABEL[v] || value || "—"}
    </span>
  );
}

export const TX_NAV = [
  { to: "", icon: LayoutDashboard, label: "Dashboard", end: true },
  { to: "carriers", icon: Building2, label: "Carriers" },
  { to: "drivers", icon: UserRound, label: "Drivers" },
  { to: "trucks", icon: Truck, label: "Trucks" },
  { to: "compliance", icon: ShieldCheck, label: "Compliance" },
  { to: "documents", icon: FileText, label: "Documents" },
  { to: "inspections", icon: ClipboardCheck, label: "Inspections" },
  { to: "orientation", icon: GraduationCap, label: "Orientation" },
  { to: "command-queue", icon: ListChecks, label: "Command Queue" },
  { to: "intelligence", icon: Activity, label: "Intelligence" },
  { to: "rate-schedules", icon: DollarSign, label: "Rate Schedules" },
  { to: "audit", icon: History, label: "Audit Timeline" },
  { to: "reports", icon: BarChart3, label: "Reports" },
];

// TRACK 18.00 · Phase A · operational-group nav. Users think in
// operations, not workspaces. Groups + items defined here drive
// both the desktop sidebar nav and the compact top-strip nav.
// Every group/item uses unique data-testid for QA + RBAC tests.
export const TX_OPS_NAV_GROUPS = [
  {
    key: "overview",
    label: "Overview",
    testid: "txops-nav-group-overview",
    items: [
      { to: "", icon: LayoutDashboard, label: "Mission Control", end: true, testid: "txops-nav-overview" },
    ],
  },
  {
    key: "operations",
    label: "Operations",
    testid: "txops-nav-group-operations",
    items: [
      { to: "dispatch", icon: Truck, label: "Dispatch", testid: "txops-nav-dispatch" },
      { to: "live-operations", icon: Activity, label: "Live Operations", testid: "txops-nav-live-operations" },
      { to: "trucks", icon: Truck, label: "Fleet", testid: "txops-nav-fleet" },
    ],
  },
  {
    key: "people",
    label: "People",
    testid: "txops-nav-group-people",
    items: [
      { to: "drivers", icon: UserRound, label: "Drivers", testid: "txops-nav-drivers" },
      { to: "carriers", icon: Building2, label: "Carriers", testid: "txops-nav-carriers" },
    ],
  },
  {
    key: "compliance",
    label: "Compliance",
    testid: "txops-nav-group-compliance",
    items: [
      { to: "compliance", icon: ShieldCheck, label: "Compliance", testid: "txops-nav-compliance" },
      { to: "orientation", icon: GraduationCap, label: "Orientation", testid: "txops-nav-orientation" },
    ],
  },
  {
    key: "intelligence",
    label: "Operations Intelligence",
    testid: "txops-nav-group-intelligence",
    items: [
      { to: "intelligence", icon: Activity, label: "Intelligence", testid: "txops-nav-intelligence" },
      { to: "command-queue", icon: ListChecks, label: "Automation", testid: "txops-nav-automation" },
      { to: "intelligence/cleanup", icon: FileText, label: "Cleanup", testid: "txops-nav-cleanup" },
    ],
  },
  {
    key: "administration",
    label: "Administration",
    testid: "txops-nav-group-administration",
    items: [
      { to: "reports", icon: BarChart3, label: "Reports", testid: "txops-nav-reports" },
      { to: "audit", icon: History, label: "Administration", testid: "txops-nav-administration" },
    ],
  },
];

export function TransportationSubNav() {
  return (
    <nav
      className="space-y-2 border-b border-slate-200 pb-3 mb-4"
      data-testid="transportation-subnav"
      aria-label="Transportation Operations navigation"
    >
      {TX_OPS_NAV_GROUPS.map((group) => (
        <div
          key={group.key}
          data-testid={group.testid}
          className="flex flex-wrap items-center gap-1"
        >
          <span
            className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold mr-2 select-none"
            data-testid={`${group.testid}-label`}
          >
            {group.label}
          </span>
          {group.items.map((item) => (
            <NavLink
              key={item.testid}
              to={`/admin/transportation/${item.to}`}
              end={item.end}
              data-testid={item.testid}
              className={({ isActive }) =>
                `inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs transition-colors ${
                  isActive
                    ? "bg-slate-900 text-white"
                    : "text-slate-700 hover:bg-slate-100"
                }`
              }
            >
              <item.icon className="h-3.5 w-3.5" />
              {item.label}
            </NavLink>
          ))}
        </div>
      ))}
    </nav>
  );
}

export function PageHeader({ title, subtitle, right, testid }) {
  return (
    <div className="flex items-start justify-between mb-4" data-testid={testid}>
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">{title}</h1>
        {subtitle && (
          <p className="text-sm text-slate-600 mt-1 max-w-2xl">{subtitle}</p>
        )}
      </div>
      {right && <div className="flex items-center gap-2">{right}</div>}
    </div>
  );
}

export function ComingSoon({ feature, testid }) {
  return (
    <div
      data-testid={testid || "coming-soon"}
      className="inline-flex items-center gap-2 rounded-md border border-dashed border-slate-300 bg-slate-50 px-3 py-2 text-xs text-slate-500"
    >
      <span className="font-medium text-slate-700">{feature}</span>
      <span className="opacity-70">· Coming soon</span>
    </div>
  );
}

export function EmptyState({ title, hint, testid }) {
  return (
    <div
      data-testid={testid || "empty-state"}
      className="border border-dashed border-slate-200 rounded-md p-6 text-center text-slate-500"
    >
      <div className="font-medium text-slate-700">{title}</div>
      {hint && <div className="text-xs mt-1">{hint}</div>}
    </div>
  );
}

export function txGet(path, params) {
  return api.get(path, { headers: adminHeaders(), params });
}

export function useTxLocation() {
  const loc = useLocation();
  return loc.pathname.replace("/admin/transportation", "").replace(/^\/+/, "");
}
