// RequireDispatch — gate every /dispatch-portal/* page (except login)
// behind a valid X-Dispatch-Token. Mirrors RequireSafety.
import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { isDispatch } from "@/lib/dispatchAuth";

export function RequireDispatch({ children }) {
  const location = useLocation();
  if (isDispatch()) return children;
  return (
    <Navigate
      to="/dispatch-portal/login"
      replace
      state={{ from: location.pathname + location.search }}
    />
  );
}

export default RequireDispatch;
