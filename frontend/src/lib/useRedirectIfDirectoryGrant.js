// useRedirectIfDirectoryGrant.js — TRACK 14.0-SSO (2026-02-15)
//
// Hook for portal login pages (SafetyLogin, PmLogin, HrLogin,
// ShopLogin, DispatchLogin). When the user navigates to a per-portal
// login form while ALREADY holding a valid directory session that
// grants this portal, we silently mint the portal token and forward
// them into the portal — no redundant login form, no friction.
//
// Behavior:
//   1. If the per-portal token is already present → redirect to
//      `destination` immediately (preserves the existing behavior of
//      every portal login page's "already signed in" useEffect).
//   2. Else if directory session present AND grant includes this
//      portal → POST /auth/issue-portal-token, fan out token, then
//      redirect to `destination`.
//   3. Else → render the login form as normal (no redirect).
//
// Hard rules respected (per user's Option A directive):
//   • Does NOT mint tokens the user is not granted.
//   • Does NOT bypass the backend's role gate (server still validates
//     the directory session and the requested portal grant on
//     /api/auth/issue-portal-token).
//   • Does NOT duplicate stale tokens — the backend is the source of
//     truth for whether the portal is currently authorized.

import { useEffect, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { getDirectoryUser, getDirectoryToken } from "@/lib/directoryAuth";
import { api } from "@/lib/api";
import { setAdminToken } from "@/lib/adminAuth";
import { setPmToken } from "@/lib/pmAuth";
import { setShopToken } from "@/lib/shopAuth";
import { setHrToken } from "@/lib/hrAuth";
import { setSafetyToken } from "@/lib/safetyAuth";
import { setDispatchToken } from "@/lib/dispatchAuth";
import { setFlToken } from "@/lib/flAuth";

const SETTERS = {
  admin: (t) => setAdminToken(t, { remember: true }),
  pm: (t) => setPmToken(t, { remember: true }),
  shop: (t) => setShopToken(t, { remember: true }),
  hr: (t) => setHrToken(t, true),
  safety: (t) => setSafetyToken(t, true),
  dispatch: (t) => setDispatchToken(t, true),
  field_leadership: (t) => setFlToken(t, true),
};

const PORTAL_ALIASES = {
  fl: "field_leadership",
  field_leadership: "field_leadership",
  leadership: "field_leadership",
  admin: "admin",
  pm: "pm",
  shop: "shop",
  hr: "hr",
  safety: "safety",
  dispatch: "dispatch",
};

/**
 * Auto-mint + redirect when the user already holds a directory grant
 * for this portal. Safe no-op for everyone else.
 *
 * @param {string} portal - "admin" | "pm" | "shop" | "hr" | "safety" | "dispatch" | "field_leadership"
 * @param {boolean} hasToken - synchronous result of the existing isX() check
 * @param {string} destination - route to forward to once the token is in place
 */
export function useRedirectIfDirectoryGrant(portal, hasToken, destination) {
  const nav = useNavigate();
  const location = useLocation();
  const ran = useRef(false);

  useEffect(() => {
    if (ran.current) return;
    // Honor the existing portal-token short-circuit first.
    if (hasToken) {
      ran.current = true;
      const intended = location.state?.continuity?.continueTo
        || location.state?.from
        || destination;
      nav(intended, { replace: true });
      return;
    }
    // Otherwise check the directory session.
    const dirToken = getDirectoryToken();
    const dirUser = getDirectoryUser();
    if (!dirToken || !dirUser || !Array.isArray(dirUser.portals)) return;
    const canonical = PORTAL_ALIASES[portal] || portal;
    const granted = dirUser.portals.includes(canonical) || dirUser.portals.includes(portal);
    if (!granted) return;
    ran.current = true;
    let cancelled = false;
    (async () => {
      try {
        const r = await api.post(
          "/auth/issue-portal-token",
          { portal: canonical },
          { headers: { "X-Directory-Token": dirToken }, skipSessionStatus: true }
        );
        if (cancelled) return;
        if (r?.data?.ok && r.data.token) {
          const setter = SETTERS[portal] || SETTERS[canonical];
          if (setter) setter(r.data.token);
          const intended = location.state?.continuity?.continueTo
            || location.state?.from
            || destination;
          nav(intended, { replace: true });
        }
      } catch {
        // Silent — fall through to render the login form. The user
        // simply lost their session somewhere and needs to sign in
        // again. The login form is the correct UX here.
      }
    })();
    return () => { cancelled = true; };
     
  }, [hasToken]);
}

export default useRedirectIfDirectoryGrant;
