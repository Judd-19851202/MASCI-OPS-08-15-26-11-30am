// TRACK 25 · SPRINT 1 · Legacy hub retired.
// The classic tile-grid /admin console has been consolidated into the
// canonical Admin Operating System landing at /admin (AdminOS.jsx · 10
// operational domains · live endpoints · SideNavV3). Any residual link
// or lazy-import to this file now redirects there immediately so no
// operator ever lands on a deprecated dashboard. Bookmarks are
// preserved: /admin/hub_v1 (Route in AppRoutes) also Navigate's here.
import React from "react";
import { Navigate } from "react-router-dom";

export default function AdminHub() {
  return (
    <Navigate
      to="/admin"
      replace
      data-testid="admin-hub-legacy-redirect"
    />
  );
}
