// src/pages/admin/AdminJobTeam.jsx — Track 14.0-JOB-OWNERSHIP-FOUNDATION
// Phase 1. Admin-scoped Project Team Manager.

import React from "react";
import { useParams } from "react-router-dom";
import AdminShell from "@/components/AdminShell";
import JobTeamRosterPanel from "@/components/team/JobTeamRosterPanel";

export default function AdminJobTeam() {
  const { projectNumber } = useParams();
  return (
    <AdminShell
      title={`Job Team — ${projectNumber}`}
      section="jobs"
      intro={
        <p className="text-sm text-slate-600">
          Assign Superintendent, Foreman, Safety Lead, Project Engineer,
          Asset Admin / 811 Locate Coordinator, Dispatcher Contact, and
          Shop Contact to this project. Every change is audited. The
          existing PM and Co-PM email assignments are mirrored here
          read-only on roster backfill; rename PMs from{" "}
          <a href="/admin/jobs" className="underline">Jobs &amp; Field</a>.
        </p>
      }
    >
      <JobTeamRosterPanel projectNumber={projectNumber} scope="admin" />
    </AdminShell>
  );
}
