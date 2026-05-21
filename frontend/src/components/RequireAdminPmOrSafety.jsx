// RequireAdminPmOrSafety — iter322 closure.
//
// Bounded role expansion for the four Safety review **detail** views:
//   /admin/inspections/:id
//   /admin/meetings/:id
//   /admin/incidents/:id
//   (jhas detail uses the JHP admin page, not a Safety detail view)
//
// The list pages live under /safety-portal/* and are already gated by
// RequireSafety. The detail views, however, live under /admin/* and
// are wrapped by RequireAdminOrPm. That guard rejects Safety tokens
// and renders AccessDenied — the "wrong-role" message operators saw
// when clicking through from /safety-portal/audits or /incidents.
//
// This guard accepts Admin · PM · Safety. RBAC posture is unchanged
// for write/delete (backend stays on require_admin). Read-only detail
// view is widened to Safety in keeping with the iter322 backend gate.
//
// No other surface uses this guard. Mirror of RequireAdminOrPm shape.
import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { isAdmin } from "@/lib/adminAuth";
import { isPm } from "@/lib/pmAuth";
import { isSafety } from "@/lib/safetyAuth";
import { isSignedInAnywhere } from "@/lib/permissions";
import AccessDenied from "@/pages/AccessDenied";

export function RequireAdminPmOrSafety({ children }) {
  const location = useLocation();
  if (isAdmin() || isPm() || isSafety()) return children;
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

export default RequireAdminPmOrSafety;
