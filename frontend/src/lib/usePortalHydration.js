// usePortalHydration.js — iter88
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
// This closes the race where MultiPortalHydrator hasn't re-issued the
// token yet but the user just navigated to /hr (or /pm, /shop). Instead
// of bouncing to /hr/login we hold the route for ~200-500ms while the
// token is silently re-issued, then render the destination.

import { useEffect, useRef, useState } from "react";
import { getDirectoryUser, getDirectoryToken } from "@/lib/directoryAuth";
import { api } from "@/lib/api";
import { setAdminToken } from "@/lib/adminAuth";
import { setPmToken } from "@/lib/pmAuth";
import { setShopToken } from "@/lib/shopAuth";
import { setHrToken } from "@/lib/hrAuth";

const SETTERS = {
  admin: (t) => setAdminToken(t, { remember: true }),
  pm: (t) => setPmToken(t, { remember: true }),
  shop: (t) => setShopToken(t, { remember: true }),
  hr: (t) => setHrToken(t, true),
};

/**
 * @param {string} portal - "admin" | "pm" | "shop" | "hr"
 * @param {boolean} hasToken - synchronous result of the existing isX() check
 * @returns {"ready" | "hydrating" | "deny"}
 */
export function usePortalHydration(portal, hasToken) {
  const [state, setState] = useState(() => {
    if (hasToken) return "ready";
    const dirToken = getDirectoryToken();
    const dirUser = getDirectoryUser();
    const authorized =
      dirToken &&
      dirUser &&
      Array.isArray(dirUser.portals) &&
      dirUser.portals.includes(portal);
    return authorized ? "hydrating" : "deny";
  });
  const ranOnce = useRef(false);

  useEffect(() => {
    if (state !== "hydrating" || ranOnce.current) return;
    ranOnce.current = true;
    const dirToken = getDirectoryToken();
    if (!dirToken) {
      setState("deny");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const r = await api.post(
          "/auth/issue-portal-token",
          { portal },
          { headers: { "X-Directory-Token": dirToken } }
        );
        if (cancelled) return;
        if (r?.data?.ok && r.data.token) {
          SETTERS[portal](r.data.token);
          setState("ready");
        } else {
          setState("deny");
        }
      } catch {
        if (!cancelled) setState("deny");
      }
    })();
    return () => { cancelled = true; };
  }, [state, portal]);

  // When `hasToken` flips true due to an outside setter, jump to ready.
  useEffect(() => {
    if (hasToken && state !== "ready") setState("ready");
  }, [hasToken, state]);

  return state;
}
