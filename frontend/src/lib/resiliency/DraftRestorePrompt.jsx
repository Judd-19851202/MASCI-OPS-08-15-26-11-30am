// DraftRestorePrompt.jsx — iter434 · Phase 31 · Part 2.
//
// Calm, single-card prompt offered when a form mounts AND an unsent
// draft was found in IndexedDB for this (actor, formKey).
//
// Doctrine
// --------
// - Shown ONCE per recovery decision. Hides after Restore or Discard.
// - NO modal · NO overlay · NO sticky banner · NO sound.
// - Two buttons only: Restore · Discard. No "remind me later".
// - Calm language: "You have unsaved work from earlier." · "Restore"
//   · "Discard". Bilingual via useT().
// - When the form has no draft to recover, this component renders
//   nothing (returns null).

import React from "react";
import { ScrollText, RotateCcw, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useT } from "@/lib/i18n";

export default function DraftRestorePrompt({
  pendingDraft,
  onRestore,
  onDiscard,
  testId = "draft-restore-prompt",
}) {
  const { t } = useT();
  if (!pendingDraft) return null;
  return (
    <section
      data-testid={testId}
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
          <p className="text-xs text-amber-800 mt-1">
            {t("Your work is saved on this device until it is submitted.")}
          </p>
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
