import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { useT } from "@/lib/i18n";
import { LangToggle } from "@/components/LangToggle";
import { MasciLogo } from "@/components/MasciLogo";

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
}) {
  const { t } = useT();
  return (
    <div
      className="min-h-screen wp17-public-shell wp17-grid-bg pb-32"
      data-testid={containerTestId}
    >
      <div className="caution-stripe" />
      {/* HEADER — fixed height row for stable layout across all steps. */}
      <header className="sticky top-0 z-30 wp17-public-header border-b border-slate-200 text-white">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 h-14 flex items-center gap-3">
          {backLink ? (
            <Link
              to={backLink}
              className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-white/12 bg-white/8 text-white/85 hover:bg-white/14"
              data-testid={`${containerTestId}-back-link`}
              aria-label={backLabel || t("Back")}
            >
              <ArrowLeft className="h-4 w-4" />
            </Link>
          ) : null}
          <MasciLogo className="w-8 h-8 shrink-0" />
          <div className="flex-1 min-w-0">
            {kicker && (
              <div
                className="font-mono text-[10px] uppercase tracking-[0.22em] text-white/70 truncate"
                data-testid={`${containerTestId}-kicker`}
              >
                {kicker}
              </div>
            )}
            <h1
              className="font-display text-base sm:text-lg font-black tracking-tight text-white leading-tight"
              data-testid={`${containerTestId}-title`}
            >
              {title}
            </h1>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {draftSlot}
            {headerRightSlot}
            <LangToggle />
          </div>
        </div>
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
      </header>

      {/* SUBTITLE (optional) */}
      {subtitle && (
        <div className="max-w-3xl mx-auto px-4 sm:px-6 pt-3">
          <p className="text-slate-600 text-sm sm:text-base leading-snug wp17-support-copy">
            {subtitle}
          </p>
        </div>
      )}

      {/* MAIN */}
      <main className="max-w-3xl mx-auto px-4 sm:px-6 py-5 space-y-5">
        {children}
      </main>

      {/* STICKY FOOTER */}
      {stickyFooter && (
        <div
          className="fixed bottom-0 inset-x-0 z-30 bg-white/95 backdrop-blur border-t border-slate-200 wp17-shell-footer"
          data-testid={`${containerTestId}-sticky-footer`}
        >
          <div className="max-w-3xl mx-auto px-4 sm:px-6 py-3">
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
