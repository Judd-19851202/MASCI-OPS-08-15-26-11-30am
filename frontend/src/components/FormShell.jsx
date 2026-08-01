import React from "react";
import { useT } from "@/lib/i18n";
import { CanonicalHeader } from "@/components/CanonicalHeader";

function normalizeFormPortalLabel(kicker, fallback) {
  const cleaned = String(kicker || "")
    .replace(/^MASCI\s*[·-]\s*/i, "")
    .trim();
  if (!cleaned) return fallback;
  const parts = cleaned.split("·").map((part) => part.trim()).filter(Boolean);
  return parts[0] || cleaned || fallback;
}

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
  const headerPortalLabel = normalizeFormPortalLabel(kicker, t("Operations Workspace"));
  const resolvedBackLink = backLink === "/" ? null : backLink;
  const utilityCard = subtitle || progressSlot || draftSlot || headerRightSlot ? (
    <div className="wp17-panel p-4 sm:p-5" data-testid={`${containerTestId}-utility-card`}>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0 flex-1">
          {subtitle ? (
            <p className="max-w-3xl text-sm sm:text-base leading-6 text-slate-600" data-testid={`${containerTestId}-subtitle`}>
              {subtitle}
            </p>
          ) : null}
        </div>
        {(draftSlot || headerRightSlot) ? (
          <div className="flex flex-wrap items-center gap-2 lg:justify-end" data-testid={`${containerTestId}-utility-actions`}>
            {draftSlot}
            {headerRightSlot}
          </div>
        ) : null}
      </div>

      {progressSlot ? (
        <div className="mt-4 rounded-[1.15rem] border border-slate-200 bg-slate-50/90 px-3 py-3 sm:px-4" data-testid={`${containerTestId}-progress-band`}>
          {progressSlot}
        </div>
      ) : null}
    </div>
  ) : null;

  return (
    <div
      className="min-h-screen wp17-public-shell wp17-grid-bg pb-32"
      data-testid={containerTestId}
    >
      <div className="caution-stripe" />
      <CanonicalHeader
        variant="platform"
        contextLabel={title || headerPortalLabel}
        accent="red"
        backTo={resolvedBackLink}
        backLabel={backLabel || t("Back")}
        homeTo="/"
        showHomeLink={false}
        showLangToggle
        utilitySlot={utilityCard}
        containerClassName={widthClass}
        testIdPrefix="form-shell"
      />

      {/* MAIN */}
      <main className={`${widthClass} mx-auto px-4 sm:px-6 py-6 sm:py-7 space-y-6`}>
        {children}
      </main>

      {/* STICKY FOOTER */}
      {stickyFooter && (
        <div
          className="fixed bottom-0 inset-x-0 z-30 border-t border-slate-200 bg-[rgba(246,248,252,0.94)] shadow-[0_-14px_32px_rgba(15,23,42,0.08)] backdrop-blur-xl wp17-shell-footer"
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
