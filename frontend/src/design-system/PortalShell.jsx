// Track 13.5A · Phase B1 — <PortalShell> primitive.
// NOT applied to any existing portal in Phase B1.
import React from "react";

export function PortalShell({
  portalName,
  portalRole,
  pageTitle,
  subtitle,
  primaryActions = null,
  lastActivity = null,
  alertSlot = null,
  children,
  className = "",
}) {
  return (
    <div
      data-testid="ds-portal-shell"
      className={className}
      style={{ background: "var(--paper-base)", color: "var(--ink-regular)", minHeight: "100vh" }}
    >
      <header
        style={{
          background: "var(--paper-rail)",
          color: "var(--paper-rail-ink)",
          padding: "12px 24px",
        }}
      >
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span style={{
              fontSize: "var(--kicker-size)",
              letterSpacing: "var(--kicker-tracking)",
              fontWeight: "var(--kicker-weight)",
              textTransform: "uppercase",
              color: "var(--ink-faint)",
            }}>
              {portalName} · {portalRole}
            </span>
          </div>
          {primaryActions}
        </div>
      </header>

      <section style={{ padding: "var(--pad-section)" }}>
        <div className="flex items-start justify-between gap-4" style={{ marginBottom: 16 }}>
          <div>
            <h1 style={{
              fontSize: 28, fontWeight: 700, margin: 0,
              color: "var(--ink-strong)", fontFamily: "var(--font-display)",
            }}>
              {pageTitle}
            </h1>
            {subtitle && (
              <p style={{ color: "var(--ink-soft)", margin: "4px 0 0", fontSize: 14 }}>
                {subtitle}
              </p>
            )}
          </div>
          {lastActivity && (
            <aside style={{ color: "var(--ink-soft)", fontSize: 12 }}>
              {lastActivity}
            </aside>
          )}
        </div>

        {alertSlot && <div style={{ marginBottom: 16 }}>{alertSlot}</div>}

        <main data-testid="ds-portal-shell-content">{children}</main>
      </section>
    </div>
  );
}

export default PortalShell;
