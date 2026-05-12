import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { isHr } from "@/lib/hrAuth";

/**
 * RequireHr — gates every /hr/* page (except /hr/login, /hr/forgot,
 * /hr/reset/:token) behind a valid X-HR-Token in localStorage or
 * sessionStorage. HR is an isolated scope: admin tokens do NOT satisfy
 * this guard (admin has its own console). HR users authenticate
 * explicitly via /hr/login.
 */
export function RequireHr({ children }) {
  const location = useLocation();
  if (!isHr()) {
    return (
      <Navigate
        to="/hr/login"
        replace
        state={{ from: location.pathname + location.search }}
      />
    );
  }
  return children;
}

export default RequireHr;
