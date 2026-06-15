import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { isFl } from "@/lib/flAuth";
import { usePortalHydration } from "@/lib/usePortalHydration";
import PortalHydratingLoader from "@/components/PortalHydratingLoader";
import { isSignedInAnywhere } from "@/lib/permissions";
import { buildContinuity } from "@/lib/portalContinuity";
import AccessDenied from "@/pages/AccessDenied";

/**
 * RequireFl — gates Field Leadership Portal pages behind a valid
 * X-FL-Token. iter314 governed per-user identity, distinct from the
 * legacy `/field-leadership/login` shared-password gate.
 *
 * TRACK 14.0-SSO (2026-02-15): now uses usePortalHydration so a user
 * with an active directory session that grants field_leadership access
 * gets the FL token silently minted on-demand. Also adds the
 * AccessDenied branch so signed-in-elsewhere users see a clean
 * "you don't have access" card instead of a confusing FL login form.
 */
export function RequireFl({ children }) {
  const location = useLocation();
  const hasToken = isFl();
  const state = usePortalHydration("field_leadership", hasToken);
  if (state === "ready") return children;
  if (state === "hydrating") return <PortalHydratingLoader portal="field_leadership" />;
  if (isSignedInAnywhere()) {
    return <AccessDenied attemptedPortal="field_leadership" />;
  }
  return (
    <Navigate
      to="/field-leadership/portal/login"
      replace
      state={{
        from: location.pathname + location.search,
        continuity: buildContinuity(location.pathname + location.search),
      }}
    />
  );
}

export default RequireFl;
