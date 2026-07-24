import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { isPm } from "@/lib/pmAuth";
import { isSignedInAnywhere } from "@/lib/permissions";
import { usePortalHydration } from "@/lib/usePortalHydration";
import PortalHydratingLoader from "@/components/PortalHydratingLoader";
import AccessDenied from "@/pages/AccessDenied";

/**
 * Shared PM sub-route guard. Requires an explicit PM token.
 *
 * Falls back to /pm/login if no token is present (PM is the lower-trust
 * persona, so we route uninvited visitors there).
 *
 * Iter149: signed-in-elsewhere users see AccessDenied instead of a
 * jarring redirect to the PM login screen.
 */
export function RequireAdminOrPm({ children }) {
  const location = useLocation();
  const state = usePortalHydration("pm", isPm());
  if (state === "ready") return children;
  if (state === "hydrating") return <PortalHydratingLoader portal="pm" />;
  if (!isPm()) {
    if (isSignedInAnywhere()) {
      return <AccessDenied attemptedPortal="pm" />;
    }
    return (
      <Navigate
        to="/pm/login"
        replace
        state={{ from: location.pathname + location.search }}
      />
    );
  }
  return children;
}

export default RequireAdminOrPm;
