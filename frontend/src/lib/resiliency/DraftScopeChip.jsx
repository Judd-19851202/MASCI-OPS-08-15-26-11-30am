// DraftScopeChip.jsx · TRACK 26.11 · P0 field trust surface.
//
// Renders a single always-on chip in the Daily Report header that
// tells the operator exactly which draft they are working in and its
// live save state. Prevents the "wait, is this today's report?"
// confusion that Track 26.08 exposed via the pending G-1 restore
// prompt — this chip is the equivalent contract but always visible,
// not just on restore.
//
// Contract:
//   • Shows project number when picked (else "Project not selected")
//   • Shows report date (defaults to today)
//   • Shows short device identifier suffix so a foreman knows
//     "this iPad" vs "office desktop"
//   • Shows the effective 7-state pill status inline
//
// Purely presentational. Reads no globals other than what the parent
// passes down. Every text string wired through the app's i18n hook.

import React from "react";
import { Briefcase, CalendarDays, Smartphone } from "lucide-react";
import { useT } from "@/lib/i18n";
import DraftStatusPill from "./DraftStatusPill";

function _shortDevice(deviceId) {
  if (!deviceId) return "";
  // deviceId is `d.<uuid>` — surface the last 6 chars so operators
  // can distinguish devices without exposing anything meaningful.
  const s = String(deviceId);
  return s.length > 6 ? s.slice(-6) : s;
}

export default function DraftScopeChip({
  projectNumber = "",
  projectName = "",
  reportDate = "",
  deviceId = "",
  status = "draft",
  lastSavedAt = null,
  testId = "dr-v3-draft-scope-chip",
}) {
  const { t } = useT();
  const displayProject = (projectNumber || "").trim() || t("Project not selected");
  const displayDate = (reportDate || "").trim() || t("(no date)");
  const displayDevice = _shortDevice(deviceId);
  return (
    <div
      data-testid={testId}
      data-project-number={projectNumber || ""}
      data-report-date={reportDate || ""}
      data-device-suffix={displayDevice}
      className="flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 bg-white/70 px-3 py-2 text-xs text-slate-700 shadow-sm backdrop-blur"
    >
      <span className="inline-flex items-center gap-1.5 font-medium">
        <Briefcase className="h-3.5 w-3.5 text-slate-500" aria-hidden="true" />
        <span data-testid={`${testId}-project`}>
          {projectName ? `${projectName} (${displayProject})` : displayProject}
        </span>
      </span>
      <span className="text-slate-300" aria-hidden="true">·</span>
      <span className="inline-flex items-center gap-1.5">
        <CalendarDays className="h-3.5 w-3.5 text-slate-500" aria-hidden="true" />
        <span data-testid={`${testId}-date`}>{displayDate}</span>
      </span>
      {displayDevice ? (
        <>
          <span className="text-slate-300" aria-hidden="true">·</span>
          <span
            className="inline-flex items-center gap-1.5 text-slate-500"
            data-testid={`${testId}-device`}
            title={t("Device fingerprint (last 6)")}
          >
            <Smartphone className="h-3.5 w-3.5" aria-hidden="true" />
            <span className="font-mono">{displayDevice}</span>
          </span>
        </>
      ) : null}
      <span className="ml-auto">
        <DraftStatusPill
          status={status}
          lastSavedAt={lastSavedAt}
          testId={`${testId}-pill`}
        />
      </span>
    </div>
  );
}
