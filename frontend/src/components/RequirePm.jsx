import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { isAdmin } from "@/lib/adminAuth";
import { isPm } from "@/lib/pmAuth";

/**
 * Wrap any PM-portal route. Accepts EITHER a valid admin token OR a valid
 * PM token (admin should be able to view anything a PM can view, but the
 * PM portal also needs its own dedicated entry point with the strict-admin
 * controls — backups, restore, force-reseed — hidden from view).
 *
 * If no token is set, the user is redirected to /pm/login with the
 * original path captured so we can bounce them back after a successful
 * login.
 */
export function RequirePm({ children }) {
  const location = useLocation();
  if (!isPm() && !isAdmin()) {
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

export default RequirePm;
