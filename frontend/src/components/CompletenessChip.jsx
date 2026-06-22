// TRACK 15.62 · CompletenessChip — header pill showing operationally
// honest score. NOT a fake percentage — refer to dailyReportScore.js.
import React from "react";
import { scoreDailyReport, DR_SCORE_DIMENSIONS } from "../lib/dailyReportScore";

const CLR = {
  red:     "bg-red-100 text-red-900 border-red-300",
  amber:   "bg-amber-100 text-amber-900 border-amber-300",
  emerald: "bg-emerald-100 text-emerald-900 border-emerald-300",
  green:   "bg-green-100 text-green-900 border-green-300",
};

export const CompletenessChip = React.memo(function CompletenessChip({ data, testId = "dr-completeness-chip" }) {
  const s = scoreDailyReport(data || {});
  const cls = CLR[s.color] || CLR.amber;
  const tooltip = DR_SCORE_DIMENSIONS
    .map((d) => `${(s.dimensions[d.key] || 0) >= d.weight ? "✓" : "·"} ${d.label}`)
    .join("\n");
  return (
    <div
      data-testid={testId}
      title={tooltip}
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-semibold ${cls}`}
    >
      <span>{s.total}/{s.max}</span>
      <span className="hidden sm:inline opacity-80">·</span>
      <span className="hidden sm:inline">{s.label}</span>
    </div>
  );
});

export default CompletenessChip;
