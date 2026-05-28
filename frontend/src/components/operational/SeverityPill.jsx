// SeverityPill.jsx — single-red doctrine.
// `high` renders red. `medium` renders amber. `low` renders slate.
// NO gradient. NO icon. NO animation.

import React from "react";

const STYLE = {
  high: "bg-rose-50 text-rose-700 border-rose-200",
  medium: "bg-amber-50 text-amber-800 border-amber-200",
  low: "bg-slate-50 text-slate-700 border-slate-200",
};

export default function SeverityPill({ severity, dataTestId }) {
  const cls = STYLE[severity] || STYLE.low;
  return (
    <span
      data-testid={dataTestId || `severity-pill-${severity || "unknown"}`}
      className={
        `inline-flex items-center px-2 py-0.5 rounded-full ` +
        `text-xs font-medium border ${cls}`
      }
    >
      {severity || "—"}
    </span>
  );
}
