import React from "react";
import { useT } from "@/lib/i18n";
import { Check, ChevronDown, ChevronRight, AlertOctagon } from "lucide-react";

/**
 * TRACK 19.11 · Reusable Platform Primitive · FormSection
 * --------------------------------------------------------
 * A progressive-disclosure section wrapper for operational forms.
 *
 * States:
 *   • active     — fully expanded, editable (default)
 *   • completed  — collapsed to a summary strip (green check + count)
 *   • pending    — collapsed placeholder (waiting for prior steps)
 *
 * Rendering contract: STATELESS. Every piece of interactive/validation
 * state lives on the parent page. This primitive only styles/toggles.
 *
 * Consumed by Equipment Pre-Op in Track 19.11 MAIN, and reusable
 * across DVIR (Track 19.12) and Safety Meeting (Track 19.13).
 *
 * Bilingual via useT(). Zero backend touched.
 */
export function FormSection({
  number,
  title,
  subtitle = null,
  state = "active",           // "active" | "completed" | "pending"
  onExpand = null,             // fired when user taps a collapsed header
  summaryChip = null,          // small right-aligned indicator (e.g. "3 PASS · 0 FAIL")
  warning = null,              // amber string shown at header level
  children,
  testId = "form-section",
}) {
  const { t } = useT();

  if (state === "pending") {
    return (
      <section
        className="rounded-[1.2rem] border border-dashed border-slate-300 bg-slate-50/80 px-4 py-3.5"
        data-testid={testId}
        data-section-state="pending"
      >
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">
              {t("Section")} {number}
            </span>
            <h2 className="text-base font-semibold text-slate-600 truncate">
              {title}
            </h2>
          </div>
          <ChevronRight className="w-4 h-4 text-slate-400 shrink-0" aria-hidden />
        </div>
      </section>
    );
  }

  if (state === "completed") {
    return (
      <section
        className="rounded-[1.2rem] border border-emerald-200 bg-emerald-50/80 px-4 py-3.5 hover:bg-emerald-50 transition-colors"
        data-testid={testId}
        data-section-state="completed"
      >
        <button
          type="button"
          onClick={onExpand || undefined}
          className="w-full flex items-center justify-between gap-3 text-left"
          data-testid={`${testId}-reopen`}
          disabled={!onExpand}
        >
          <div className="flex items-center gap-3 min-w-0">
            <span className="w-5 h-5 rounded-full bg-emerald-600 text-white flex items-center justify-center shrink-0">
              <Check className="w-3.5 h-3.5" aria-hidden />
            </span>
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-emerald-800 font-bold">
              {t("Section")} {number}
            </span>
            <h2 className="text-base font-semibold text-slate-900 truncate">
              {title}
            </h2>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {summaryChip}
            {onExpand && <ChevronDown className="w-4 h-4 text-emerald-700" aria-hidden />}
          </div>
        </button>
      </section>
    );
  }

  // active
  return (
    <section
      className="wp17-panel space-y-4 p-4 sm:p-5"
      data-testid={testId}
      data-section-state="active"
    >
      <header className="space-y-1">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-700 font-bold">
              {t("Section")} {number}
            </span>
            <h2 className="text-lg sm:text-xl font-semibold tracking-tight text-slate-900">
              {title}
            </h2>
          </div>
          {summaryChip}
        </div>
        {subtitle && <p className="text-sm text-slate-600 leading-snug">{subtitle}</p>}
        {warning && (
          <div className="flex items-start gap-2 rounded border border-amber-300 bg-amber-50 px-3 py-2">
            <AlertOctagon className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" aria-hidden />
            <p className="text-sm text-amber-900 leading-snug">{warning}</p>
          </div>
        )}
      </header>
      {children}
    </section>
  );
}

export default FormSection;
