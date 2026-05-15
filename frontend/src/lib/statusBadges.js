// lib/statusBadges.js — Iter B unification.
//
// Single source of truth for every status-color mapping platform-wide.
// Replaces 5 separate STATUS_COLORS constants in PoRequests, Tasks,
// DocumentExpirations, HrEmployees, SafetyCorrectiveActions.
//
// Each map is a tailwind-class object so consumers can render either
// via the <StatusBadge /> component (preferred) OR inline if needed
// (e.g., inside a table cell with custom layout).
//
// Adding a new domain: register it here, expose it via STATUS_DOMAINS,
// and consumers automatically get unified styling.

const DEFAULT_TINT = "bg-slate-100 text-slate-700 border-slate-300";

// ─── PO Requests ─────────────────────────────────────────────────
export const PO_STATUS_TINTS = {
  "Draft":                  "bg-slate-100 text-slate-700 border-slate-300",
  "Submitted":              "bg-blue-100 text-blue-800 border-blue-300",
  "Pending Approval":       "bg-blue-100 text-blue-800 border-blue-300",
  "Clarification Needed":   "bg-amber-100 text-amber-800 border-amber-300",
  "Approved":               "bg-emerald-100 text-emerald-800 border-emerald-300",
  "Rejected":               "bg-rose-100 text-rose-700 border-rose-300",
  "Pending Receipt":        "bg-indigo-100 text-indigo-800 border-indigo-300",
  "Receipt Uploaded":       "bg-cyan-100 text-cyan-800 border-cyan-300",
  "Closed":                 "bg-slate-200 text-slate-700 border-slate-400",
  "Overdue Receipt":        "bg-rose-100 text-rose-700 border-rose-300",
  "Cancelled":              "bg-slate-100 text-slate-500 border-slate-300",
};

// ─── Tasks ───────────────────────────────────────────────────────
export const TASK_STATUS_TINTS = {
  "Open":           "bg-blue-100 text-blue-800 border-blue-300",
  "In Progress":    "bg-indigo-100 text-indigo-800 border-indigo-300",
  "Pending Review": "bg-purple-100 text-purple-800 border-purple-300",
  "Blocked":        "bg-amber-100 text-amber-800 border-amber-300",
  "Done":           "bg-emerald-100 text-emerald-800 border-emerald-300",
  "Completed":      "bg-emerald-100 text-emerald-800 border-emerald-300",
  "Cancelled":      "bg-slate-100 text-slate-500 border-slate-300",
  "Closed":         "bg-slate-200 text-slate-700 border-slate-400",
  "Overdue":        "bg-rose-100 text-rose-700 border-rose-300",
};

export const TASK_PRIORITY_TINTS = {
  "Critical": "bg-rose-100 text-rose-800 border-rose-400",
  "High":     "bg-orange-100 text-orange-800 border-orange-300",
  "Medium":   "bg-amber-50 text-amber-800 border-amber-200",
  "Low":      "bg-slate-100 text-slate-700 border-slate-300",
};

// ─── Document Expirations ────────────────────────────────────────
export const DOC_EXP_STATUS_TINTS = {
  "Active":         "bg-emerald-100 text-emerald-800 border-emerald-300",
  "Current":        "bg-emerald-100 text-emerald-800 border-emerald-300",
  "Expiring Soon":  "bg-amber-100 text-amber-800 border-amber-300",
  "Expired":        "bg-rose-100 text-rose-700 border-rose-300",
  "Renewed":        "bg-blue-100 text-blue-800 border-blue-300",
  "Waived":         "bg-slate-100 text-slate-500 border-slate-300",
  "Archived":       "bg-slate-100 text-slate-500 border-slate-300",
  "Not Applicable": "bg-slate-50 text-slate-400 border-slate-200",
};

// ─── Employee Lifecycle ──────────────────────────────────────────
export const LIFECYCLE_STATUS_TINTS = {
  "Pending Hire":        "bg-blue-100 text-blue-800 border-blue-300",
  "Active":              "bg-emerald-100 text-emerald-800 border-emerald-300",
  "Seasonal":            "bg-cyan-100 text-cyan-800 border-cyan-300",
  "On Leave":            "bg-blue-100 text-blue-800 border-blue-300",
  "Leave of Absence":    "bg-amber-100 text-amber-800 border-amber-300",
  "Pending Onboarding":  "bg-amber-100 text-amber-800 border-amber-300",
  "Pending Offboarding": "bg-orange-100 text-orange-800 border-orange-300",
  "Suspended":           "bg-orange-100 text-orange-800 border-orange-300",
  "Offboarded":          "bg-slate-200 text-slate-700 border-slate-400",
  "Terminated":          "bg-rose-100 text-rose-700 border-rose-300",
  "Resigned":            "bg-rose-100 text-rose-700 border-rose-300",
  "Retired":             "bg-purple-100 text-purple-800 border-purple-300",
  "Inactive":            "bg-slate-100 text-slate-500 border-slate-300",
};

// ─── Corrective Actions ──────────────────────────────────────────
export const CA_STATUS_TINTS = {
  "Open":          "bg-blue-100 text-blue-800 border-blue-300",
  "In Progress":   "bg-indigo-100 text-indigo-800 border-indigo-300",
  "Completed":     "bg-emerald-100 text-emerald-800 border-emerald-300",
  "Overdue":       "bg-rose-100 text-rose-700 border-rose-300",
  "Closed":        "bg-slate-200 text-slate-700 border-slate-400",
  "Cancelled":     "bg-slate-100 text-slate-500 border-slate-300",
  "Verification":  "bg-cyan-100 text-cyan-800 border-cyan-300",
};

// ─── Severity (shared by Notifications + Incidents) ─────────────
export const SEVERITY_TINTS = {
  "Critical": "bg-rose-100 text-rose-800 border-rose-400",
  "Warning":  "bg-amber-100 text-amber-800 border-amber-300",
  "Info":     "bg-blue-100 text-blue-800 border-blue-300",
  "High":     "bg-rose-100 text-rose-800 border-rose-400",
  "Medium":   "bg-amber-100 text-amber-800 border-amber-300",
  "Low":      "bg-slate-100 text-slate-700 border-slate-300",
};

// Domain registry — used by <StatusBadge kind="…" />.
export const STATUS_DOMAINS = {
  po:        PO_STATUS_TINTS,
  task:      TASK_STATUS_TINTS,
  priority:  TASK_PRIORITY_TINTS,
  doc_exp:   DOC_EXP_STATUS_TINTS,
  lifecycle: LIFECYCLE_STATUS_TINTS,
  ca:        CA_STATUS_TINTS,
  severity:  SEVERITY_TINTS,
};

export function tintFor(kind, value) {
  const map = STATUS_DOMAINS[kind];
  if (!map) return DEFAULT_TINT;
  return map[value] || DEFAULT_TINT;
}
