// src/pages/pm/PmJobTeam.jsx — Track 14.0-JOB-OWNERSHIP-FOUNDATION
// Phase 1. PM-scoped Job Team Manager.
// Track 15.10 — added breadcrumb + back navigation (PM never trapped).

import React from "react";
import { Link, useParams } from "react-router-dom";
import { ChevronLeft, ChevronRight } from "lucide-react";
import PortalShell from "@/design-system/PortalShell";
import JobTeamRosterPanel from "@/components/team/JobTeamRosterPanel";
import { sanitizeOperatorProjectNumber } from "@/lib/operatorLanguage";

export default function PmJobTeam() {
  const { projectNumber } = useParams();
  const safeProjectNumber = sanitizeOperatorProjectNumber(projectNumber, "Project number unavailable");
  return (
    <PortalShell portal="pm" title={`Job Team — ${safeProjectNumber}`}>
      <div className="space-y-4 p-4">
        {/* TRACK 15.10 · breadcrumb + sticky back action so PM is
            never trapped on iPad portrait/landscape. Visible on
            every viewport including the PWA. */}
        <nav
          aria-label="Breadcrumb"
          data-testid="pm-job-team-breadcrumb"
          className="flex items-center gap-1.5 text-xs font-mono uppercase tracking-[0.12em] text-slate-500 flex-wrap"
        >
          <Link to="/pm/portal" className="hover:text-purple-700" data-testid="pm-job-team-crumb-portal">
            PM Portal
          </Link>
          <ChevronRight className="w-3.5 h-3.5" />
          <Link to="/pm/project-staffing" className="hover:text-purple-700" data-testid="pm-job-team-crumb-staffing">
            Project Staffing
          </Link>
          <ChevronRight className="w-3.5 h-3.5" />
          <span className="text-slate-800 font-bold" data-testid="pm-job-team-crumb-current">
            Project {safeProjectNumber} Team
          </span>
        </nav>
        <div className="flex items-center justify-between gap-3">
          <Link
            to="/pm/project-staffing"
            className="inline-flex items-center gap-1 px-3 py-1.5 rounded border border-slate-300 bg-white hover:bg-slate-50 text-xs font-bold uppercase tracking-wide"
            data-testid="pm-job-team-back"
          >
            <ChevronLeft className="w-3.5 h-3.5" /> Back to Project Staffing
          </Link>
        </div>
        <p className="text-sm text-slate-600 max-w-2xl">
          Roster the operational team on this project — Superintendent,
          Foreman, Project Engineer, Project Administrator, Project
          Coordinator, Safety / QA-QC / HR / Dispatch / Equipment / Shop /
          Survey / Accounting Representatives. Project Manager, Co-PM, and
          Executive Oversight stay admin-managed and are visible read-only
          here. Every change sends a notice and appears in project history.
        </p>
        <JobTeamRosterPanel projectNumber={projectNumber} scope="pm" />
      </div>
    </PortalShell>
  );
}
