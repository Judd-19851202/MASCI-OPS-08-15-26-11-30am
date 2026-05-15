import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { isAdmin } from "@/lib/adminAuth";
import { isPm } from "@/lib/pmAuth";
import { isSignedInAnywhere } from "@/lib/permissions";
import AccessDenied from "@/pages/AccessDenied";

/**
 * Shared sub-route guard for pages that EITHER an Admin OR a PM should
 * be able to view (inspections, equipment, daily reports, jobs master,
 * employees, etc.). The Admin Hub (/admin) and any backup/restore route
 * stay admin-strict via the plain ``RequireAdmin`` guard.
 *
 * Falls back to /pm/login if no token is present (PM is the lower-trust
 * persona, so we route uninvited visitors there).
 *
 * Iter149: signed-in-elsewhere users see AccessDenied instead of a
 * jarring redirect to the PM login screen.
 */
export function RequireAdminOrPm({ children }) {
  const location = useLocation();
  if (!isAdmin() && !isPm()) {
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
