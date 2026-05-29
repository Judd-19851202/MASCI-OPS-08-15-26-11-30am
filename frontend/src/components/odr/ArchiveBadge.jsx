// ArchiveBadge.jsx — Phase V.1 · M1 · Option C.
//
// Calm, slate, non-alarming visual treatment for legacy daily reports
// surfaced inside the unified Operational Records dashboard.
//
// Doctrine:
//   /app/memory/ARCHIVE_VISUAL_TREATMENT_STANDARD.md
//   /app/memory/M1_OPTION_C_IMPLEMENTATION_PLAN.md
//
// Required by operator directive:
//   "Every historical Daily Report must display:
//      ARCHIVED DAILY REPORT · Historical Record · Read Only ·
//      Original Format Preserved
//    Calm · slate styling · no warning colors · no alarm language.
//    Purpose: explain why the record differs from ODR."
//
// This component is the single source of archive visual treatment.
// Reuse it everywhere a legacy row appears so the language and tone
// stay identical platform-wide (Doctrine Lock #2 · Platform Inheritance).

import React from "react";

export default function ArchiveBadge({ size = "md", className = "" }) {
  const sizes = {
    sm: "px-1.5 py-0.5 text-[10px]",
    md: "px-2 py-0.5 text-xs",
    lg: "px-2.5 py-1 text-sm",
  };
  return (
    <span
      data-testid="archive-badge"
      className={
        "inline-flex items-center rounded-md border border-slate-300 " +
        "bg-slate-100 text-slate-600 font-medium tracking-wide uppercase " +
        sizes[size] +
        " " +
        className
      }
      title="Archived Daily Report · Historical Record · Read Only · Original Format Preserved"
    >
      Archived
    </span>
  );
}

export function ArchiveExplainerCard({ className = "" }) {
  return (
    <div
      data-testid="archive-explainer"
      className={
        "rounded-md border border-slate-200 bg-slate-50 p-3 text-slate-600 " +
        className
      }
    >
      <div className="text-xs uppercase tracking-wider text-slate-500">
        Archived Daily Report
      </div>
      <div className="mt-1 text-sm leading-snug">
        Historical Record · Read Only · Original Format Preserved.
        <br />
        This entry was filed before MASCI Ops moved to the Operational
        Daily Record. Its original shape, signatures, and PDF have not
        been altered.
      </div>
    </div>
  );
}
