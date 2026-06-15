// src/pages/admin/AdminProjectStaffing.jsx
// Track 14.0-PM-STAFFING-UI-DISCOVERABILITY-CLOSURE
// Admin-scoped cross-project staffing overview.
import React from "react";
import AdminShell from "@/components/AdminShell";
import ProjectStaffingHub from "@/pages/ProjectStaffingHub";

export default function AdminProjectStaffing() {
  return (
    <AdminShell title="Project Staffing" section="jobs">
      <ProjectStaffingHub scope="admin" />
    </AdminShell>
  );
}
