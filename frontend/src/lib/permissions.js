// permissions.js — Iter149 (Phase 2.5). Single source of truth for
// role / portal access logic. Used by route guards, the Hub home tile
// filter, PortalSwitcher, and the AccessDenied page.
//
// Design constraints (per user mandate):
//   * simple, predictable, consistent, role-based, scalable.
//   * NO permission spaghetti. Roles are CANONICAL portal names.
//   * Admin acts as super-role for read access (admin token also
//     satisfies Admin-or-PM gates server-side; admin DOES NOT
//     transparently satisfy /hr, /shop, /safety, /dispatch — those
//     are isolated by mandate).
//   * Per-portal token in localStorage is the source of truth for a
//     "signed-in to portal X" claim. Multi-portal users have a
//     directory session that lists `portals: []` — that array is the
//     authoritative list of portals the user CAN reach via switcher.

import { getAdminToken } from "@/lib/adminAuth";
import { getPmToken } from "@/lib/pmAuth";
import { getShopToken } from "@/lib/shopAuth";
import { getHrToken } from "@/lib/hrAuth";
import { getSafetyToken } from "@/lib/safetyAuth";
import { getDispatchToken } from "@/lib/dispatchAuth";
import { isFl } from "@/lib/flAuth";
import { isLeadershipAuthed } from "@/lib/leadershipAuth";
import { getDirectoryToken, getDirectoryUser } from "@/lib/directoryAuth";

// Canonical portal keys (order = preference for "home portal" detection)
export const PORTALS = ["admin", "hr", "safety", "pm", "shop", "dispatch", "leadership"];

export const PORTAL_LABEL = {
  admin: "Admin Console",
  pm: "PM Portal",
  shop: "Shop Console",
  hr: "HR Portal",
  safety: "Safety Portal",
  dispatch: "Dispatch Portal",
  leadership: "Field Leadership",
};

export const PORTAL_HOME = {
  admin: "/admin",
  pm: "/pm",
  shop: "/shop",
  hr: "/hr",
  safety: "/safety-portal",
  dispatch: "/dispatch-portal",
  leadership: "/leadership",
};

export const PORTAL_LOGIN = {
  admin: "/admin/login",
  pm: "/pm/login",
  shop: "/shop/login",
  hr: "/hr/login",
  safety: "/safety-portal/login",
  dispatch: "/dispatch-portal/login",
  leadership: "/leadership",
};

// Token presence probes, keyed by portal.
const TOKEN_PROBES = {
  admin: () => !!getAdminToken(),
  pm: () => !!getPmToken(),
  shop: () => !!getShopToken(),
  hr: () => !!getHrToken(),
  safety: () => !!getSafetyToken(),
  dispatch: () => !!getDispatchToken(),
  leadership: () => isLeadershipAuthed() || isFl(),
};

/**
 * Returns the list of portals the current browser session is signed
 * into RIGHT NOW (token actually present). Order follows PORTALS.
 */
export function activePortals() {
  return PORTALS.filter((p) => {
    try { return TOKEN_PROBES[p]?.() === true; } catch { return false; }
  });
}

/**
 * Returns the list of portals the user is AUTHORIZED to access via
 * the directory multi-portal session, OR the singletoken portals
 * they're actively signed into. Union — gives the widest set so we
 * can render switcher / hub tiles correctly.
 */
export function authorizedPortals() {
  const dir = getDirectoryUser();
  const hasDirectorySession = !!getDirectoryToken();
  const fromDirectory = hasDirectorySession && Array.isArray(dir?.portals) ? dir.portals : [];
  const active = activePortals();
  return Array.from(new Set([...fromDirectory, ...active]));
}

export function assignedPortals() {
  const dir = getDirectoryUser();
  return Array.isArray(dir?.portals) ? Array.from(new Set(dir.portals)) : [];
}

export function reachablePortals() {
  return authorizedPortals();
}

/**
 * The "home portal" for the current session — the first portal
 * (by preference order) we have an active token for. Returns null
 * when no portal is signed in. Used to redirect from AccessDenied
 * back to a sensible default.
 */
export function homePortal() {
  const active = activePortals();
  return active[0] || null;
}

/**
 * True iff the current session can reach the given portal — either
 * through a live token OR through the directory's authorized list.
 */
export function canAccessPortal(portal) {
  if (!portal) return false;
  return reachablePortals().includes(portal);
}

/**
 * True iff the user has ANY portal session live or directory access.
 * Distinguishes "fully signed-out anonymous" from "signed-in but on
 * wrong portal" — the AccessDenied page treats these two cases
 * differently.
 */
export function isSignedInAnywhere() {
  return authorizedPortals().length > 0;
}

/**
 * Resolve the URL of the user's "best" home portal, falling back
 * to "/" for fully anonymous users. Useful for "Return to your
 * portal" buttons on AccessDenied.
 */
export function homePortalUrl() {
  const h = homePortal();
  return h ? PORTAL_HOME[h] : "/";
}
