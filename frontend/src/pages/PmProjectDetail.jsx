// PmProjectDetail.jsx — Phase V-Prelude · Wave 1.1.
//
// Calm per-project detail surface that hosts the Operational Timeline
// sidecar. This page is intentionally MINIMAL — its sole job is to
// give the chronology sidecar a high-context home inside the PM portal,
// so real operators can validate timeline usability during the Wave 1
// observation window.
//
// DO NOT add tiles, KPIs, charts, or dashboard widgets here (Wave 1.1
// hard rule: "no dashboard additions"). This is a single-project
// chronology surface.

import React from "react";
import { useParams, Link } from "react-router-dom";
import { Briefcase } from "lucide-react";
import PmShell from "@/components/PmShell";
import OperationalTimelineSidecar from "@/components/operational/OperationalTimelineSidecar";
import TrenchSafetyOnProjectPanel from "@/components/trench/TrenchSafetyOnProjectPanel";

export default function PmProjectDetail() {
  const { projectNumber } = useParams();
  const pn = (projectNumber || "").trim();

  return (
    <PmShell
      title="Project detail"
      section="jobs"
      intro={
        <p className="text-xs text-slate-500">
          Single-project chronology view (read-only).
        </p>
      }
    >
      <div
        data-testid="pm-project-detail-page"
        className="bg-white border border-slate-200 rounded-md p-4 sm:p-6"
      >
        <header className="flex items-baseline gap-2 flex-wrap">
          <Briefcase className="w-4 h-4 text-slate-400 shrink-0" aria-hidden="true" />
          <span
            data-testid="pm-project-detail-number"
            className="font-mono font-bold text-slate-900 text-lg break-all"
          >
            {pn || "—"}
          </span>
          <Link
            to="/pm/jobs"
            data-testid="pm-project-detail-back"
            className="ml-auto text-xs text-slate-500 hover:text-slate-800 underline-offset-2 hover:underline"
          >
            ← All jobs
          </Link>
        </header>
        <p className="text-xs text-slate-500 mt-1">
          Operational chronology for this project. Calm, text-only —
          no charts, no notifications, no editing surface.
        </p>
      </div>

      <OperationalTimelineSidecar projectNumber={pn} />

      {/* Phase 4A — Trench Safety Operations Integration */}
      <TrenchSafetyOnProjectPanel projectNumber={pn} />
    </PmShell>
  );
}
