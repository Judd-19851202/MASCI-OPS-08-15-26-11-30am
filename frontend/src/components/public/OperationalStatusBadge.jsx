import React from "react";

export function OperationalStatusBadge({ children, tone = "default", testId }) {
  const toneClass = {
    default: "border-slate-200 bg-white text-slate-700",
    cyan: "border-cyan-200 bg-cyan-50 text-cyan-800",
    amber: "border-amber-200 bg-amber-50 text-amber-900",
    red: "border-red-200 bg-red-50 text-red-800",
    emerald: "border-emerald-200 bg-emerald-50 text-emerald-800",
  }[tone] || "border-slate-200 bg-white text-slate-700";

  return (
    <span
      className={`inline-flex items-center rounded-full border px-3 py-1 text-[11px] font-mono font-bold uppercase tracking-[0.18em] ${toneClass}`}
      data-testid={testId}
    >
      {children}
    </span>
  );
}

export default OperationalStatusBadge;