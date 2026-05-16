// Validate any locally-stored auth tokens on app load.
//
// Why this exists:
//   `isAdmin()` / `isPm()` / `isShop()` / `isDev()` only check whether a
//   token STRING exists in localStorage — they do not verify the backend
//   still accepts it. When passwords get rotated or the HMAC secret
//   changes, a user's old token stops working server-side but the
//   frontend still thinks they're signed in. On the Training Hub this
//   means the Shop/PM/Admin tiles render as "unlocked" (OPEN TRACK)
//   even though every gated request will 401.
//
// This module fires one ping per stored token at startup. If the
// backend returns 401 we nuke the stale token so the UI reflects the
// real auth state (locked tiles, password-required messaging, etc.).

import { getAdminToken, clearAdminToken } from "./adminAuth";
import { getPmToken, clearPmToken } from "./pmAuth";
import { getShopToken, clearShopToken } from "./shopAuth";
import { getDevToken, clearDevToken } from "./devAuth";
import { getHrToken, clearHrToken } from "./hrAuth";
import { getSafetyToken, clearSafetyToken } from "./safetyAuth";
import { getDispatchToken, clearDispatchToken } from "./dispatchAuth";
import { getDirectoryToken, clearDirectorySession } from "./directoryAuth";

const API = (process.env.REACT_APP_BACKEND_URL || "").replace(/\/$/, "");

// Returns `true` if the backend accepts the token, `false` only on 401.
// Network errors are treated as "accept" so we never nuke a good token
// just because the user briefly went offline.
async function accepts(path, header, token) {
  if (!token) return true;
  try {
    const res = await fetch(`${API}${path}`, {
      method: "GET",
      headers: { [header]: token },
      // Critical: auth check must bypass any HTTP cache. Otherwise a
      // previously-cached 200 (from before a password rotation) will
      // mask a real 401 and we'll never clear the stale token.
      cache: "no-store",
    });
    return res.status !== 401;
  } catch {
    return true;
  }
}

export async function validateStoredTokens() {
  const results = await Promise.all([
    accepts("/api/admin/check", "X-Admin-Token", getAdminToken()).then(
      (v) => ({ kind: "admin", valid: v }),
    ),
    accepts("/api/pm/check", "X-PM-Token", getPmToken()).then((v) => ({
      kind: "pm",
      valid: v,
    })),
    accepts("/api/shop/check", "X-Shop-Token", getShopToken()).then((v) => ({
      kind: "shop",
      valid: v,
    })),
    accepts("/api/dev/check", "X-Dev-Token", getDevToken()).then((v) => ({
      kind: "dev",
      valid: v,
    })),
    accepts("/api/hr/me", "X-HR-Token", getHrToken()).then((v) => ({
      kind: "hr",
      valid: v,
    })),
    accepts("/api/safety/me", "X-Safety-Token", getSafetyToken()).then((v) => ({
      kind: "safety",
      valid: v,
    })),
    accepts("/api/dispatch/me", "X-Dispatch-Token", getDispatchToken()).then((v) => ({
      kind: "dispatch",
      valid: v,
    })),
    // P0 (iter179) — also validate the multi-portal directory session.
    // If the backend rejects the directory token, clear the directory
    // session entirely (token + cached user) so PortalSwitcher can't
    // render a stale portals list inside a freshly-logged-in user's
    // per-portal session.
    accepts("/api/auth/me-directory", "X-Directory-Token", getDirectoryToken()).then((v) => ({
      kind: "directory",
      valid: v,
    })),
  ]);

  let cleared = false;
  for (const r of results) {
    if (r.valid) continue;
    if (r.kind === "admin") clearAdminToken();
    else if (r.kind === "pm") clearPmToken();
    else if (r.kind === "shop") clearShopToken();
    else if (r.kind === "dev") clearDevToken();
    else if (r.kind === "hr") clearHrToken();
    else if (r.kind === "safety") clearSafetyToken();
    else if (r.kind === "dispatch") clearDispatchToken();
    else if (r.kind === "directory") clearDirectorySession();
    cleared = true;
  }
  return cleared;
}
