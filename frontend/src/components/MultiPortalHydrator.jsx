// MultiPortalHydrator.jsx — iter88 self-healing layer
//
// Purpose: keep every per-portal token (admin / pm / shop / hr) in sync
// with the directory session for users who have multiple portals. If any
// portal token goes missing — but the directory session is alive and
// the user is authorized for that portal — silently call
// POST /api/auth/issue-portal-token to re-mint it.
//
// This component runs once at app boot AND any time the directory user
// or the route changes. It exists so the multi-portal experience is
// bulletproof against stale-bundle cache issues, localStorage corruption,
// or any other state where the per-portal tokens get wiped without the
// directory session also being wiped. As long as the directory session
// is alive, every authorized portal should always be one tab-switch
// away — never a re-login.
//
// Mounted globally in App.js. Renders nothing.

import React, { useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";
import { getDirectoryUser, getDirectoryToken } from "@/lib/directoryAuth";
import { getAdminToken, setAdminToken } from "@/lib/adminAuth";
import { getPmToken, setPmToken } from "@/lib/pmAuth";
import { getShopToken, setShopToken } from "@/lib/shopAuth";
import { getHrToken, setHrToken } from "@/lib/hrAuth";
import { api } from "@/lib/api";

const TOKEN_GETTERS = {
  admin: getAdminToken,
  pm: getPmToken,
  shop: getShopToken,
  hr: getHrToken,
};

const TOKEN_SETTERS_REMEMBER = {
  // PM/Shop/Admin take an opts object; HR takes a plain boolean.
  admin: (t) => setAdminToken(t, { remember: true }),
  pm: (t) => setPmToken(t, { remember: true }),
  shop: (t) => setShopToken(t, { remember: true }),
  hr: (t) => setHrToken(t, true),
};

export default function MultiPortalHydrator() {
  const { pathname } = useLocation();
  const inflight = useRef(new Set());

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const dirToken = getDirectoryToken();
      const dirUser = getDirectoryUser();
      if (!dirToken || !dirUser) return;
      const authorized = Array.isArray(dirUser.portals) ? dirUser.portals : [];
      if (!authorized.length) return;
      for (const portal of authorized) {
        if (cancelled) break;
        const getter = TOKEN_GETTERS[portal];
        const setter = TOKEN_SETTERS_REMEMBER[portal];
        if (!getter || !setter) continue;
        if (getter()) continue; // already present
        if (inflight.current.has(portal)) continue;
        inflight.current.add(portal);
        try {
          const r = await api.post(
            "/auth/issue-portal-token",
            { portal },
            { headers: { "X-Directory-Token": dirToken } }
          );
          if (!cancelled && r?.data?.ok && r.data.token) {
            setter(r.data.token);
          }
        } catch (err) {
          // Common failures:
          //   401 → directory session expired (user signed out elsewhere)
          //   403 → portal no longer authorized
          //   network → preview cold-start; retry on next route change
          if (err?.response?.status === 401) {
            // Stop trying — directory session is dead. Other components
            // (PortalSwitcher, RequireX) will surface a clean re-login.
            break;
          }
        } finally {
          inflight.current.delete(portal);
        }
      }
    })();
    return () => { cancelled = true; };
  }, [pathname]);

  return null;
}
