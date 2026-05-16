import React from "react";
import { useLocation } from "react-router-dom";
import { clearAdminToken, getAdminToken } from "@/lib/adminAuth";
import { clearPmToken, getPmToken } from "@/lib/pmAuth";
import { clearShopToken, getShopToken } from "@/lib/shopAuth";
import { clearHrToken, getHrToken } from "@/lib/hrAuth";
import { clearSafetyToken, getSafetyToken } from "@/lib/safetyAuth";
import { clearDispatchToken, getDispatchToken } from "@/lib/dispatchAuth";
import { getDirectoryUser } from "@/lib/directoryAuth";
import { clearAllSessions } from "@/lib/sessionReset";

/**
 * EnforcePortalScope — controlled token cleanup as the user navigates.
 *
 * Iter149: clear a portal's token only when the user explicitly
 * navigates to a DIFFERENT portal's login page. Anything else
 * preserves the token so cross-portal AccessDenied pages can still
 * render a "Back to your portal" CTA.
 *
 * Iter179 (P0 access-control hardening): landing on ANY login page
 * (per-portal OR /sign-in) is an explicit "I am switching identity"
 * signal. We now wipe EVERY auth artifact on that entry — including
 * the multi-portal directory session + every other-portal token +
 * per-portal user objects. Previously only the current portal's
 * tokens were cleared which left a stale super-admin
 * `masci.directory.user` in localStorage, so PortalSwitcher rendered
 * an Admin Console link inside the next user's HR/Shop/PM portal.
 *
 * Multi-portal directory sessions still bypass the legacy
 * cross-portal clearing logic (so users with multiple portals can
 * freely navigate between them once signed in via /sign-in).
 */
const LOGIN_PATHS = {
  admin: "/admin/login",
  pm: "/pm/login",
  shop: "/shop/login",
  hr: "/hr/login",
  safety: "/safety-portal/login",
  dispatch: "/dispatch-portal/login",
};

// Every path on which a fresh login form is rendered. Landing on any
// of these is an explicit identity switch — wipe stale auth state.
const ALL_LOGIN_PATHS = [
  ...Object.values(LOGIN_PATHS),
  "/sign-in",
  "/safety/forms/login",
  "/dev/login",
];

function authorizedPortals() {
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
    // P0 (iter179) — landing on any login page = explicit identity
    // switch. Nuke everything BEFORE the user types creds so a stale
    // multi-portal directory session can't survive into the next
    // login. notifyBackend=false because we may be wiping a session
    // we don't own (e.g. someone else's previously-signed-in browser
    // tab on a shared device).
    if (ALL_LOGIN_PATHS.includes(pathname)) {
      clearAllSessions({ notifyBackend: false });
      return;
    }

    const dirPortals = authorizedPortals();
    const dirHas = (p) => Array.isArray(dirPortals) && dirPortals.includes(p);

    const PAIRS = [
      { has: getAdminToken,    clear: clearAdminToken,    own: "admin"    },
      { has: getPmToken,       clear: clearPmToken,       own: "pm"       },
      { has: getShopToken,     clear: clearShopToken,     own: "shop"     },
      { has: getHrToken,       clear: clearHrToken,       own: "hr"       },
      { has: getSafetyToken,   clear: clearSafetyToken,   own: "safety"   },
      { has: getDispatchToken, clear: clearDispatchToken, own: "dispatch" },
    ];

    // Legacy cross-portal clearing — kept for parity with iter149
    // behavior. Only triggers when the user lands on a login page
    // other than their own AND they don't hold a multi-portal
    // directory grant for that portal.
    for (const { has, clear, own } of PAIRS) {
      if (!has()) continue;
      if (dirHas(own)) continue;
      const isOtherLogin = Object.entries(LOGIN_PATHS)
        .some(([portal, path]) => portal !== own && pathname === path);
      if (isOtherLogin) clear();
    }
  }, [pathname]);

  return null;
}
