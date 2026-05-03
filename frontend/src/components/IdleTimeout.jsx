import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { clearAdminToken, getAdminToken } from "@/lib/adminAuth";
import { clearPmToken, getPmToken } from "@/lib/pmAuth";
import { clearShopToken, getShopToken } from "@/lib/shopAuth";

/**
 * IdleTimeout — auto-logout after 20 minutes of inactivity inside any
 * staff portal (/admin/*, /pm/*, /shop/*).
 *
 * Pairs with EnforcePortalScope:
 *   • EnforcePortalScope wipes the token the moment the user leaves
 *     the portal namespace (URL-based).
 *   • IdleTimeout wipes the token after IDLE_MS of zero pointer /
 *     keyboard / scroll / touch activity (time-based).
 *
 * Together they cover both an active "leave the portal" event and a
 * passive "walked away from the desk" event — defence-in-depth for
 * shared office computers.
 *
 * Notes:
 *   • Public surfaces (Hub home, Field, /cheatsheet, etc.) have no
 *     token to wipe, so the timer simply doesn't arm there.
 *   • The dev portal (/dev) is intentionally untouched — same rule as
 *     EnforcePortalScope.
 *   • Listeners are passive so they don't interfere with native
 *     scroll / wheel inertia.
 *   • Tick interval is 30 s, not per-event — keeps CPU near zero on
 *     long-running tabs.
 */
const IDLE_MS = 20 * 60 * 1000; // 20 minutes
const TICK_MS = 30 * 1000; // poll every 30 s
const ACTIVITY_EVENTS = [
  "mousemove",
  "mousedown",
  "keydown",
  "scroll",
  "touchstart",
  "wheel",
];

function inScope(pathname, prefix) {
  return pathname === prefix || pathname.startsWith(`${prefix}/`);
}

function activePortal(pathname) {
  if (inScope(pathname, "/admin") && getAdminToken()) {
    return { kind: "admin", clear: clearAdminToken, login: "/admin/login" };
  }
  if (inScope(pathname, "/pm") && getPmToken()) {
    return { kind: "pm", clear: clearPmToken, login: "/pm/login" };
  }
  if (inScope(pathname, "/shop") && getShopToken()) {
    return { kind: "shop", clear: clearShopToken, login: "/shop/login" };
  }
  return null;
}

export default function IdleTimeout() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const deadlineRef = React.useRef(0);

  React.useEffect(() => {
    const portal = activePortal(pathname);
    if (!portal) return undefined;

    deadlineRef.current = Date.now() + IDLE_MS;

    const bump = () => {
      deadlineRef.current = Date.now() + IDLE_MS;
    };

    ACTIVITY_EVENTS.forEach((ev) =>
      window.addEventListener(ev, bump, { passive: true }),
    );

    const interval = setInterval(() => {
      if (Date.now() < deadlineRef.current) return;
      // Idle fired — tear down + sign out + bounce to login.
      clearInterval(interval);
      ACTIVITY_EVENTS.forEach((ev) => window.removeEventListener(ev, bump));
      portal.clear();
      toast.error("Signed out after 20 minutes of inactivity", {
        description: "Sign back in to continue.",
        duration: 6000,
      });
      navigate(portal.login, { replace: true });
    }, TICK_MS);

    return () => {
      clearInterval(interval);
      ACTIVITY_EVENTS.forEach((ev) => window.removeEventListener(ev, bump));
    };
  }, [pathname, navigate]);

  return null;
}
