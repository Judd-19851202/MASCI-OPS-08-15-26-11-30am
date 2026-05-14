// RequireSafety — gate every /safety-portal/* page (except login,
// forgot, reset) behind a valid X-Safety-Token. Mirrors RequireHr.
import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { isSafety } from "@/lib/safetyAuth";

export function RequireSafety({ children }) {
  const location = useLocation();
  if (isSafety()) return children;
  return (
    <Navigate
      to="/safety-portal/login"
      replace
      state={{ from: location.pathname + location.search }}
    />
  );
}

export default RequireSafety;
