// sessionReset.js — Phase K · P0 Access-Control Hardening (iter179)
//
// One-shot wipe of every auth artifact in the browser. Used by every
// portal "Sign out" button AND by every portal login page on mount.
// This closes the iter179 P0 leak: previously, signing out of one
// portal left the multi-portal `masci.directory.user` and other-portal
// tokens in localStorage, so the very next per-portal login inherited
// a stale super-admin directory session and PortalSwitcher would
// render an "Admin Console" link.
//
// Defense in depth:
//   • Every token store is cleared (admin/pm/shop/hr/safety/dispatch/dev).
//   • The directory token + directory user object are cleared.
//   • Per-portal user objects (masci.hr.user, masci.shop.user, etc.)
//     are cleared so identity-derived UI doesn't leak the prior user.
//   • Server-side `/api/auth/multi-logout` is called best-effort to
//     invalidate the directory session row server-side.
//
// IMPORTANT: This module owns ONLY auth + identity keys. It does NOT
// touch operational localStorage (drafts, queues, ops escalations,
// device id, posthog distinct id). Those are intentionally preserved
// across logins so resiliency / analytics state isn't lost.

import { clearAdminToken, getAdminToken } from "./adminAuth";
import { clearPmToken, getPmToken } from "./pmAuth";
import { clearShopToken, getShopToken } from "./shopAuth";
import { clearHrToken, getHrToken } from "./hrAuth";
import { clearSafetyToken, getSafetyToken } from "./safetyAuth";
import { clearDispatchToken, getDispatchToken } from "./dispatchAuth";
import { clearDevToken } from "./devAuth";
import { clearFlToken, getFlToken } from "./flAuth";
import { clearLeadershipToken, getLeadershipToken } from "./leadershipAuth";
import { clearSafetyFormsToken, getSafetyFormsToken } from "./safetyFormsAuth";
import { clearJwt } from "./jwtAuth";
import { clearDriverSession } from "./driverAuth";
import {
  clearDirectorySession,
  getDirectoryToken,
} from "./directoryAuth";

// All identity-derived localStorage / sessionStorage keys that any
// portal authentication writes. Kept narrow on purpose — operational
// keys (drafts, queues, ops_*, device id, posthog) are NOT included.
const IDENTITY_KEYS = [
  // Multi-portal directory session
  "masci.directory.token",
  "masci.directory.user",
  // Per-portal user identity objects (the tokens are wiped by their
  // own clear helpers below, but the user objects need explicit kills
  // so PortalSwitcher / WelcomeBack / role-aware UI cannot read them).
  "masci.hr.user",
  "masci.shop.user",
  "masci.pm.user",
  "masci.safety.user",
  "masci.dispatch.user",
  "masci.admin.user",
  "masci.fl.user",
  "masci.leadership.token",
  "masci.leadership.issued",
  "masci.driver.token",
  "masci.driver.session",
  "masci.driver.tenant",
  "masci.is_asset_admin",
  "admin_must_change_password",
  "pm_must_change_password",
  "shop_must_change_password",
  "hr_must_change_password",
  "safety_must_change_password",
  "dispatch_must_change_password",
  "field_leadership_must_change_password",
  "fl_must_change_password",
  "directory_must_change_password",
  // Safety-forms standalone auth (separate from safety portal)
  "masci.safetyforms.token",
  "masci.safetyforms.user",
];

const API = (process.env.REACT_APP_BACKEND_URL || "").replace(/\/$/, "");

/**
 * Wipe every auth artifact from this browser. Returns a promise so
 * callers can `await` the server-side multi-logout before redirecting.
 *
 * @param {Object} [opts]
 * @param {boolean} [opts.notifyBackend=true] — when true, fire
 *   `/api/auth/multi-logout` so the directory session row is killed
 *   server-side. Set false in pre-login bootstrapping (no need to
 *   ping a session we may not even own).
 */
export async function clearAllSessions({ notifyBackend = true } = {}) {
  const dirTok = (() => {
    try {
      return getDirectoryToken();
    } catch {
      return "";
    }
  })();
  const adminTok = (() => {
    try { return getAdminToken(); } catch { return ""; }
  })();
  const pmTok = (() => {
    try { return getPmToken(); } catch { return ""; }
  })();
  const shopTok = (() => {
    try { return getShopToken(); } catch { return ""; }
  })();
  const hrTok = (() => {
    try { return getHrToken(); } catch { return ""; }
  })();
  const safetyTok = (() => {
    try { return getSafetyToken(); } catch { return ""; }
  })();
  const dispatchTok = (() => {
    try { return getDispatchToken(); } catch { return ""; }
  })();
  const flTok = (() => {
    try { return getFlToken(); } catch { return ""; }
  })();
  const leadershipTok = (() => {
    try { return getLeadershipToken(); } catch { return ""; }
  })();
  const safetyFormsTok = (() => {
    try { return getSafetyFormsToken(); } catch { return ""; }
  })();

  // Local wipe FIRST. We must not depend on the network call to
  // succeed before clearing in-browser state — a flaky/offline browser
  // must still end up logged out.
  try { clearAdminToken(); } catch { /* ignore */ }
  try { clearPmToken(); } catch { /* ignore */ }
  try { clearShopToken(); } catch { /* ignore */ }
  try { clearHrToken(); } catch { /* ignore */ }
  try { clearSafetyToken(); } catch { /* ignore */ }
  try { clearDispatchToken(); } catch { /* ignore */ }
  try { clearFlToken(); } catch { /* ignore */ }
  try { clearLeadershipToken(); } catch { /* ignore */ }
  try { clearDevToken(); } catch { /* ignore */ }
  try { clearSafetyFormsToken(); } catch { /* ignore */ }
  try { clearJwt(); } catch { /* ignore */ }
  try { clearDriverSession(); } catch { /* ignore */ }
  try { clearDirectorySession(); } catch { /* ignore */ }

  for (const key of IDENTITY_KEYS) {
    try { localStorage.removeItem(key); } catch { /* ignore */ }
    try { sessionStorage.removeItem(key); } catch { /* ignore */ }
  }

  // Best-effort server-side invalidation. Failures here are non-fatal:
  // we already cleared the client. A 401/network error simply means
  // we logged out a session that was already gone.
  if (
    notifyBackend
    && API
    && (dirTok || adminTok || pmTok || shopTok || hrTok || safetyTok || dispatchTok || flTok || leadershipTok || safetyFormsTok)
  ) {
    try {
      const headers = {
        "Content-Type": "application/json",
        ...(dirTok ? { "X-Directory-Token": dirTok } : {}),
        ...(adminTok ? { "X-Admin-Token": adminTok } : {}),
        ...(pmTok ? { "X-PM-Token": pmTok } : {}),
        ...(shopTok ? { "X-Shop-Token": shopTok } : {}),
        ...(hrTok ? { "X-HR-Token": hrTok } : {}),
        ...(safetyTok ? { "X-Safety-Token": safetyTok } : {}),
        ...(dispatchTok ? { "X-Dispatch-Token": dispatchTok } : {}),
        ...(flTok ? { "X-FL-Token": flTok } : {}),
        ...(leadershipTok ? { "X-Leadership-Token": leadershipTok } : {}),
        ...(safetyFormsTok ? { "X-Safety-Forms-Token": safetyFormsTok } : {}),
      };
      await fetch(`${API}/api/auth/multi-logout`, {
        method: "POST",
        headers,
        cache: "no-store",
      });
    } catch {
      /* offline / network error — local wipe already done, safe */
    }
  }
}
