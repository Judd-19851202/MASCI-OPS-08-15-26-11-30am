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
  GraduationCap, ListChecks, Activity, Lock,
} from "lucide-react";
import { api } from "@/lib/api";
import { getAdminToken, isAdmin } from "@/lib/adminAuth";
import { getDispatchToken } from "@/lib/dispatchAuth";

export const TENANT = "masci";

export function adminHeaders() {
  return { "X-Admin-Token": getAdminToken() || "" };
}

// TRACK 18.12C · Cross-role header bundle.
// Transportation Operations is a SHARED operational doorway between
// Super Admin and Dispatch users. Read-only endpoints under
// `/api/admin/transportation/*` that have been migrated to the
// `_local_dispatch_or_admin` gate accept EITHER header. We always send
// both — the empty-string short-circuit is fine because the gate
// requires a "." in the token, which empty strings don't have.
export function txHeaders() {
  return {
    "X-Admin-Token": getAdminToken() || "",
    "X-Dispatch-Token": getDispatchToken() || "",
  };
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
  const prefix = useTxPathPrefix();
  const groups = visibleTxOpsNavGroups();
  return (
    <nav
      className="space-y-2 border-b border-slate-200 pb-3 mb-4"
      data-testid="transportation-subnav"
      aria-label="Transportation Operations navigation"
    >
      {groups.map((group) => (
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
              to={`${prefix}/${item.to}`}
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
  // TRACK 18.12B · Restricted-state plumbing — the single 401/403-safe
  // doorway for every Transportation Operations data loader.
  //
  // Every Transportation Operations workspace calls admin-strict
  // /api/admin/transportation/* endpoints. For dispatch / non-admin
  // transportation tokens those endpoints return 401/403. Letting the
  // raw axios rejection bubble up triggers React's dev runtime-error
  // overlay AND surfaces raw "Admin login required" / "Request failed
  // with status code 401" copy in the operational chrome — both
  // forbidden by Track 18.12B doctrine. We silence 401/403 here and
  // resolve with a restricted-tagged payload. Loaders inspect the
  // marker via `isTxRestricted()` and render <TxOpsRestrictedData />
  // (or workspace-level <TxOpsRestricted />). Other HTTP errors still
  // throw, preserving real error reporting.
  return api
    .get(path, { headers: txHeaders(), params, skipSessionStatus: true })
    .catch((err) => {
      const status = err?.response?.status;
      if (status === 401 || status === 403) {
        return {
          data: {
            restricted: true,
            rows: [],
            items: [],
            signals: [],
            records: [],
          },
          status,
          __txRestricted: true,
        };
      }
      throw err;
    });
}

// TRACK 18.12B · Detection helper.
// True when the response was synthesised by txGet's 401/403 absorption
// path. Loaders use it to render a Transportation-branded restricted
// state instead of an empty grid / silent failure.
export function isTxRestricted(r) {
  if (!r) return false;
  if (r.__txRestricted === true) return true;
  if (r.data && r.data.restricted === true) return true;
  return false;
}

// TRACK 18.12B · txCatch — error-message normaliser for legacy loaders
// that wrap their own try/catch. Strips the forbidden "Admin login
// required" / "Request failed with status code 4xx" / "Forbidden" /
// "Unauthorized" tokens before they hit any user-facing surface.
// Returns null for absorbed auth failures (caller should render a
// restricted state); returns a human-safe message string otherwise.
export function txCatch(err) {
  const status = err?.response?.status;
  if (status === 401 || status === 403) return null;
  const raw =
    err?.response?.data?.detail ||
    err?.message ||
    "Unable to load right now.";
  const safe = String(raw)
    .replace(/Admin login required\.?/gi, "")
    .replace(/Request failed with status code 4\d{2}/gi, "")
    .replace(/^Forbidden$/i, "")
    .replace(/^Unauthorized$/i, "")
    .trim();
  return safe || "Unable to load right now.";
}

// TRACK 18.12B · TxOpsRestricted helpers re-exported so Transportation
// loaders can adopt them without a new import line. Kept thin —
// rendering is owned by /components/transportation/TxOpsRestricted.
export function TxOpsLoaderRestricted({ workspace, testid }) {
  return (
    <div
      data-testid={testid || "txops-loader-restricted"}
      className="rounded-md border border-amber-300/40 bg-amber-50/60 px-4 py-6 text-center"
    >
      <Lock className="mx-auto h-5 w-5 text-amber-700 mb-2" aria-hidden />
      <div className="text-[11px] uppercase tracking-wider font-semibold text-amber-800">
        Transportation Operations
      </div>
      <p className="mt-1 text-sm text-slate-700 max-w-md mx-auto">
        {workspace
          ? `This Transportation workspace (${workspace}) is restricted for your role.`
          : "This Transportation data is not available for your role."}
      </p>
      <p className="mt-1 text-xs text-slate-500">
        Contact your dispatcher lead or operations manager to request access.
      </p>
    </div>
  );
}

// TRACK 18.12B/C · Role-aware nav filter — VISIBLE = USABLE.
// Track 18.12C amendment: if a workspace is visible to a dispatcher it
// MUST be usable. Any Class-C admin-governance surface must either be
// hidden from the dispatch nav OR (for the rare deep-link case) render
// a clean restricted state. This filter is the primary visibility gate.
//
// Dispatch-hidden items:
//   • Administration group as a whole (Audit Timeline + Reports placeholder)
//   • Operations Intelligence → Intelligence (admin-only deep analytics)
//
// Dispatch-visible items must back real data via OPS-GUARD endpoints:
//   • Mission Control · Dispatch · Live Operations · Fleet · Drivers ·
//     Carriers · Compliance · Orientation · Automation (Morning Queue +
//     Forecast) · Cleanup
const DISPATCH_HIDDEN_NAV_ITEMS = new Set([
  // Class C admin-only deep analytics.
  "txops-nav-intelligence",
]);

export function visibleTxOpsNavGroups() {
  const admin = isAdmin();
  if (admin) return TX_OPS_NAV_GROUPS;
  return TX_OPS_NAV_GROUPS
    // Drop entire admin-governance group.
    .filter((g) => g.key !== "administration")
    // Drop individual admin-only items from each retained group.
    .map((g) => ({
      ...g,
      items: g.items.filter(
        (it) => !DISPATCH_HIDDEN_NAV_ITEMS.has(it.testid),
      ),
    }))
    // Drop now-empty groups (shouldn't happen given current shape, but
    // keeps the SubNav from rendering a heading with no items).
    .filter((g) => g.items && g.items.length > 0);
}

/**
 * TRACK 18.12 · Mission Control access repair.
 *
 * Returns the active Transportation routing prefix based on the
 * current URL — `/transportation-operations` for dispatch /
 * transportation users, `/admin/transportation` for admin oversight.
 * Both doorways mount the SAME `TransportationApp` router (Track
 * 18.09C single source of truth), so the only thing we need to do
 * to keep dispatch users inside Transportation Operations is to use
 * the prefix-aware builder for every user-facing route.
 */
export function useTxPathPrefix() {
  const loc = useLocation();
  if (loc.pathname.startsWith("/transportation-operations")) {
    return "/transportation-operations";
  }
  return "/admin/transportation";
}

export function useTxLocation() {
  const loc = useLocation();
  return loc.pathname
    .replace(/^\/transportation-operations/, "")
    .replace(/^\/admin\/transportation/, "")
    .replace(/^\/+/, "");
}
