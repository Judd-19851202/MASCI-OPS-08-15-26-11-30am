// Track 13.5A · Phase B1 — <StatusChip> primitive.
// Token-based colors. NOT applied to any existing chip in Phase B1.
import React from "react";
import { lookupStatus, SEVERITY_STYLE } from "./statusRegistry";

export function StatusChip({
  statusKey,
  label,
  severity = "neutral",
  icon = null,
  tooltip = null,
  compact = false,
  className = "",
}) {
  const entry = statusKey ? lookupStatus(statusKey) : null;
  const finalLabel = label ?? (entry ? entry.label : "—");
  const finalSeverity = entry?.severity ?? severity;
  const style = SEVERITY_STYLE[finalSeverity] || SEVERITY_STYLE.neutral;

  return (
    <span
      title={tooltip || finalLabel}
      data-testid={`status-chip-${(statusKey || finalLabel).toLowerCase().replace(/\W+/g, "-")}`}
      className={`inline-flex items-center gap-1.5 font-medium ${className}`}
      style={{
        color: style.color,
        backgroundColor: style.bg,
        border: `1px solid ${style.border}`,
        borderRadius: "var(--radius-chip)",
        padding: compact ? "2px 8px" : "4px 12px",
        fontSize: compact ? "11px" : "12px",
        lineHeight: 1,
        letterSpacing: "0.02em",
        whiteSpace: "nowrap",
      }}
    >
      {icon && <span aria-hidden style={{ width: 12, height: 12 }}>{icon}</span>}
      {finalLabel}
    </span>
  );
}

export default StatusChip;
