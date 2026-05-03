import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { clearAdminToken, getAdminToken } from "@/lib/adminAuth";
import { clearPmToken, getPmToken } from "@/lib/pmAuth";
import { clearShopToken, getShopToken } from "@/lib/shopAuth";

/**
 * IdleTimeout — auto-logout after 20 minutes of inactivity inside any
 * staff portal (/admin/*, /pm/*, /shop/*), with a 1-minute warning
 * toast at the 19-minute mark so an admin reading a long PDF gets one
 * click to extend the session instead of being booted mid-read.
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
const WARN_BEFORE_MS = 60 * 1000; // show "60 sec to logout" warning at 19:00
const TICK_MS = 30 * 1000; // poll every 30 s
const ACTIVITY_EVENTS = [
  "mousemove",
  "mousedown",
  "keydown",
  "scroll",
  "touchstart",
  "wheel",
];
const WARN_TOAST_ID = "masci-idle-warn";

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
  const warnShownRef = React.useRef(false);

  React.useEffect(() => {
    const portal = activePortal(pathname);
    if (!portal) return undefined;

    deadlineRef.current = Date.now() + IDLE_MS;
    warnShownRef.current = false;

    const bump = () => {
      deadlineRef.current = Date.now() + IDLE_MS;
      // Any activity also dismisses an already-shown warning toast and
      // resets the warn-flag so it can fire again on the next idle run.
      if (warnShownRef.current) {
        warnShownRef.current = false;
        toast.dismiss(WARN_TOAST_ID);
      }
    };

    ACTIVITY_EVENTS.forEach((ev) =>
      window.addEventListener(ev, bump, { passive: true }),
    );

    const interval = setInterval(() => {
      const now = Date.now();
      const msLeft = deadlineRef.current - now;

      // 19-min mark: 1-minute warning with a "Stay signed in" action.
      if (
        msLeft > 0 &&
        msLeft <= WARN_BEFORE_MS &&
        !warnShownRef.current
      ) {
        warnShownRef.current = true;
        toast.warning("Signing you out in 60 seconds", {
          id: WARN_TOAST_ID,
          description:
            "20 minutes of inactivity. Click below to stay signed in.",
          duration: WARN_BEFORE_MS, // toast lives until logout would fire
          action: {
            label: "Stay signed in",
            onClick: () => bump(),
          },
        });
        return;
      }

      if (msLeft > 0) return;

      // 20-min mark: tear down + sign out + bounce to login.
      clearInterval(interval);
      ACTIVITY_EVENTS.forEach((ev) => window.removeEventListener(ev, bump));
      toast.dismiss(WARN_TOAST_ID);
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
      toast.dismiss(WARN_TOAST_ID);
    };
  }, [pathname, navigate]);

  return null;
}
