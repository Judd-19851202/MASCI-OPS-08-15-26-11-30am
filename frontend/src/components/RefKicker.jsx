// RefKicker · iter336 · review-side reference continuity
//
// Subdued mono kicker that surfaces the same canonical record
// identifier visible on the /thank-you page (iter335). Mounted at
// the top of detail/review pages so when a field crew calls in
// referencing "INC-2026-0517-002", Safety/PM/HR can instantly
// spot-match the open record.
//
// Display rules:
//   • Renders ONLY when a stable identifier is present (graceful absence)
//   • Same visual contract as iter335 ThankYou reference line
//   • EN: "Ref · <ID>"  /  ES: "Ref. · <ID>"
//   • select-all on the ID for tap-and-hold mobile copy
import React from "react";
import { useT } from "@/lib/i18n";

export function RefKicker({ recordId, testId = "ref-kicker", className = "" }) {
  const { t } = useT();
  if (!recordId) return null;
  return (
    <p
      className={`font-mono text-[11px] uppercase tracking-[0.18em] text-slate-500 ${className}`}
      data-testid={testId}
    >
      <span className="text-slate-400">{t("Ref")} · </span>
      <span className="text-slate-700 font-bold select-all">{recordId}</span>
    </p>
  );
}

export default RefKicker;
