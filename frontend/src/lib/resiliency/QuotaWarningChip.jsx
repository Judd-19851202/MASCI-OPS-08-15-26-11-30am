// QuotaWarningChip.jsx — TRUST-1 · TF-004 · 2026-05-27.
//
// Tiny, calm storage-pressure chip. Renders ONLY when `pressure` is
// truthy (i.e. >= 80% of the device storage estimate is in use). The
// chip is hidden by default and never replaces the autosave pill —
// it sits beside it as a calm "submit soon" nudge.
//
// Doctrine
// --------
//   * No alarm color. Amber, not red. NEVER pulsing.
//   * Operator language: "Storage almost full · finish and submit
//     soon." NEVER "QuotaExceededError", "IndexedDB", "navigator
//     storage", "browser quota".
//   * No action button. Pure awareness chip.

import React from "react";
import { Database } from "lucide-react";

export default function QuotaWarningChip({ pressure, testId = "quota-warning-chip" }) {
  if (!pressure || typeof pressure.ratio !== "number") return null;
  const pct = Math.min(99, Math.round(pressure.ratio * 100));
  const title = `Storage ${pct}% full · finish and submit soon`;
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-50 text-amber-800 text-[10px] font-mono uppercase tracking-wider border border-amber-200"
      data-testid={testId}
      data-ratio={pressure.ratio.toFixed(3)}
      title={title}
      aria-label={title}
    >
      <Database className="w-3 h-3" aria-hidden="true" />
      Storage {pct}%
    </span>
  );
}
