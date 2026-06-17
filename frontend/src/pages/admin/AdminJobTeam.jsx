// src/pages/admin/AdminJobTeam.jsx — Track 14.0-JOB-OWNERSHIP-FOUNDATION
// Phase 1. Admin-scoped Project Team Manager.
// Track 15.10 — added breadcrumb + back navigation (consistent with PM).

import React from "react";
import { Link, useParams } from "react-router-dom";
import { ChevronLeft, ChevronRight } from "lucide-react";
import AdminShell from "@/components/AdminShell";
import JobTeamRosterPanel from "@/components/team/JobTeamRosterPanel";

export default function AdminJobTeam() {
  const { projectNumber } = useParams();
  return (
    <AdminShell
      title={`Job Team — ${projectNumber}`}
      section="jobs"
      intro={
        <div className="space-y-3">
          {/* TRACK 15.10 · breadcrumb + back action for Admin parity. */}
          <nav
            aria-label="Breadcrumb"
            data-testid="admin-job-team-breadcrumb"
            className="flex items-center gap-1.5 text-xs font-mono uppercase tracking-[0.12em] text-slate-500 flex-wrap"
          >
            <Link to="/admin" className="hover:text-blue-700" data-testid="admin-job-team-crumb-portal">
              Admin Portal
            </Link>
            <ChevronRight className="w-3.5 h-3.5" />
            <Link to="/admin/project-staffing" className="hover:text-blue-700" data-testid="admin-job-team-crumb-staffing">
              Project Staffing
            </Link>
            <ChevronRight className="w-3.5 h-3.5" />
            <span className="text-slate-800 font-bold" data-testid="admin-job-team-crumb-current">
              Project {projectNumber} Team
            </span>
          </nav>
          <Link
            to="/admin/project-staffing"
            className="inline-flex items-center gap-1 px-3 py-1.5 rounded border border-slate-300 bg-white hover:bg-slate-50 text-xs font-bold uppercase tracking-wide"
            data-testid="admin-job-team-back"
          >
            <ChevronLeft className="w-3.5 h-3.5" /> Back to Project Staffing
          </Link>
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
        </div>
      }
    >
      <JobTeamRosterPanel projectNumber={projectNumber} scope="admin" />
    </AdminShell>
  );
}
