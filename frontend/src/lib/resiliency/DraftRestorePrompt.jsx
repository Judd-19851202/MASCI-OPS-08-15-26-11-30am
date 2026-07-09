// DraftRestorePrompt.jsx — iter440 · P0 field-incident remediation.
//
// Calm, single-card prompt offered when a form mounts AND an unsent
// draft was found in IndexedDB for this (device, formKey).
//
// What changed at iter440
// -----------------------
//   - Shows the relative `savedAt` timestamp ("Saved 2 hours ago")
//     so the operator can tell whether the offered draft is today's
//     in-progress work or yesterday's stale tail.
//   - If `isCrossToken` is true (the draft was recovered from a
//     previous session under a different portal token), a small
//     "Recovered from a previous session" subtitle appears so the
//     operator knows this is intentional, not stale data.
//
// Doctrine (unchanged)
// --------------------
//   - Shown ONCE per recovery decision. Hides after Restore or
//     Discard.
//   - NO modal · NO overlay · NO sticky banner · NO sound.
//   - Two buttons only: Restore · Discard.

import React from "react";
import { ScrollText, RotateCcw, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useT } from "@/lib/i18n";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

function _humanizeAge(savedAt, t) {
  if (!savedAt) return "";
  const secs = Math.max(0, Math.floor((Date.now() - savedAt) / 1000));
  if (secs < 60) return `${secs}${t("s ago")}`;
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `${mins}${t("m ago")}`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}${t("h ago")}`;
  const days = Math.floor(hrs / 24);
  if (days < 14) return `${days}${t("d ago")}`;
  return formatPlatformTime(savedAt);
}

export default function DraftRestorePrompt({
  pendingDraft,
  savedAt = null,
  isCrossToken = false,
  onRestore,
  onDiscard,
  testId = "draft-restore-prompt",
}) {
  const { t } = useT();
  if (!pendingDraft) return null;
  const age = savedAt ? _humanizeAge(savedAt, t) : null;
  // TRACK 26.08 · always surface the project + date the draft is bound
  // to so a multi-project supervisor cannot silently restore another
  // day's work. Draft contract requires (device, user, project, date)
  // scoping — see /app/memory/TRACK_26_08_DAILY_REPORT_DRAFT_CONTINUITY.md
  const draftProject = (pendingDraft.project_number || "").trim();
  const draftProjectName = (pendingDraft.project_name || "").trim();
  const draftDate = (pendingDraft.report_date || "").trim();
  return (
    <section
      data-testid={testId}
      data-saved-at={savedAt || ""}
      data-cross-token={isCrossToken ? "1" : "0"}
      data-draft-project={draftProject}
      data-draft-report-date={draftDate}
      className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 mb-4"
    >
      <div className="flex items-start gap-3">
        <ScrollText
          className="h-5 w-5 text-amber-700 mt-0.5 flex-shrink-0"
          aria-hidden="true"
        />
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-amber-900">
            {t("You have unsaved work from earlier.")}
          </h3>
          <p
            className="text-xs text-amber-800 mt-1"
            data-testid={`${testId}-savedat`}
          >
            {age
              ? t("Saved {age} on this device.").replace("{age}", age)
              : t("Your work is saved on this device until it is submitted.")}
          </p>
          {(draftProject || draftDate) ? (
            <p
              className="text-xs text-amber-900 mt-1 font-medium"
              data-testid={`${testId}-scope`}
            >
              {draftProject
                ? `${t("Project")}: ${draftProjectName ? `${draftProjectName} (${draftProject})` : draftProject}`
                : t("Project not yet selected")}
              {draftDate ? ` · ${t("Date")}: ${draftDate}` : ""}
            </p>
          ) : null}
          {isCrossToken ? (
            <p
              className="text-xs text-amber-700/80 mt-1 italic"
              data-testid={`${testId}-crosstoken`}
            >
              {t("Recovered from a previous session.")}
            </p>
          ) : null}
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2 mt-3">
        <Button
          type="button"
          onClick={onRestore}
          data-testid={`${testId}-restore`}
          className="bg-amber-700 hover:bg-amber-800 text-white h-9 px-4"
        >
          <RotateCcw className="h-4 w-4 mr-1.5" aria-hidden="true" />
          {t("Restore")}
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={onDiscard}
          data-testid={`${testId}-discard`}
          className="h-9 px-4 border-amber-300 text-amber-900 hover:bg-amber-100"
        >
          <Trash2 className="h-4 w-4 mr-1.5" aria-hidden="true" />
          {t("Discard")}
        </Button>
      </div>
    </section>
  );
}
