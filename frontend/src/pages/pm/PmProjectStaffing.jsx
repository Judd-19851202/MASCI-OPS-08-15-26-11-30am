// src/pages/pm/PmProjectStaffing.jsx
// Track 14.0-PM-STAFFING-UI-DISCOVERABILITY-CLOSURE
// PM-scoped cross-project staffing overview.
import React from "react";
import PortalShell from "@/design-system/PortalShell";
import ProjectStaffingHub from "@/pages/ProjectStaffingHub";

export default function PmProjectStaffing() {
  return (
    <PortalShell portal="pm" title="Project Staffing">
      <ProjectStaffingHub scope="pm" />
    </PortalShell>
  );
}
