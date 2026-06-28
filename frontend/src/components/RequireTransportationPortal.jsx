/**
 * TRACK 18.00E-FIX · Transportation Operations Portal access gate.
 *
 * Accepts ANY of the operational portal tokens — admin, dispatch,
 * leadership, safety, pm, hr, shop, fl. Lets the existing Phase A/B/C/D
 * Transportation Operations shell open for a dispatcher logged in via
 * /dispatch-portal/login without bouncing them to the admin gate.
 *
 * RBAC within the shell is still enforced by the backend composer
 * endpoints (Phase C search + Phase D relationships + Track 16.16
 * readiness already key off `_actor`). Workspaces a role cannot
 * reach show a Transportation-branded restricted page — never the
 * legacy admin-strict access-denied page.
 *
 * Doctrine:
 *   - No new auth verb.
 *   - No new token.
 *   - No new collection.
 *   - Existing localStorage tokens reused as-is.
 */
import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { isAdmin } from "@/lib/adminAuth";
import { isDispatch } from "@/lib/dispatchAuth";
import { isSignedInAnywhere } from "@/lib/permissions";
import { buildContinuity } from "@/lib/portalContinuity";

function isAnyTransportationPortal() {
  // Admin and dispatch are the two primary holders. Any other portal
  // token (safety/hr/pm/shop/fl) also unlocks the shell at the route
  // level — backend composers still RBAC-filter what is visible.
  if (isAdmin() || isDispatch()) return true;
  return isSignedInAnywhere();
}

export function RequireTransportationPortal({ children }) {
  const location = useLocation();
  if (isAnyTransportationPortal()) {
    return children;
  }
  // No portal session at all → land at /sign-in with continuity so we
  // return to the requested Transportation Operations route after
  // authentication.
  return (
    <Navigate
      to="/sign-in"
      replace
      state={{
        from: location.pathname + location.search,
        continuity: buildContinuity(location.pathname + location.search),
      }}
    />
  );
}

export default RequireTransportationPortal;
