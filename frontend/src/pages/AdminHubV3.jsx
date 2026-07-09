// TRACK 25 · SPRINT 1 · Legacy hub retired.
// AdminHubV3 was the "Executive Home" flag-gated landing. Consolidated
// into the canonical Admin Operating System at /admin (AdminOS.jsx).
// Any residual link or lazy-import to this file now redirects there
// immediately.
import React from "react";
import { Navigate } from "react-router-dom";

export default function AdminHubV3() {
  return (
    <Navigate
      to="/admin"
      replace
      data-testid="admin-hub-v3-legacy-redirect"
    />
  );
}
