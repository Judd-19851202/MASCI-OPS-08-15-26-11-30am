import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { isAdmin } from "@/lib/adminAuth";
import { isPm } from "@/lib/pmAuth";
import { usePortalHydration } from "@/lib/usePortalHydration";
import PortalHydratingLoader from "@/components/PortalHydratingLoader";

/**
 * Wrap any PM-portal route. Accepts EITHER a valid admin token OR a valid
 * PM token (admin should be able to view anything a PM can view, but the
 * PM portal also needs its own dedicated entry point with the strict-admin
 * controls — backups, restore, force-reseed — hidden from view).
 *
 * Iter88: if neither token is present but the user has a live /sign-in
 * directory session that authorizes PM access, we silently re-mint the
 * PM token instead of bouncing to /pm/login.
 */
export function RequirePm({ children }) {
  const location = useLocation();
  const hasToken = isPm() || isAdmin();
  const state = usePortalHydration("pm", hasToken);
  if (state === "ready") return children;
  if (state === "hydrating") return <PortalHydratingLoader portal="pm" />;
  return (
    <Navigate
      to="/pm/login"
      replace
      state={{ from: location.pathname + location.search }}
    />
  );
}

export default RequirePm;
