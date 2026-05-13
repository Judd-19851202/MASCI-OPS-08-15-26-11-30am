import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { isHr } from "@/lib/hrAuth";
import { usePortalHydration } from "@/lib/usePortalHydration";
import PortalHydratingLoader from "@/components/PortalHydratingLoader";

/**
 * RequireHr — gates every /hr/* page (except /hr/login, /hr/forgot,
 * /hr/reset/:token) behind a valid X-HR-Token. HR is an isolated scope:
 * admin tokens do NOT satisfy this guard (admin has its own console).
 *
 * Iter88: if the HR token is missing but the user has a live /sign-in
 * directory session that authorizes HR access, we silently re-mint the
 * HR token instead of bouncing to /hr/login.
 */
export function RequireHr({ children }) {
  const location = useLocation();
  const hasToken = isHr();
  const state = usePortalHydration("hr", hasToken);
  if (state === "ready") return children;
  if (state === "hydrating") return <PortalHydratingLoader portal="hr" />;
  return (
    <Navigate
      to="/hr/login"
      replace
      state={{ from: location.pathname + location.search }}
    />
  );
}

export default RequireHr;
