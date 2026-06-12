// Track 13.5A · Phase B1 — Canonical status vocabulary registry.
//
// Presentation foundation only. NO business logic migration in Phase B1.
// Maps non-punitive operator-native status labels to severity variants
// and (where applicable) the engine literal a workflow currently emits.
//
// Forbidden labels (REJECTED · DENIED · FAILED) are deliberately absent.
//
// Source: MASCI_DESIGN_SYSTEM_V1.md §11.

export const STATUS_FAMILY = {
  GENERAL: "general",
  HOLD: "hold",
  ASSET: "asset",
};

// severity drives the StatusChip color: neutral · info · positive · attention · urgent · halt
export const STATUS_REGISTRY = {
  // ── General workflow lifecycle ─────────────────────────────
  draft:                { label: "Draft",                family: STATUS_FAMILY.GENERAL, severity: "neutral",   icon: "edit-3" },
  submitted:            { label: "Submitted",            family: STATUS_FAMILY.GENERAL, severity: "info",      icon: "send" },
  needs_revision:       { label: "Needs Revision",       family: STATUS_FAMILY.GENERAL, severity: "attention", icon: "rotate-ccw" },
  pending_verification: { label: "Pending Verification", family: STATUS_FAMILY.GENERAL, severity: "info",      icon: "clock" },
  verified:             { label: "Verified",             family: STATUS_FAMILY.GENERAL, severity: "positive",  icon: "check" },
  closed:               { label: "Closed",               family: STATUS_FAMILY.GENERAL, severity: "neutral",   icon: "check-circle" },
  reopened:             { label: "Reopened",             family: STATUS_FAMILY.GENERAL, severity: "attention", icon: "rotate-cw" },

  // ── Holds ─────────────────────────────────────────────────
  safety_hold:          { label: "Safety Hold",          family: STATUS_FAMILY.HOLD,    severity: "urgent",    icon: "shield-alert" },
  maintenance_hold:     { label: "Maintenance Hold",     family: STATUS_FAMILY.HOLD,    severity: "attention", icon: "wrench" },
  certification_hold:   { label: "Certification Hold",   family: STATUS_FAMILY.HOLD,    severity: "attention", icon: "award" },
  inspection_hold:      { label: "Inspection Hold",      family: STATUS_FAMILY.HOLD,    severity: "attention", icon: "clipboard-check" },

  // ── Asset / fleet state ──────────────────────────────────-
  in_transport:         { label: "In Transport",         family: STATUS_FAMILY.ASSET,   severity: "info",      icon: "truck" },
  assigned:             { label: "Assigned",             family: STATUS_FAMILY.ASSET,   severity: "positive",  icon: "user-check" },
  available:            { label: "Available",            family: STATUS_FAMILY.ASSET,   severity: "positive",  icon: "check-circle" },
  returned_to_service:  { label: "Returned to Service",  family: STATUS_FAMILY.ASSET,   severity: "positive",  icon: "log-in" },
  stale_position:       { label: "Stale Position",       family: STATUS_FAMILY.ASSET,   severity: "attention", icon: "map-pin-off" },
  offline_feed:         { label: "Offline (Feed)",       family: STATUS_FAMILY.ASSET,   severity: "neutral",   icon: "wifi-off" },
};

// Labels we MUST NOT introduce. Lint helper for future PRs.
export const FORBIDDEN_LABELS = ["Rejected", "Denied", "Failed"];

// severity → token mapping (all token values resolve from tokens.css).
export const SEVERITY_STYLE = {
  neutral:   { color: "var(--ink-soft)",       bg: "var(--paper-tinted-info)",    border: "var(--border-bold)"   },
  info:      { color: "#0e7490",               bg: "var(--paper-tinted-info)",    border: "#a5f3fc"              },
  positive:  { color: "var(--status-good)",    bg: "var(--paper-tinted-success)", border: "#a7f3d0"              },
  attention: { color: "var(--status-warn)",    bg: "var(--paper-tinted-warn)",    border: "#fde68a"              },
  urgent:    { color: "var(--status-bad)",     bg: "var(--paper-tinted-error)",   border: "#fecaca"              },
  halt:      { color: "var(--brand-on-primary)", bg: "var(--brand-primary)",      border: "var(--brand-primary)" },
};

export function lookupStatus(key) {
  return STATUS_REGISTRY[key] || null;
}
