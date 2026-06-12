// Track 13.5A · Phase B1 — <Card> primitive.
// Token-based styling. NOT applied to any existing card in Phase B1.
import React from "react";

export function Card({
  title,
  description,
  metric,
  status,
  action,
  density = "regular",   // "compact" | "regular" | "spacious"
  variant = "default",   // "default" | "warning" | "danger" | "success"
  children,
  className = "",
  "data-testid": testId,
}) {
  const pad = density === "compact" ? "var(--pad-tight)"
            : density === "spacious" ? "var(--pad-section)"
            : "var(--pad-card)";
  const variantStripe = {
    default: "transparent",
    warning: "var(--status-warn)",
    danger:  "var(--status-bad)",
    success: "var(--status-good)",
  }[variant] || "transparent";

  return (
    <section
      data-testid={testId || `ds-card-${(title || "untitled").toLowerCase().replace(/\W+/g, "-")}`}
      className={className}
      style={{
        background: "var(--paper-card)",
        border: "1px solid var(--border-hairline)",
        borderRadius: "var(--radius-card)",
        boxShadow: "0 1px 2px 0 rgba(15,23,42,0.04)",
        padding: pad,
        borderTop: variant !== "default" ? `3px solid ${variantStripe}` : undefined,
        color: "var(--ink-regular)",
      }}
    >
      {(title || status) && (
        <header className="flex items-start justify-between" style={{ marginBottom: 8 }}>
          {title && (
            <h3 style={{
              color: "var(--ink-strong)",
              fontSize: 14, fontWeight: 700, letterSpacing: "0.01em",
              margin: 0,
            }}>{title}</h3>
          )}
          {status && <div>{status}</div>}
        </header>
      )}
      {description && (
        <p style={{ color: "var(--ink-soft)", fontSize: 12, margin: 0, marginBottom: 8 }}>
          {description}
        </p>
      )}
      {metric != null && (
        <div style={{
          color: "var(--ink-strong)",
          fontSize: 28, fontWeight: 700, lineHeight: 1.1,
          margin: "4px 0 8px",
        }}>{metric}</div>
      )}
      {children}
      {action && <footer style={{ marginTop: 12 }}>{action}</footer>}
    </section>
  );
}

export default Card;
