// RequireSafety — gate every /safety-portal/* page (except login,
// forgot, reset) behind a valid X-Safety-Token. Mirrors RequireHr.
//
// Iter149: when the user is signed into a DIFFERENT portal (not Safety),
// render AccessDenied instead of bouncing to the Safety login screen —
// less jarring, clearer mental model.
import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { isSafety } from "@/lib/safetyAuth";
import { isSignedInAnywhere } from "@/lib/permissions";
import AccessDenied from "@/pages/AccessDenied";

export function RequireSafety({ children }) {
  const location = useLocation();
  if (isSafety()) return children;
  if (isSignedInAnywhere()) {
    return <AccessDenied attemptedPortal="safety" />;
  }
  return (
    <Navigate
      to="/safety-portal/login"
      replace
      state={{ from: location.pathname + location.search }}
    />
  );
}

export default RequireSafety;
