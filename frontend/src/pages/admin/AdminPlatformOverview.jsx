// TRACK 25 · SPRINT 6 · Admin OS · Platform Overview.
//
// The canonical platform overview IS the Admin Operating System
// landing at /admin (AdminOS.jsx · 10 domain cards · live probes ·
// executive posture strip). To eliminate any "which hub is the real
// one?" confusion, /admin/platform-overview simply redirects to
// /admin. Bookmarks that expect a dedicated overview URL keep
// working, and there is only ONE canonical overview experience.
import React from "react";
import { Navigate } from "react-router-dom";

export default function AdminPlatformOverview() {
  return (
    <Navigate
      to="/admin"
      replace
      data-testid="admin-platform-overview-redirect"
    />
  );
}
