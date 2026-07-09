// TRACK 25 · SPRINT 1 · Legacy hub switcher retired.
// AdminHubSwitcher flipped between AdminHubV2 and AdminHubV3 behind
// the masci.admin.nav.v3 feature flag. Both destinations are now
// consolidated into the canonical Admin Operating System at /admin
// (AdminOS.jsx). Any residual link or lazy-import to this file now
// redirects there immediately.
import React from "react";
import { Navigate } from "react-router-dom";

export default function AdminHubSwitcher() {
  return (
    <Navigate
      to="/admin"
      replace
      data-testid="admin-hub-switcher-legacy-redirect"
    />
  );
}
