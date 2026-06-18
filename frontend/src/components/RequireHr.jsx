import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { isHr } from "@/lib/hrAuth";
import { usePortalHydration } from "@/lib/usePortalHydration";
import PortalHydratingLoader from "@/components/PortalHydratingLoader";
import { isSignedInAnywhere } from "@/lib/permissions";
import { buildContinuity } from "@/lib/portalContinuity";
import { getMustChange } from "@/lib/mustChangePassword";
import AccessDenied from "@/pages/AccessDenied";

/**
 * RequireHr — gates every /hr/* page (except /hr/login, /hr/forgot,
 * /hr/reset/:token) behind a valid X-HR-Token. HR is an isolated scope:
 * admin tokens do NOT satisfy this guard (admin has its own console).
 *
 * Iter88: if the HR token is missing but the user has a live /sign-in
 * directory session that authorizes HR access, we silently re-mint the
 * HR token instead of bouncing to /hr/login.
 *
 * Iter149: signed-in-elsewhere users see AccessDenied (no jarring
 * login bounce); anonymous users still get the HR login page.
 *
 * Track 15.14A Layer 2: if the user holds a valid HR token but still
 * owes a password rotation, route every non-change-password destination
 * to /hr/change-password. The backend backstop (Layer 3) is the source
 * of truth; this guard is the fast-path so the SPA never even fires a
 * protected fetch.
 */
export function RequireHr({ children }) {
  const location = useLocation();
  const hasToken = isHr();
  const state = usePortalHydration("hr", hasToken);
  if (state === "ready") {
    if (getMustChange("hr") && !/\/hr\/change-password/.test(location.pathname)) {
      return <Navigate to="/hr/change-password" replace />;
    }
    return children;
  }
  if (state === "hydrating") return <PortalHydratingLoader portal="hr" />;
  if (isSignedInAnywhere()) {
    return <AccessDenied attemptedPortal="hr" />;
  }
  return (
    <Navigate
      to="/hr/login"
      replace
      state={{
        from: location.pathname + location.search,
        continuity: buildContinuity(location.pathname + location.search),
      }}
    />
  );
}

export default RequireHr;
