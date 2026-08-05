// StatusBadge.jsx — Iter B unification.
//
// Single-line render of a domain status. Replaces ad-hoc `<span>` +
// inline tailwind classes scattered across PoRequests/Tasks/DocExp etc.
//
// Usage:
//   <StatusBadge kind="po" value="Approved" />
//   <StatusBadge kind="task" value={t.status} size="sm" />
//
// Canonical operator-target labels (TR-0005 extension):
//   <StatusBadge kind="qaqc" value="DEFICIENCY_RAISED" useCanonicalLabel />
//     → renders "Needs Revision" with the QA/QC amber tint.
//   Without the flag, the raw value is rendered (backwards-compatible).
//
// Sizes: "sm" (compact mobile / dense lists) | "md" (default) | "lg".
import React from "react";
import { tintFor, labelFor } from "@/lib/statusBadges";
import { sanitizeOperatorCopy } from "@/lib/operatorLanguage";

const SIZE_CLASSES = {
  sm: "px-1.5 py-0.5 text-[10px]",
  md: "px-2 py-0.5 text-[11px]",
  lg: "px-2.5 py-1 text-xs",
};

export function StatusBadge({
  kind,
  value,
  size = "md",
  className = "",
  testId,
  useCanonicalLabel = false,
}) {
  if (!value) return null;
  const tint = tintFor(kind, value);
  const sz = SIZE_CLASSES[size] || SIZE_CLASSES.md;
  const displayed = sanitizeOperatorCopy(useCanonicalLabel ? labelFor(kind, value) : value, value);
  return (
    <span
      className={`inline-flex items-center gap-1 rounded font-mono uppercase tracking-wider font-bold border ${tint} ${sz} ${className}`}
      data-testid={testId || `status-badge-${kind}-${String(value).toLowerCase().replace(/\s+/g, '-')}`}
    >
      {displayed}
    </span>
  );
}

export default StatusBadge;
