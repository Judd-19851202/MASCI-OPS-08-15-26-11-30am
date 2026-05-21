import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { isAdmin } from "@/lib/adminAuth";
import { usePortalHydration } from "@/lib/usePortalHydration";
import PortalHydratingLoader from "@/components/PortalHydratingLoader";
import { isSignedInAnywhere } from "@/lib/permissions";
import { buildContinuity } from "@/lib/portalContinuity";
import AccessDenied from "@/pages/AccessDenied";

/**
 * Admin-strict guard. Used on /admin (the hub page itself) and any other
 * route that exposes backup/restore controls. PMs are NOT admitted here —
 * they have their own /pm hub and use ``RequireAdminOrPm`` on shared
 * sub-routes (inspections, equipment, etc.).
 *
 * Iter88: if the admin token is missing but the user has a live
 * /sign-in directory session that authorizes admin access, we silently
 * re-mint the token via /api/auth/issue-portal-token instead of
 * bouncing to /admin/login (closes the multi-portal race).
 */
export function RequireAdmin({ children }) {
  const location = useLocation();
  const hasToken = isAdmin();
  const state = usePortalHydration("admin", hasToken);
  if (state === "ready") return children;
  if (state === "hydrating") return <PortalHydratingLoader portal="admin" />;
  if (isSignedInAnywhere()) {
    return <AccessDenied attemptedPortal="admin" />;
  }
  return (
    <Navigate
      to="/admin/login"
      replace
      state={{
        from: location.pathname + location.search,
        continuity: buildContinuity(location.pathname + location.search),
      }}
    />
  );
}

export default RequireAdmin;
