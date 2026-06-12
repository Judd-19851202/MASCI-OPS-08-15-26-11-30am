// Track 13.5A · Phase B1 — <PublicShell> primitive.
// NOT applied to any existing public surface in Phase B1.
import React from "react";

export function PublicShell({
  surfaceName,
  languageToggle = null,
  backNav = null,
  children,
  className = "",
}) {
  return (
    <div
      data-testid="ds-public-shell"
      className={className}
      style={{ background: "var(--paper-base)", color: "var(--ink-regular)", minHeight: "100vh" }}
    >
      <header
        style={{
          background: "var(--paper-card)",
          borderBottom: "1px solid var(--border-hairline)",
          padding: "12px 16px",
        }}
      >
        <div className="flex items-center justify-between gap-3" style={{ maxWidth: 1200, margin: "0 auto" }}>
          <div className="flex items-center gap-3">
            {backNav}
            <span style={{
              fontSize: "var(--kicker-size)",
              letterSpacing: "var(--kicker-tracking)",
              fontWeight: "var(--kicker-weight)",
              textTransform: "uppercase",
              color: "var(--ink-soft)",
            }}>
              MASCI · {surfaceName}
            </span>
          </div>
          {languageToggle}
        </div>
      </header>

      <main
        data-testid="ds-public-shell-content"
        style={{ padding: "var(--pad-section)", maxWidth: 1200, margin: "0 auto" }}
      >
        {children}
      </main>
    </div>
  );
}

export default PublicShell;
