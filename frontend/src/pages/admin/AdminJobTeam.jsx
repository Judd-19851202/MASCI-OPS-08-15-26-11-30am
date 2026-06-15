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
          Manage the full 17-role project roster — Project Manager, Co-PM,
          Executive Oversight, Superintendent, Assistant Superintendent,
          Foreman, Project Engineer, Project Administrator, Project
          Coordinator, Safety / QA-QC / HR / Dispatch / Equipment / Shop /
          Survey / Accounting Representatives. Every assignment fires a
          notification to the affected user and is recorded in the audit
          history. PM / Co-PM email assignments are mirrored from{" "}
          <a href="/admin/jobs" className="underline">Jobs &amp; Field</a>{" "}
          on first save.
        </p>
      }
    >
      <JobTeamRosterPanel projectNumber={projectNumber} scope="admin" />
    </AdminShell>
  );
}
