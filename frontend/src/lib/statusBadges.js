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

// ─── Incident Lifecycle ──────────────────────────────────────────
// Per backend `incident_lifecycle.py` state machine.
export const INCIDENT_STATUS_TINTS = {
  "open":                "bg-blue-100 text-blue-800 border-blue-300",
  "in_review":           "bg-indigo-100 text-indigo-800 border-indigo-300",
  "corrective_pending":  "bg-amber-100 text-amber-800 border-amber-300",
  "closed":              "bg-slate-200 text-slate-700 border-slate-400",
  "reopened":            "bg-rose-100 text-rose-800 border-rose-300",
};

// ─── Daily Report Lifecycle ──────────────────────────────────────
// Per backend `daily_report_lifecycle.py` state machine.
export const DAILY_REPORT_STATUS_TINTS = {
  "OPEN":            "bg-blue-100 text-blue-800 border-blue-300",
  "PENDING_REVIEW":  "bg-amber-100 text-amber-800 border-amber-300",
  "CLOSED":          "bg-slate-200 text-slate-700 border-slate-400",
};

// ─── QA/QC Lifecycle ─────────────────────────────────────────────
// Per backend `qaqc_lifecycle.py` state machine.
export const QAQC_STATUS_TINTS = {
  "IN_PROGRESS":            "bg-blue-100 text-blue-800 border-blue-300",
  "DEFICIENCY_RAISED":      "bg-amber-100 text-amber-800 border-amber-300",
  "PENDING_RE_INSPECTION":  "bg-indigo-100 text-indigo-800 border-indigo-300",
  "CLOSED":                 "bg-emerald-100 text-emerald-800 border-emerald-300",
};

// ─── Site Inspection Lifecycle ───────────────────────────────────
// Per backend `site_inspection_lifecycle.py` state machine.
export const SITE_INSPECTION_STATUS_TINTS = {
  "IN_PROGRESS":            "bg-blue-100 text-blue-800 border-blue-300",
  "FINDINGS_RAISED":        "bg-amber-100 text-amber-800 border-amber-300",
  "PENDING_RE_INSPECTION":  "bg-indigo-100 text-indigo-800 border-indigo-300",
  "CLOSED":                 "bg-emerald-100 text-emerald-800 border-emerald-300",
};

// ─── Asset Transfer ──────────────────────────────────────────────
// Mirrors the local AssetTransfers.jsx STATUS_COLORS exactly.
export const ASSET_TRANSFER_STATUS_TINTS = {
  "Requested":    "bg-amber-50 text-amber-900 border-amber-300",
  "Approved":     "bg-indigo-50 text-indigo-900 border-indigo-300",
  "In Transit":   "bg-blue-50 text-blue-900 border-blue-300",
  "Received":     "bg-emerald-50 text-emerald-900 border-emerald-300",
  "Closed":       "bg-slate-50 text-slate-700 border-slate-300",
  "Rejected":     "bg-rose-50 text-rose-900 border-rose-300",
  "Cancelled":    "bg-slate-50 text-slate-500 border-slate-300",
};

// ─── Dispatch (operations) ───────────────────────────────────────
// Mirrors the local admin/AdminDispatch.jsx STATUS_COLORS exactly.
export const DISPATCH_STATUS_TINTS = {
  "Pending Review": "bg-amber-100 text-amber-900 border-amber-300",
  "Approved":       "bg-blue-100 text-blue-900 border-blue-300",
  "Scheduled":      "bg-violet-100 text-violet-900 border-violet-300",
  "In Transit":     "bg-cyan-100 text-cyan-900 border-cyan-300",
  "Completed":      "bg-emerald-100 text-emerald-900 border-emerald-300",
  "Denied":         "bg-red-100 text-red-900 border-red-300",
  "Cancelled":      "bg-slate-200 text-slate-700 border-slate-300",
};

// ─── FleetDVIR ────────────────────────────────────────────────────
export const FLEET_DVIR_STATUS_TINTS = {
  "Pass":          "bg-emerald-100 text-emerald-800 border-emerald-300",
  "Fail":          "bg-rose-100 text-rose-700 border-rose-300",
  "Needs Service": "bg-amber-100 text-amber-800 border-amber-300",
  "Out of Service":"bg-rose-200 text-rose-900 border-rose-400",
};

// ─── Operational Constraint ──────────────────────────────────────
// Per backend `operational_constraints.py`.
export const CONSTRAINT_STATUS_TINTS = {
  "open":        "bg-blue-100 text-blue-800 border-blue-300",
  "monitoring":  "bg-amber-100 text-amber-800 border-amber-300",
  "resolved":    "bg-emerald-100 text-emerald-800 border-emerald-300",
  "void":        "bg-slate-100 text-slate-500 border-slate-300",
};

// Domain registry — used by <StatusBadge kind="…" />.
export const STATUS_DOMAINS = {
  po:               PO_STATUS_TINTS,
  task:             TASK_STATUS_TINTS,
  priority:         TASK_PRIORITY_TINTS,
  doc_exp:          DOC_EXP_STATUS_TINTS,
  lifecycle:        LIFECYCLE_STATUS_TINTS,
  ca:               CA_STATUS_TINTS,
  severity:         SEVERITY_TINTS,
  incident:         INCIDENT_STATUS_TINTS,
  daily_report:     DAILY_REPORT_STATUS_TINTS,
  qaqc:             QAQC_STATUS_TINTS,
  site_inspection:  SITE_INSPECTION_STATUS_TINTS,
  asset_transfer:   ASSET_TRANSFER_STATUS_TINTS,
  dispatch:         DISPATCH_STATUS_TINTS,
  fleet_dvir:       FLEET_DVIR_STATUS_TINTS,
  constraint:       CONSTRAINT_STATUS_TINTS,
};

export function tintFor(kind, value) {
  const map = STATUS_DOMAINS[kind];
  if (!map) return DEFAULT_TINT;
  return map[value] || DEFAULT_TINT;
}

// ─── Operator-Target Display Labels (canonical vocabulary) ───────
// Per STATUS_CANONICAL_DICTIONARY.md.
// Maps domain + backend value → operator-target user-facing label.
// Returns null when no mapping exists; the consumer should fall back
// to a humanized version of the raw value (e.g., "IN_PROGRESS" → "In Progress").
// Adding rows here is the canonical way to retire raw-backend-string display.
export const STATUS_LABEL_MAP = {
  incident: {
    "open":               "Action Required",
    "in_review":          "Pending Verification",
    "corrective_pending": "Needs Revision",
    "closed":             "Closed",
    "reopened":           "Reopened",
  },
  daily_report: {
    "OPEN":           "Action Required",
    "PENDING_REVIEW": "Pending Verification",
    "CLOSED":         "Closed",
  },
  qaqc: {
    "IN_PROGRESS":           "Pending Verification",
    "DEFICIENCY_RAISED":     "Needs Revision",
    "PENDING_RE_INSPECTION": "Needs Correction",
    "CLOSED":                "Closed",
  },
  site_inspection: {
    "IN_PROGRESS":           "Pending Verification",
    "FINDINGS_RAISED":       "Needs Revision",
    "PENDING_RE_INSPECTION": "Needs Correction",
    "CLOSED":                "Closed",
  },
  asset_transfer: {
    "Requested":  "Action Required",
    "Approved":   "Pending Closure",
    "In Transit": "Pending Closure",
    "Received":   "Closed",
    "Closed":     "Closed",
    "Rejected":   "Closed",
    "Cancelled":  "Closed",
  },
  constraint: {
    "open":       "Action Required",
    "monitoring": "Pending Verification",
    "resolved":   "Closed",
    "void":       "Closed",
  },
};

/**
 * Humanize a raw backend status string for fallback display when no
 * canonical label is defined. Converts SCREAMING_SNAKE_CASE / snake_case
 * to Title Case With Spaces; leaves Title Case strings alone.
 */
function _humanize(s) {
  if (s == null) return "";
  const str = String(s);
  if (!/[_A-Z]/.test(str) || /\s/.test(str)) return str;
  return str
    .toLowerCase()
    .split(/[_\s]+/)
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

/**
 * Return the operator-target display label for a domain + value.
 * Falls back to the humanized raw value if no canonical mapping exists.
 *
 * Usage:
 *   labelFor("qaqc", "DEFICIENCY_RAISED")  // → "Needs Revision"
 *   labelFor("qaqc", "UNKNOWN_STATE")       // → "Unknown State"
 *   labelFor("po", "Approved")              // → "Approved"  (no map row; passthrough)
 */
export function labelFor(kind, value) {
  if (value == null) return "";
  const map = STATUS_LABEL_MAP[kind];
  if (map && map[value]) return map[value];
  return _humanize(value);
}
