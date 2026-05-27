// returnContext.js — iter443 · P1 governance refinement.
//
// Single source of truth for "where does Back go AND what does it
// say?" on shared surfaces (pages reachable from more than one
// portal: ViewIncident, ViewInspection, ViewMeeting, ViewCAPA, …).
//
// Doctrine
// --------
//   - Pure JS. No global state. No localStorage. No sessionStorage.
//   - Resolution order is fixed and documented (see below).
//   - Falls back gracefully to the caller-supplied default.
//   - Labels here are ENGLISH KEYS; translation is the consumer's
//     job (call `t(ret.label)` at the render site).
//
// Resolution order (first non-empty wins)
//   1. location.state.from = { label, path, key? }   (explicit caller)
//   2. ?from=<key>&fromPath=<path>                   (deep link)
//   3. derived from current pathname                 (best guess)
//   4. supplied fallback                             (last resort)
//
// Cross-ref: SHARED_SURFACE_CONTEXT_MAP.md / RETURN_PATH_GOVERNANCE_STANDARD.md.

import { useMemo } from "react";
import { useLocation } from "react-router-dom";

// Closed set of context keys. Adding one requires updating the
// SHARED_SURFACE_CONTEXT_MAP doc + the regression test.
const KNOWN_KEYS = {
  "admin-console":    { label: "Admin Console",  path: "/admin" },
  "admin-incidents":  { label: "Incidents",      path: "/admin/incidents" },
  "pm-portal":        { label: "PM Portal",      path: "/pm" },
  "pm-incidents":     { label: "Incidents",      path: "/pm/incidents" },
  "pm-project":       { label: "Project Safety", path: "/pm" },  // path overridden by caller
  "safety-portal":    { label: "Safety Portal",  path: "/safety-portal" },
  "safety-incidents": { label: "Incident Center", path: "/safety-portal/incidents" },
  "hr-portal":        { label: "HR Portal",      path: "/hr" },
  "shop-portal":      { label: "Shop Portal",    path: "/shop" },
  "incidents":        { label: "Incidents",      path: "/incidents" },
};

function _validShape(o) {
  return o && typeof o === "object" && typeof o.label === "string" && typeof o.path === "string"
    && o.label.length > 0 && o.path.length > 0;
}

function _fromState(state) {
  if (!state || typeof state !== "object") return null;
  const f = state.from;
  if (!_validShape(f)) return null;
  return {
    key: typeof f.key === "string" ? f.key : "state",
    label: f.label,
    path: f.path,
  };
}

function _fromQuery(search) {
  if (!search) return null;
  try {
    const sp = new URLSearchParams(search);
    const key = sp.get("from");
    if (!key) return null;
    const fromPath = sp.get("fromPath");
    if (KNOWN_KEYS[key]) {
      const base = KNOWN_KEYS[key];
      return {
        key,
        label: base.label,
        path: fromPath && fromPath.startsWith("/") ? fromPath : base.path,
      };
    }
    // Unknown key with explicit path is still acceptable as a soft
    // override; we use the key as label (operator-readable) if it
    // looks human-ish; otherwise fall through.
    if (fromPath && fromPath.startsWith("/") && /^[a-z0-9-]+$/i.test(key)) {
      const human = key.split("-").map((s) => s.charAt(0).toUpperCase() + s.slice(1)).join(" ");
      return { key, label: human, path: fromPath };
    }
  } catch { /* malformed query — fall through */ }
  return null;
}

// Pathname → derived context. Matches most-specific first, then
// prefixes. Returns null if nothing matches.
export function deriveFromPathname(pathname) {
  if (!pathname || typeof pathname !== "string") return null;
  // Exact list pages (so list → detail → back returns to list with
  // the right label, "Incidents", not "Admin Console").
  if (pathname === "/admin/incidents") {
    return { ...KNOWN_KEYS["admin-incidents"], key: "admin-incidents" };
  }
  if (pathname === "/pm/incidents") {
    return { ...KNOWN_KEYS["pm-incidents"], key: "pm-incidents" };
  }
  if (pathname === "/safety-portal/incidents") {
    return { ...KNOWN_KEYS["safety-incidents"], key: "safety-incidents" };
  }
  // Project dashboard scope.
  const pmProj = pathname.match(/^(\/pm\/projects\/[^/]+)/);
  if (pmProj) {
    return {
      key: "pm-project",
      label: "Project Safety",
      path: `${pmProj[1]}/dashboard`,
    };
  }
  // Portal-wide prefixes.
  if (pathname.startsWith("/admin/")) {
    return { ...KNOWN_KEYS["admin-console"], key: "admin-console" };
  }
  if (pathname.startsWith("/pm/")) {
    return { ...KNOWN_KEYS["pm-portal"], key: "pm-portal" };
  }
  if (pathname.startsWith("/safety-portal/")) {
    return { ...KNOWN_KEYS["safety-portal"], key: "safety-portal" };
  }
  if (pathname.startsWith("/hr/")) {
    return { ...KNOWN_KEYS["hr-portal"], key: "hr-portal" };
  }
  if (pathname.startsWith("/shop/")) {
    return { ...KNOWN_KEYS["shop-portal"], key: "shop-portal" };
  }
  return null;
}

/**
 * @param fallback {label, path, key?}
 * @returns {label, path, key}
 *
 * Always returns a valid ReturnContext shape — fallback covers the
 * worst case.
 */
export function useReturnContext(fallback) {
  const loc = useLocation();
  return useMemo(() => {
    return (
      _fromState(loc.state) ||
      _fromQuery(loc.search) ||
      deriveFromPathname(loc.pathname) ||
      fallback ||
      { key: "fallback", label: "Back", path: "/" }
    );
  }, [loc.state, loc.search, loc.pathname, fallback]);
}

// Test helper — pure resolver, no hook.
export function _resolveReturnContextForTests({ state, search, pathname, fallback }) {
  return (
    _fromState(state) ||
    _fromQuery(search) ||
    deriveFromPathname(pathname) ||
    fallback ||
    { key: "fallback", label: "Back", path: "/" }
  );
}
