// RequireDispatch — gate every /dispatch-portal/* page (except login)
// behind a valid X-Dispatch-Token. Mirrors RequireSafety.
//
// Iter149: signed-in-elsewhere users see AccessDenied; anonymous users
// still get bounced to the dispatch login page.
//
// TRACK 14.0-SSO (2026-02-15): now uses usePortalHydration so a user
// with an active directory session that grants Dispatch access gets
// the Dispatch token silently minted on-demand.
import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { isDispatch } from "@/lib/dispatchAuth";
import { usePortalHydration } from "@/lib/usePortalHydration";
import PortalHydratingLoader from "@/components/PortalHydratingLoader";
import { isSignedInAnywhere } from "@/lib/permissions";
import { buildContinuity } from "@/lib/portalContinuity";
import { getMustChange } from "@/lib/mustChangePassword";
import AccessDenied from "@/pages/AccessDenied";

export function RequireDispatch({ children }) {
  const location = useLocation();
  const hasToken = isDispatch();
  const state = usePortalHydration("dispatch", hasToken);
  if (state === "ready") {
    if (getMustChange("dispatch") && !/\/dispatch-portal\/change-password/.test(location.pathname)) {
      return <Navigate to="/dispatch-portal/change-password" replace />;
    }
    return children;
  }
  if (state === "hydrating") return <PortalHydratingLoader portal="dispatch" />;
  if (isSignedInAnywhere()) {
    return <AccessDenied attemptedPortal="dispatch" />;
  }
  return (
    <Navigate
      to="/dispatch-portal/login"
      replace
      state={{
        from: location.pathname + location.search,
        continuity: buildContinuity(location.pathname + location.search),
      }}
    />
  );
}

export default RequireDispatch;
