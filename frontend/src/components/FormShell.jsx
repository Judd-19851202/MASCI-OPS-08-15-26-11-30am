import React from "react";
import { useT } from "@/lib/i18n";
import { CanonicalHeader } from "@/components/CanonicalHeader";

/**
 * TRACK 19.10 · Phase 1 · Unified Operational FormShell Primitive.
 *
 * OPT-IN by design. Existing forms are NOT auto-refactored — each form
 * decides when to consume this primitive during its dedicated redesign
 * track (19.11 Equipment · 19.12 DVIR · 19.13 Safety Meeting).
 *
 * Provides:
 *   • Consistent page header (kicker · title · optional subtitle)
 *   • Bilingual language toggle (uses existing @/components/LangToggle)
 *   • Autosave / draft-restore slot (children pass their own indicator)
 *   • Progress slot (optional · children pass their own ring / pill)
 *   • Sticky submit-footer slot with unified spacing
 *
 * Rendering contract: STATELESS. Every piece of interactive state stays
 * on the parent page. This primitive is only visual scaffolding, so
 * consuming it cannot break inspection engines / fail-cascade / audit
 * spine / any protected behaviour.
 *
 * Non-negotiable: bilingual via useT() — every operator-facing string
 * inside this component goes through the existing i18n dictionary. No
 * new EN-only strings.
 */
export function FormShell({
  kicker,
  title,
  subtitle,
  progressSlot = null,
  draftSlot = null,
  headerRightSlot = null,
  backLink = null,
  backLabel = null,
  children,
  stickyFooter = null,
  containerTestId = "form-shell",
  widthClass = "max-w-3xl",
}) {
  const { t } = useT();
  return (
    <div
      className="min-h-screen wp17-public-shell wp17-grid-bg pb-32"
      data-testid={containerTestId}
    >
      <div className="caution-stripe" />
      <CanonicalHeader
        portalLabel={kicker || t("MASCI Operations Platform")}
        pageLabel={title}
        accent="red"
        backTo={backLink}
        backLabel={backLabel || t("Back")}
        homeTo="/"
        showHomeLink={false}
        showLangToggle
        postControlsSlot={(
          <div className="flex items-center gap-2 shrink-0">
            {draftSlot}
            {headerRightSlot}
          </div>
        )}
        containerClassName={widthClass}
        testIdPrefix={containerTestId}
      />
        {/* PROGRESS band — dedicated horizontal row so the ProgressRail
            never fights with header actions or clips off-screen. Kept
            inside the sticky header so it scrolls with the page top. */}
        {progressSlot && (
          <div
            className="border-t border-white/10 bg-white/10"
            data-testid={`${containerTestId}-progress-band`}
          >
            <div className="max-w-3xl mx-auto px-4 sm:px-6 py-2">
              {progressSlot}
            </div>
          </div>
        )}

      {/* SUBTITLE (optional) */}
      {subtitle && (
        <div className={`${widthClass} mx-auto px-4 sm:px-6 pt-3`}>
          <p className="text-slate-600 text-sm sm:text-base leading-snug wp17-support-copy">
            {subtitle}
          </p>
        </div>
      )}

      {/* MAIN */}
      <main className={`${widthClass} mx-auto px-4 sm:px-6 py-5 space-y-5`}>
        {children}
      </main>

      {/* STICKY FOOTER */}
      {stickyFooter && (
        <div
          className="fixed bottom-0 inset-x-0 z-30 bg-white/95 backdrop-blur border-t border-slate-200 wp17-shell-footer"
          data-testid={`${containerTestId}-sticky-footer`}
        >
          <div className={`${widthClass} mx-auto px-4 sm:px-6 py-3`}>
            {stickyFooter}
          </div>
        </div>
      )}

      <span className="sr-only">
        {t("Operational form · MASCI platform")}
      </span>
    </div>
  );
}

export default FormShell;
