// portalContext.js — TRUST-PO-1 · 2026-05-28.
//
// Tracks which operational portal the operator is currently inside, so
// shared pages (e.g., /po-requests) can render capability-scoped UI
// even when the user happens to hold multiple portal tokens at once
// (the classic Super Admin in Field Leadership scenario).
//
// Source of truth: sessionStorage key `masci.portal-context`. Each
// portal hub writes its name on mount; navigating away from the hub
// does NOT clear the context — the context is the "most recent portal
// the user entered" until they explicitly enter a different portal.
//
// Recognised names:
//   "field-leadership"  · Field Leadership hub
//   "admin"             · Admin hub
//   "pm"                · PM hub
//   "hr"                · HR / Office hub
//   "safety"            · Safety portal
//   "shop"              · Shop portal
//   "public"            · marketing / unauthenticated surfaces
//
// Doctrine
// --------
//   * NEVER trust token-presence alone for capability decisions on
//     shared pages. ALWAYS consult portal context first.
//   * Setting context is idempotent + cheap. Safe to call from a
//     useEffect on every hub mount.
//   * Reading context returns "unknown" when nothing has been written
//     (very-first-load or test scenarios). Capability code MUST treat
//     "unknown" conservatively — render only ALWAYS-allowed actions.

const KEY = "masci.portal-context";

const KNOWN = new Set([
  "field-leadership",
  "admin",
  "pm",
  "hr",
  "safety",
  "shop",
  "public",
]);

export function setPortalContext(name) {
  if (!name || !KNOWN.has(name)) return;
  try {
    window.sessionStorage.setItem(KEY, name);
  } catch { /* sessionStorage disabled — capabilities will fall back to "unknown" */ }
}

export function getPortalContext() {
  try {
    const v = window.sessionStorage.getItem(KEY) || "";
    return KNOWN.has(v) ? v : "unknown";
  } catch {
    return "unknown";
  }
}

export function clearPortalContext() {
  try { window.sessionStorage.removeItem(KEY); } catch { /* noop */ }
}

// Convenience predicates for the most common gates.
export function isInFieldLeadershipContext() {
  return getPortalContext() === "field-leadership";
}

export function isInApproverContext() {
  const ctx = getPortalContext();
  return ctx === "pm" || ctx === "hr" || ctx === "admin";
}

// Test seam.
export const __TESTING__ = { KEY, KNOWN };
