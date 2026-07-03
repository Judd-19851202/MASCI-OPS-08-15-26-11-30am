// Track 19.54 · Operational Guidance System (OGS).
//
// Universal attention-language chip. Used everywhere any product,
// portal, or Guidance Card renders an attention level. Enforces the
// four-value universal vocabulary defined in Track 19.54:
//
//   CRITICAL — Immediate action required.
//   HIGH     — Address today.
//   MEDIUM   — Plan.
//   LOW      — Healthy.
//
// Consumes ONLY the `attention_level` string already returned by the
// certified Operational Intelligence summary payload. Zero re-derivation.

import React from "react";

const TONE = {
  CRITICAL: { chip: "bg-red-100 text-red-900 border-red-300", label: "Immediate action required" },
  HIGH:     { chip: "bg-orange-100 text-orange-900 border-orange-300", label: "Address today" },
  MEDIUM:   { chip: "bg-amber-100 text-amber-900 border-amber-300", label: "Plan this week" },
  LOW:      { chip: "bg-emerald-100 text-emerald-900 border-emerald-300", label: "Healthy" },
};

export default function AttentionChip({ level, showHint = false, testId }) {
  const key = (level || "").toUpperCase();
  const tone = TONE[key] || { chip: "bg-slate-100 text-slate-800 border-slate-300", label: "—" };
  return (
    <span
      data-testid={testId || "attention-chip"}
      className={`inline-flex items-center gap-1 rounded border px-1.5 py-0.5 text-[10px] font-mono font-bold uppercase tracking-wider ${tone.chip}`}
    >
      <span>{key || "—"}</span>
      {showHint && key && (
        <span
          data-testid={`${testId || "attention-chip"}-hint`}
          className="normal-case font-medium tracking-normal"
        >
          · {tone.label}
        </span>
      )}
    </span>
  );
}
