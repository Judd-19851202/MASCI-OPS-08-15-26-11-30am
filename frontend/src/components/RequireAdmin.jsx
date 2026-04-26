import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { isAdmin } from "@/lib/adminAuth";

/**
 * Wrap any admin-only route. If no admin token is set, the user is
 * redirected to /admin/login with the original path captured so we can
 * bounce them back after a successful login.
 *
 *   <Route path="/admin/inspections" element={
 *     <RequireAdmin><InspectionsDashboard /></RequireAdmin>
 *   } />
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
