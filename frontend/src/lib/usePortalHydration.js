// usePortalHydration.js — iter88 + TRACK 14.0-SSO (2026-02-15)
//
// Hook that asks: "should this RequireX guard render its children,
// bounce to a login page, or show a brief loader while we re-issue a
// missing portal token?"
//
// Decision tree:
//   1. If the per-portal token already exists → "ready" (render children).
//   2. If no directory session → "deny" (bounce to login as before).
//   3. If directory session exists AND user.portals includes this portal →
//      synchronously fire /api/auth/issue-portal-token and return "hydrating"
//      until the response lands. Then "ready" or "deny" depending on outcome.
//   4. Otherwise → "deny".
//
// TRACK 14.0-SSO (2026-02-15): Extended SETTERS to cover safety,
// dispatch, and field_leadership (alias fl). Previously these three
// portals lacked a hydration setter, so even though the backend
// minted their portal_tokens during /api/auth/multi-login, a user
// arriving at a /safety-portal/* or /dispatch-portal/* route via
// direct URL was bounced to the portal-specific login form despite
// holding a valid directory session — the exact "feels like seven
// disconnected apps" symptom users reported.
//
// This closes the race where MultiPortalHydrator hasn't re-issued the
// token yet but the user just navigated to /hr (or /pm, /shop, /safety-
// portal, /dispatch-portal, /field-leadership/portal). Instead of
// bouncing to the portal login we hold the route for ~200-500ms while
// the token is silently re-issued, then render the destination.

import { useEffect, useRef, useState } from "react";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import { getDirectoryUser, getDirectoryToken } from "@/lib/directoryAuth";
import { api } from "@/lib/api";
import { setAdminToken } from "@/lib/adminAuth";
import { setPmToken } from "@/lib/pmAuth";
import { setShopToken } from "@/lib/shopAuth";
import { setHrToken } from "@/lib/hrAuth";
import { setSafetyToken } from "@/lib/safetyAuth";
import { setDispatchToken } from "@/lib/dispatchAuth";
import { setFlToken } from "@/lib/flAuth";

const HYDRATION_TIMEOUT_MS = 5000;

const SETTERS = {
  admin: (t) => setAdminToken(t, { remember: true }),
  pm: (t) => setPmToken(t, { remember: true }),
  shop: (t) => setShopToken(t, { remember: true }),
  hr: (t) => setHrToken(t, true),
  // TRACK 14.0-SSO additions.
  safety: (t) => setSafetyToken(t, true),
  dispatch: (t) => setDispatchToken(t, true),
  field_leadership: (t) => setFlToken(t, true),
  // Alias — some callers / route guards reference the portal as `fl`.
  fl: (t) => setFlToken(t, true),
};

// TRACK 14.0-SSO · Some portals are stored under one canonical name
// in the directory.user.portals array (e.g. "field_leadership") but
// referenced by route guards under a shorter alias ("fl"). Map both
// directions so the grant check below resolves whichever spelling
// the caller used.
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

function _hasGrant(dirUser, portal) {
  if (!dirUser || !Array.isArray(dirUser.portals)) return false;
  const canonical = PORTAL_ALIASES[portal] || portal;
  return dirUser.portals.includes(canonical) || dirUser.portals.includes(portal);
}

/**
 * @param {string} portal - "admin" | "pm" | "shop" | "hr" | "safety" | "dispatch" | "field_leadership" | "fl"
 * @param {boolean} hasToken - synchronous result of the existing isX() check
 * @returns {"ready" | "hydrating" | "deny"}
 */
export function usePortalHydration(portal, hasToken) {
  const [state, setState] = useState(() => {
    if (hasToken) return "ready";
    const dirToken = getDirectoryToken();
    const dirUser = getDirectoryUser();
    const authorized = dirToken && _hasGrant(dirUser, portal);
    return authorized ? "hydrating" : "deny";
  });
  const ranOnce = useRef(false);

  useEffect(() => {
    if (state !== "hydrating" || ranOnce.current) return;
    ranOnce.current = true;
    const dirToken = getDirectoryToken();
    const dirUser = getDirectoryUser();
    if (!dirToken) {
      setState("deny");
      return;
    }
    if (!_hasGrant(dirUser, portal)) {
      setState("deny");
      return;
    }
    let cancelled = false;
    const timeoutId = window.setTimeout(() => {
      if (!cancelled) setState("deny");
    }, HYDRATION_TIMEOUT_MS);
    (async () => {
      try {
        // TRACK 14.0-SSO · Resolve the alias to the canonical portal
        // name the backend expects in the /issue-portal-token payload.
        const canonical = PORTAL_ALIASES[portal] || portal;
        const r = await api.post(
          "/auth/issue-portal-token",
          { portal: canonical },
          { headers: buildScopedPortalAuthHeaders(["directory"]), skipSessionStatus: true }
        );
        if (cancelled) return;
        if (r?.data?.ok && r.data.token) {
          const setter = SETTERS[portal] || SETTERS[canonical];
          if (setter) setter(r.data.token);
          clearTimeout(timeoutId);
          setState("ready");
        } else {
          clearTimeout(timeoutId);
          setState("deny");
        }
      } catch (err) {
        clearTimeout(timeoutId);
        if (!cancelled) {
          if (Number(err?.response?.status || 0) === 401) setState("deny");
          else setState("deny");
        }
      }
    })();
    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
  }, [state, portal]);

  // Anti-hang (CRITICAL): the guard must NEVER remain in "hydrating" forever.
  // A re-entry after ranOnce, or a child 401 that clears the freshly-issued
  // token, previously left an untimed spinner. This absolute deadline forces a
  // governed "deny" (login bounce / AccessDenied) so the user always reaches a
  // resolvable state.
  useEffect(() => {
    if (state !== "hydrating") return undefined;
    const hardId = window.setTimeout(() => setState("deny"), HYDRATION_TIMEOUT_MS + 1500);
    return () => window.clearTimeout(hardId);
  }, [state]);

  // If a just-issued portal token is immediately rejected/cleared (child gets
  // 401 -> interceptor clears it -> hasToken flips false after we reached
  // "ready"), surface a governed denial. Debounced so the normal handshake
  // window (parent `hasToken` prop catching up right after issue-portal-token)
  // does not trip it.
  useEffect(() => {
    if (state !== "ready" || hasToken) return undefined;
    const id = window.setTimeout(() => setState("deny"), 1200);
    return () => window.clearTimeout(id);
  }, [state, hasToken]);

  // When `hasToken` flips true due to an outside setter, jump to ready.
  useEffect(() => {
    if (hasToken && state !== "ready") setState("ready");
  }, [hasToken, state]);

  return state;
}
