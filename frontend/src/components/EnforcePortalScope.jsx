import React from "react";
import { useLocation } from "react-router-dom";
import { clearAdminToken, getAdminToken } from "@/lib/adminAuth";
import { clearPmToken, getPmToken } from "@/lib/pmAuth";
import { clearShopToken, getShopToken } from "@/lib/shopAuth";
import { clearHrToken, getHrToken } from "@/lib/hrAuth";

/**
 * EnforcePortalScope — auto-logout when an authenticated user navigates
 * AWAY from their portal's URL namespace.
 *
 * Behaviour:
 *   • Admin token is cleared the moment the pathname leaves `/admin/*`.
 *   • PM token is cleared the moment the pathname leaves `/pm/*`.
 *   • Shop token is cleared the moment the pathname leaves `/shop/*`.
 *
 * This is a deliberate session-tightening: each portal is its own
 * sandbox. Once you step out, you have to re-authenticate to come
 * back. Same rule for all 3 portals.
 *
 * Multi-audience exemption:
 *   The Training Hub at `/training/*` is a deliberately shared surface —
 *   PMs / Admins / Shop staff all need to access training packets and
 *   videos while signed into their own portal (clicking the "PM
 *   Training" tile from the landing page is the canonical flow). To
 *   prevent the scope check from wiping a freshly-issued PM/Shop/Admin
 *   token the moment React Router lands on `/training/pm` after a
 *   successful login, training routes are explicitly in-scope for
 *   every portal. Per-track audience gating still happens inside the
 *   training page itself (see `TrainingTrack.jsx`).
 *
 * Notes:
 *   • Login pages (`/admin/login`, `/pm/login`, `/shop/login`) are
 *     inside their own portal namespace, so visiting them does not
 *     wipe a token (and a fresh login at the login page works the same
 *     way it always did).
 *   • `localStorage` is shared across browser tabs, so opening a
 *     non-portal route in a new tab will also wipe the source tab's
 *     session — that's intentional per the spec.
 *   • Dev portal (`/dev`) is left untouched — that's a vendor-internal
 *     surface and was never part of the staff portal model.
 */
function inScope(pathname, prefix) {
  // Allow the bare prefix `/admin` or any sub-path `/admin/*`. Reject
  // look-alikes like `/admin-something`.
  if (pathname === prefix || pathname.startsWith(`${prefix}/`)) return true;
  // Multi-audience training surface — never wipes any portal token.
  if (pathname === "/training" || pathname.startsWith("/training/")) return true;
  return false;
}

export default function EnforcePortalScope() {
  const { pathname } = useLocation();

  React.useEffect(() => {
    if (getAdminToken() && !inScope(pathname, "/admin")) {
      clearAdminToken();
    }
    if (getPmToken() && !inScope(pathname, "/pm")) {
      clearPmToken();
    }
    if (getShopToken() && !inScope(pathname, "/shop")) {
      clearShopToken();
    }
    if (getHrToken() && !inScope(pathname, "/hr")) {
      clearHrToken();
    }
  }, [pathname]);

  return null;
}
