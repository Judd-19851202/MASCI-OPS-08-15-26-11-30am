import React from "react";
import { useLocation } from "react-router-dom";
import { clearAdminToken, getAdminToken } from "@/lib/adminAuth";
import { clearPmToken, getPmToken } from "@/lib/pmAuth";
import { clearShopToken, getShopToken } from "@/lib/shopAuth";
import { clearHrToken, getHrToken } from "@/lib/hrAuth";
import { clearSafetyToken, getSafetyToken } from "@/lib/safetyAuth";
import { clearDispatchToken, getDispatchToken } from "@/lib/dispatchAuth";
import { getDirectoryUser } from "@/lib/directoryAuth";

/**
 * EnforcePortalScope — controlled token cleanup as the user navigates.
 *
 * Iter149 revision (Phase 2.5 — role/permission refinement):
 *   The previous policy cleared a portal token the moment the user
 *   left that portal's URL namespace. That was too aggressive — it
 *   stranded users on AccessDenied pages (because their "home portal"
 *   token was wiped during the cross-portal nav). It also made the
 *   "switch portals" experience hostile.
 *
 *   New policy: clear a portal's token ONLY when the user explicitly
 *   navigates to a DIFFERENT portal's LOGIN page (a strong signal that
 *   they intend to sign into something else). Anything else preserves
 *   the token so:
 *     • Cross-portal AccessDenied can render with a valid "Back to
 *       your portal" CTA.
 *     • The Hub home WelcomeBack strip stays accurate.
 *     • Refresh / browser back stops randomly logging users out.
 *
 *   Multi-portal directory sessions still bypass clearing — same as
 *   the prior implementation.
 */
const LOGIN_PATHS = {
  admin: "/admin/login",
  pm: "/pm/login",
  shop: "/shop/login",
  hr: "/hr/login",
  safety: "/safety-portal/login",
  dispatch: "/dispatch-portal/login",
};

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

    // Only clear when the user lands on a DIFFERENT portal's login
    // page — a clean "I'm signing into something else" intent. Any
    // other navigation (cross-portal browsing, hub home, deep links,
    // refresh, drilling into shared docs) preserves the existing
    // portal token so AccessDenied can render the correct "back to
    // your portal" CTA.
    const PAIRS = [
      { has: getAdminToken,    clear: clearAdminToken,    own: "admin"    },
      { has: getPmToken,       clear: clearPmToken,       own: "pm"       },
      { has: getShopToken,     clear: clearShopToken,     own: "shop"     },
      { has: getHrToken,       clear: clearHrToken,       own: "hr"       },
      { has: getSafetyToken,   clear: clearSafetyToken,   own: "safety"   },
      { has: getDispatchToken, clear: clearDispatchToken, own: "dispatch" },
    ];

    for (const { has, clear, own } of PAIRS) {
      if (!has()) continue;
      if (dirHas(own)) continue;
      // Is the current path a login page belonging to a portal OTHER
      // than `own`? If so, the user is explicitly signing in
      // somewhere else — clear the old token.
      const isOtherLogin = Object.entries(LOGIN_PATHS)
        .some(([portal, path]) => portal !== own && pathname === path);
      if (isOtherLogin) clear();
    }
  }, [pathname]);

  return null;
}
