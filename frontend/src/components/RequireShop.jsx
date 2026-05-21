import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { isShop } from "@/lib/shopAuth";
import { isAdmin } from "@/lib/adminAuth";
import { usePortalHydration } from "@/lib/usePortalHydration";
import PortalHydratingLoader from "@/components/PortalHydratingLoader";
import { isSignedInAnywhere } from "@/lib/permissions";
import { buildContinuity } from "@/lib/portalContinuity";
import AccessDenied from "@/pages/AccessDenied";

/**
 * Allows the route through if the user holds EITHER a shop token or an
 * admin token (admin can see everything the shop sees).
 *
 * Iter88: if neither token is present but the user has a live /sign-in
 * directory session that authorizes Shop access, we silently re-mint
 * the Shop token instead of bouncing to /shop/login.
 *
 * Iter149: signed-in-elsewhere users see AccessDenied; anonymous users
 * are bounced to the Shop login page as before.
 */
export function RequireShop({ children }) {
  const location = useLocation();
  const hasToken = isShop() || isAdmin();
  const state = usePortalHydration("shop", hasToken);
  if (state === "ready") return children;
  if (state === "hydrating") return <PortalHydratingLoader portal="shop" />;
  if (isSignedInAnywhere()) {
    return <AccessDenied attemptedPortal="shop" />;
  }
  return (
    <Navigate
      to="/shop/login"
      replace
      state={{
        from: location.pathname + location.search,
        continuity: buildContinuity(location.pathname + location.search),
      }}
    />
  );
}

export default RequireShop;
