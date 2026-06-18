// RequireSafety — gate every /safety-portal/* page (except login,
// forgot, reset) behind a valid X-Safety-Token. Mirrors RequireHr.
//
// Iter149: when the user is signed into a DIFFERENT portal (not Safety),
// render AccessDenied instead of bouncing to the Safety login screen —
// less jarring, clearer mental model.
//
// TRACK 14.0-SSO (2026-02-15): now uses usePortalHydration so a user
// with an active directory session that grants Safety access gets the
// Safety token silently minted on-demand — no portal login form, no
// "feels like seven apps" friction. Mirrors RequireHr / RequirePm /
// RequireShop / RequireAdmin behavior.
import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { isSafety } from "@/lib/safetyAuth";
import { usePortalHydration } from "@/lib/usePortalHydration";
import PortalHydratingLoader from "@/components/PortalHydratingLoader";
import { isSignedInAnywhere } from "@/lib/permissions";
import { buildContinuity } from "@/lib/portalContinuity";
import { getMustChange } from "@/lib/mustChangePassword";
import AccessDenied from "@/pages/AccessDenied";

export function RequireSafety({ children }) {
  const location = useLocation();
  const hasToken = isSafety();
  const state = usePortalHydration("safety", hasToken);
  if (state === "ready") {
    if (getMustChange("safety") && !/\/safety-portal\/change-password/.test(location.pathname)) {
      return <Navigate to="/safety-portal/change-password" replace />;
    }
    return children;
  }
  if (state === "hydrating") return <PortalHydratingLoader portal="safety" />;
  if (isSignedInAnywhere()) {
    return <AccessDenied attemptedPortal="safety" />;
  }
  const intended = location.pathname + location.search;
  return (
    <Navigate
      to="/safety-portal/login"
      replace
      state={{
        from: intended,
        // iter322-B · rich continuity descriptor for AuthRequiredBanner
        continuity: buildContinuity(intended),
      }}
    />
  );
}

export default RequireSafety;
