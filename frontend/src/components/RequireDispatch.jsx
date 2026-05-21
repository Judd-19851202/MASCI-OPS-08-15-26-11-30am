// RequireDispatch — gate every /dispatch-portal/* page (except login)
// behind a valid X-Dispatch-Token. Mirrors RequireSafety.
//
// Iter149: signed-in-elsewhere users see AccessDenied; anonymous users
// still get bounced to the dispatch login page.
import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { isDispatch } from "@/lib/dispatchAuth";
import { isSignedInAnywhere } from "@/lib/permissions";
import { buildContinuity } from "@/lib/portalContinuity";
import AccessDenied from "@/pages/AccessDenied";

export function RequireDispatch({ children }) {
  const location = useLocation();
  if (isDispatch()) return children;
  if (isSignedInAnywhere()) {
    return <AccessDenied attemptedPortal="dispatch" />;
  }
  return (
    <Navigate
      to="/dispatch-portal/login"
      replace
      state={{
        from: location.pathname + location.search,
        continuity: buildContinuity(location.pathname + location.search),
      }}
    />
  );
}

export default RequireDispatch;
