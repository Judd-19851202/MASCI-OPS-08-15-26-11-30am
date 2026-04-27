import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/lib/authContext";
import { Loader2 } from "lucide-react";

/**
 * Guard for /app routes. Redirects to /app/login when not authed.
 * When user.must_change_password is true, forces /app/change-password
 * before anything else.
 */
export function RequireUser({ children, requireRole }) {
  const { user } = useAuth();
  const loc = useLocation();

  if (user === undefined) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <Loader2 className="w-6 h-6 animate-spin text-red-700" />
      </div>
    );
  }
  if (user === null) {
    return <Navigate to="/app/login" replace state={{ from: loc.pathname }} />;
  }
  if (user.must_change_password && loc.pathname !== "/app/change-password") {
    return <Navigate to="/app/change-password" replace />;
  }
  if (requireRole && !requireRole.includes(user.role)) {
    return <Navigate to="/app" replace />;
  }
  return children;
}
