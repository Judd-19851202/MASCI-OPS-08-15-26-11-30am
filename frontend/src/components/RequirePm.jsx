import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { isPm } from "@/lib/pmAuth";
import { usePortalHydration } from "@/lib/usePortalHydration";
import PortalHydratingLoader from "@/components/PortalHydratingLoader";
import { isSignedInAnywhere } from "@/lib/permissions";
import { buildContinuity } from "@/lib/portalContinuity";
import { getMustChange } from "@/lib/mustChangePassword";
import AccessDenied from "@/pages/AccessDenied";

/**
 * Wrap any PM-portal route. Requires an explicit PM token.
 *
 * Iter88: if neither token is present but the user has a live /sign-in
 * directory session that authorizes PM access, we silently re-mint the
 * PM token instead of bouncing to /pm/login.
 *
 * Iter149: signed-in-elsewhere users see AccessDenied; anonymous users
 * are bounced to /pm/login as before.
 */
export function RequirePm({ children }) {
  const location = useLocation();
  const hasToken = isPm();
  const state = usePortalHydration("pm", hasToken);
  if (state === "ready") {
    if (getMustChange("pm") && !/\/pm\/change-password/.test(location.pathname)) {
      return <Navigate to="/pm/change-password" replace />;
    }
    return children;
  }
  if (state === "hydrating") return <PortalHydratingLoader portal="pm" />;
  if (isSignedInAnywhere()) {
    return <AccessDenied attemptedPortal="pm" />;
  }
  return (
    <Navigate
      to="/pm/login"
      replace
      state={{
        from: location.pathname + location.search,
        continuity: buildContinuity(location.pathname + location.search),
      }}
    />
  );
}

export default RequirePm;
