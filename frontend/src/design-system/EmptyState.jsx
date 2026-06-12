// Track 13.5A · Phase B1 — <EmptyState> primitive.
// NOT applied to any existing empty surface in Phase B1.
import React from "react";

export function EmptyState({
  title = "Nothing here yet.",
  explanation,
  nextAction,
  icon = null,
  severity = "neutral", // "neutral" | "good" | "attention"
  className = "",
}) {
  const tone = {
    neutral:   { color: "var(--ink-soft)",    accent: "var(--border-bold)" },
    good:      { color: "var(--status-good)", accent: "var(--status-good)" },
    attention: { color: "var(--status-warn)", accent: "var(--status-warn)" },
  }[severity] || { color: "var(--ink-soft)", accent: "var(--border-bold)" };

  return (
    <div
      data-testid={`ds-empty-${title.toLowerCase().replace(/\W+/g, "-")}`}
      className={`flex flex-col items-start gap-2 ${className}`}
      style={{
        background: "var(--paper-card)",
        border: `1px dashed ${tone.accent}`,
        borderRadius: "var(--radius-card)",
        padding: "var(--pad-card)",
        color: tone.color,
      }}
    >
      {icon && <div aria-hidden>{icon}</div>}
      <h4 style={{ color: "var(--ink-strong)", fontSize: 14, fontWeight: 600, margin: 0 }}>
        {title}
      </h4>
      {explanation && (
        <p style={{ color: "var(--ink-soft)", fontSize: 12, margin: 0 }}>{explanation}</p>
      )}
      {nextAction && <div style={{ marginTop: 4 }}>{nextAction}</div>}
    </div>
  );
}

export default EmptyState;
