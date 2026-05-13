import React from "react";
import { useLocation } from "react-router-dom";
import { clearAdminToken, getAdminToken } from "@/lib/adminAuth";
import { clearPmToken, getPmToken } from "@/lib/pmAuth";
import { clearShopToken, getShopToken } from "@/lib/shopAuth";
import { clearHrToken, getHrToken } from "@/lib/hrAuth";
import { getDirectoryUser } from "@/lib/directoryAuth";

/**
 * EnforcePortalScope — auto-logout when an authenticated SINGLE-portal
 * user navigates AWAY from their portal's URL namespace.
 *
 * Iter86 update — multi-portal awareness:
 *   When the user signed in through /sign-in (the master directory),
 *   their localStorage contains a `masci.directory.user` record with a
 *   `portals` array. Tokens for portals listed in that array are NEVER
 *   wiped while navigating between portals — that's the whole point of
 *   the master sign-in. Only tokens for portals NOT in the directory
 *   portals array (or single-portal direct-login sessions) follow the
 *   original sandbox rule.
 *
 * Original sandbox rule (still applies to non-directory sessions):
 *   • Admin token is cleared when pathname leaves `/admin/*`.
 *   • PM token is cleared when pathname leaves `/pm/*`.
 *   • Shop token is cleared when pathname leaves `/shop/*`.
 *   • HR token is cleared when pathname leaves `/hr/*`.
 *
 * Multi-audience exemptions (apply regardless of directory status):
 *   • `/training/*` — shared training surface
 *   • `/` — Hub home; serves the WelcomeBack strip
 */
function inScope(pathname, prefix) {
  if (pathname === prefix || pathname.startsWith(`${prefix}/`)) return true;
  if (pathname === "/training" || pathname.startsWith("/training/")) return true;
  if (pathname === "/") return true;
  return false;
}

function authorizedPortals() {
  // Returns the array of portals the master-directory session authorizes,
  // or null when the user is in a single-portal direct-login session.
  try {
    const user = getDirectoryUser();
    if (!user) return null;
    const portals = Array.isArray(user.portals) ? user.portals : null;
    return portals && portals.length ? portals : null;
  } catch {
    return null;
  }
}

export default function EnforcePortalScope() {
  const { pathname } = useLocation();

  React.useEffect(() => {
    const dirPortals = authorizedPortals();
    const dirHas = (p) => Array.isArray(dirPortals) && dirPortals.includes(p);

    if (getAdminToken() && !inScope(pathname, "/admin") && !dirHas("admin")) {
      clearAdminToken();
    }
    if (getPmToken() && !inScope(pathname, "/pm") && !dirHas("pm")) {
      clearPmToken();
    }
    if (getShopToken() && !inScope(pathname, "/shop") && !dirHas("shop")) {
      clearShopToken();
    }
    if (getHrToken() && !inScope(pathname, "/hr") && !dirHas("hr")) {
      clearHrToken();
    }
  }, [pathname]);

  return null;
}
