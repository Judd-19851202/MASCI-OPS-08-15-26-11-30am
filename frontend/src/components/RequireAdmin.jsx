import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { isAdmin } from "@/lib/adminAuth";

/**
 * Admin-strict guard. Used on /admin (the hub page itself) and any other
 * route that exposes backup/restore controls. PMs are NOT admitted here —
 * they have their own /pm hub and use ``RequireAdminOrPm`` on shared
 * sub-routes (inspections, equipment, etc.).
 */
export function RequireAdmin({ children }) {
  const location = useLocation();
  if (!isAdmin()) {
    return (
      <Navigate
        to="/admin/login"
        replace
        state={{ from: location.pathname + location.search }}
      />
    );
  }
  return children;
}

export default RequireAdmin;
