// src/pages/pm/PmJobTeam.jsx — Track 14.0-JOB-OWNERSHIP-FOUNDATION
// Phase 1. PM-scoped Job Team Manager.

import React from "react";
import { useParams } from "react-router-dom";
import PortalShell from "@/design-system/PortalShell";
import JobTeamRosterPanel from "@/components/team/JobTeamRosterPanel";

export default function PmJobTeam() {
  const { projectNumber } = useParams();
  return (
    <PortalShell portal="pm" title={`Job Team — ${projectNumber}`}>
      <div className="space-y-4 p-4">
        <p className="text-sm text-slate-600 max-w-2xl">
          Roster Superintendent, Foreman, Safety Lead, Project Engineer,
          Asset Admin / 811 Locate Coordinator, Dispatcher Contact, and
          Shop Contact on this project. PM and Co-PM assignments stay
          admin-managed and are visible read-only here.
        </p>
        <JobTeamRosterPanel projectNumber={projectNumber} scope="pm" />
      </div>
    </PortalShell>
  );
}
