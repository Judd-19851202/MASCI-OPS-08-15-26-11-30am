// TRACK 25 · SPRINT 1 · Legacy hub retired.
// AdminHubV2 was the Operations-Control-Center preview landing. It has
// been consolidated into the canonical Admin Operating System at
// /admin (AdminOS.jsx). Any residual link or lazy-import to this file
// now redirects there immediately so no operator ever lands on a
// deprecated dashboard. Bookmarks are preserved: /admin/hub_v2 (Route
// in AppRoutes) also Navigate's here.
import React from "react";
import { Navigate } from "react-router-dom";

export default function AdminHubV2() {
  return (
    <Navigate
      to="/admin"
      replace
      data-testid="admin-hub-v2-legacy-redirect"
    />
  );
}
