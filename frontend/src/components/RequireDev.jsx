import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { isDev } from "@/lib/devAuth";

/**
 * Wrap any Developer-portal route. Only a valid DEV token grants access —
 * admin and PM tokens are explicitly rejected so vendor-internal surfaces
 * (Ops Manual, snapshots) stay hidden from MASCI staff.
 */
export function RequireDev({ children }) {
  const location = useLocation();
  if (!isDev()) {
    return (
      <Navigate
        to="/dev/login"
        replace
        state={{ from: location.pathname + location.search }}
      />
    );
  }
  return children;
}

export default RequireDev;
