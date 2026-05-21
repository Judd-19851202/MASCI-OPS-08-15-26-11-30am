import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { isFl } from "@/lib/flAuth";

/**
 * RequireFl — gates Field Leadership Portal pages behind a valid
 * X-FL-Token. iter314 governed per-user identity, distinct from the
 * legacy `/field-leadership/login` shared-password gate.
 */
export function RequireFl({ children }) {
  const location = useLocation();
  if (isFl()) return children;
  return (
    <Navigate
      to="/field-leadership/portal/login"
      replace
      state={{ from: location.pathname + location.search }}
    />
  );
}

export default RequireFl;
