/**
 * OA-1 · StatusBadge.jsx
 * Renders one of the 6 approved statuses. No aliases. No hidden states.
 */
import React from "react";
import { useT } from "@/lib/i18n";
import { STATUS_LABEL, STATUS_TONE } from "@/lib/oa";

export default function StatusBadge({ status, className = "" }) {
  const { t } = useT();
  const tone = STATUS_TONE[status] || STATUS_TONE.open;
  const label = STATUS_LABEL[status] || status || "—";
  return (
    <span
      data-testid={`oa-status-badge-${status}`}
      className={`inline-flex items-center px-2 py-0.5 rounded border text-[10px] font-mono uppercase tracking-wider font-bold ${tone} ${className}`}
    >
      {t(label)}
    </span>
  );
}
