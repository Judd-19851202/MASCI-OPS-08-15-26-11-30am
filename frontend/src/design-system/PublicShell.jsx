// Track 13.5A · Phase B1 — <PublicShell> primitive.
// NOT applied to any existing public surface in Phase B1.
import React from "react";
import { CanonicalHeader } from "@/components/CanonicalHeader";

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
      <CanonicalHeader
        variant="platform"
        contextLabel={surfaceName}
        accent="default"
        showHomeLink={false}
        showLangToggle={false}
        postControlsSlot={languageToggle}
        preControlsSlot={backNav}
        containerClassName="max-w-[1200px]"
        testIdPrefix="ds-public-shell"
      />

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
