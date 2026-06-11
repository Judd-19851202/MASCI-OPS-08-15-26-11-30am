// directoryAuth.js — Multi-portal master login client lib (iter82)
//
// Stores the directory session token + per-portal tokens issued by
// /api/auth/multi-login. Mirrors the per-portal auth libs (adminAuth.js,
// pmAuth.js, hrAuth.js, shopAuth.js) so the rest of the app can keep
// reading from those — directoryAuth simply WRITES the per-portal token
// stores after a successful multi-login.

import { setAdminToken } from "./adminAuth";
import { setPmToken } from "./pmAuth";
import { setHrToken } from "./hrAuth";
import { setShopToken } from "./shopAuth";
import { setSafetyToken } from "./safetyAuth";
import { setDispatchToken } from "./dispatchAuth";
import { setFlToken } from "./flAuth";

const DIR_TOKEN_KEY = "masci.directory.token";
const DIR_USER_KEY = "masci.directory.user";

export function getDirectoryToken() {
  try {
    return localStorage.getItem(DIR_TOKEN_KEY) || "";
  } catch {
    return "";
  }
}

export function setDirectoryToken(token) {
  try {
    if (token) localStorage.setItem(DIR_TOKEN_KEY, token);
    else localStorage.removeItem(DIR_TOKEN_KEY);
  } catch {
    /* localStorage unavailable — ignore */
  }
}

export function getDirectoryUser() {
  try {
    const raw = localStorage.getItem(DIR_USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function setDirectoryUser(user) {
  try {
    if (user) localStorage.setItem(DIR_USER_KEY, JSON.stringify(user));
    else localStorage.removeItem(DIR_USER_KEY);
  } catch {
    /* ignore */
  }
}

export function clearDirectorySession() {
  setDirectoryToken("");
  setDirectoryUser(null);
}

/**
 * After a successful /api/auth/multi-login response, fan out the issued
 * portal tokens into their respective per-portal auth libs so the rest
 * of the app's existing token-reader middleware "just works" without
 * any code changes.
 *
 * @param {Object} response - the multi-login response body
 * @param {boolean} rememberMe - persistent vs session storage
 */
export function applyMultiLoginResponse(response, rememberMe = true) {
  if (!response?.ok) return;
  setDirectoryToken(response.session_token);
  setDirectoryUser(response.user);
  const t = response.portal_tokens || {};
  // The per-portal token setters have inconsistent signatures: PM/Shop/Admin
  // take an `opts = {}` object while HR takes a plain boolean. Normalize.
  if (t.admin) setAdminToken(t.admin, { remember: rememberMe });
  if (t.pm) setPmToken(t.pm, { remember: rememberMe });
  if (t.shop) setShopToken(t.shop, { remember: rememberMe });
  if (t.hr) setHrToken(t.hr, rememberMe);
  // Phase 5D · P2 closeout — fan out the safety + dispatch tokens that
  // /api/auth/multi-login has been minting since iter120/iter126 but
  // were never persisted on the client. Restores cross-portal continuity
  // for super-admins (and any future multi-portal user) so they don't
  // see "Access Restricted" when navigating across portals from inside
  // operational workflows like the ViewIncident → Follow-Up CAPA CTA.
  if (t.safety) setSafetyToken(t.safety, rememberMe);
  if (t.dispatch) setDispatchToken(t.dispatch, rememberMe);
  // RC-1 Track 2G fix (2026-02-11): fan out Field Leadership portal token.
  // Backend has been minting `portal_tokens.field_leadership` (with `.fl`
  // alias) since iter314 but the frontend never persisted it, so super-
  // admins navigating to `/field-leadership/portal/*` per-user routes
  // hit 401 even though the directory session is otherwise authorized.
  const flToken = t.field_leadership || t.fl;
  if (flToken) setFlToken(flToken, rememberMe);
}

/**
 * Pick the most useful landing page for a directory user based on the
 * portals they have.
 *
 * Iter131: super-admins (anyone holding the admin portal) go straight
 * to /admin — the Hub is a public landing surface, not the workbench.
 * Anyone with exactly one portal lands on that portal. Anyone with
 * multiple non-admin portals lands on the Hub so they can pick.
 */
export function landingFor(user) {
  const portals = user?.portals || [];
  // Super admins → admin console (skip the public hub)
  if (portals.includes("admin")) {
    return "/admin";
  }
  if (portals.length === 1) {
    return (
      {
        pm: "/pm",
        hr: "/hr",
        shop: "/shop",
        safety: "/safety-portal",
        dispatch: "/dispatch-portal",
      }[portals[0]] || "/"
    );
  }
  return "/"; // hub
}
