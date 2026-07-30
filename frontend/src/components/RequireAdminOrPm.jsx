import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { isPm } from "@/lib/pmAuth";
import { isAdmin } from "@/lib/adminAuth";
import { isSignedInAnywhere } from "@/lib/permissions";
import { usePortalHydration } from "@/lib/usePortalHydration";
import PortalHydratingLoader from "@/components/PortalHydratingLoader";
import AccessDenied from "@/pages/AccessDenied";

/**
 * Shared Admin OR PM sub-route guard. Requires an explicit Admin OR PM token.
 *
 * WP-16 Phase 6 fix: This guard now correctly accepts EITHER Admin OR PM tokens.
 * Previously it only checked for PM tokens, causing Admin-only users to see
 * "403 · ACCESS RESTRICTED - You don't have access to PM Portal" on shared routes.
 *
 * Falls back to /pm/login if no token is present (PM is the lower-trust
 * persona, so we route uninvited visitors there).
 *
 * Iter149: signed-in-elsewhere users see AccessDenied instead of a
 * jarring redirect to the PM login screen.
 */
export function RequireAdminOrPm({ children }) {
  const location = useLocation();
  const hasAdminToken = isAdmin();
  const hasPmToken = isPm();
  const hasAccess = hasAdminToken || hasPmToken;
  
  // Use admin hydration if admin token present, otherwise pm
  const hydratePortal = hasAdminToken ? "admin" : "pm";
  const state = usePortalHydration(hydratePortal, hasAccess);
  
  if (state === "ready") return children;
  if (state === "hydrating") return <PortalHydratingLoader portal={hydratePortal} />;
  
  if (!hasAccess) {
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
