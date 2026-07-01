import React from "react";
import { useT } from "@/lib/i18n";

/**
 * TRACK 19.10 · Phase 5 · Unified Help Drawer Primitive (proof-of-concept).
 *
 * A single, context-aware, lazy-mount help surface. Consuming forms pass
 * a `sections` array (each with `title` + `body`) and the drawer opens
 * on tap. Bilingual via useT().
 *
 * OPT-IN: existing coaching systems (`LifecycleGuide` · `HelpTipBlock` ·
 * section-header prose) remain live. This drawer is proof-of-concept
 * only — the consolidation pass lands in a later track once operators
 * validate the pattern in the field.
 *
 * Zero backend / route / persistence touched. Pure visual scaffolding.
 */
export function HelpDrawer({
  open,
  onOpenChange,
  triggerLabel,
  title,
  sections = [],
  testIdPrefix = "help-drawer",
}) {
  const { t } = useT();

  return (
    <>
      <button
        type="button"
        onClick={() => onOpenChange(true)}
        className="inline-flex items-center gap-1.5 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-[11px] font-mono uppercase tracking-[0.15em] text-slate-700 hover:border-slate-500 hover:text-slate-900"
        data-testid={`${testIdPrefix}-trigger`}
        aria-expanded={open}
        aria-controls={`${testIdPrefix}-panel`}
      >
        <span aria-hidden="true">?</span>
        {triggerLabel || t("Help")}
      </button>

      {open && (
        <div
          className="fixed inset-0 z-[55] flex items-end sm:items-start sm:justify-end bg-slate-900/40"
          data-testid={testIdPrefix}
          role="dialog"
          aria-modal="true"
          aria-label={title || t("Help drawer")}
          onClick={(e) => {
            if (e.target === e.currentTarget) onOpenChange(false);
          }}
        >
          <aside
            id={`${testIdPrefix}-panel`}
            className="bg-white w-full sm:max-w-md h-auto sm:h-full sm:m-4 rounded-t-2xl sm:rounded-2xl shadow-2xl border border-slate-200 overflow-y-auto"
            data-testid={`${testIdPrefix}-panel`}
          >
            <div className="sticky top-0 flex items-center justify-between p-4 border-b border-slate-200 bg-white">
              <div>
                <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
                  {t("Help")}
                </div>
                <div className="font-display text-lg font-black tracking-tight text-slate-900 leading-tight">
                  {title || t("Guidance")}
                </div>
              </div>
              <button
                type="button"
                onClick={() => onOpenChange(false)}
                className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-[11px] font-mono uppercase tracking-[0.15em] text-slate-700 hover:border-slate-500"
                data-testid={`${testIdPrefix}-close`}
              >
                {t("Close")}
              </button>
            </div>

            <div className="p-4 space-y-4">
              {sections.length === 0 && (
                <p className="text-sm text-slate-600">
                  {t("No guidance available for this section.")}
                </p>
              )}
              {sections.map((s, i) => (
                <section
                  key={i}
                  data-testid={`${testIdPrefix}-section-${i}`}
                  className="rounded-xl border border-slate-200 bg-slate-50 p-3"
                >
                  <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 mb-1">
                    {t("Section")} {i + 1}
                  </div>
                  <h3 className="font-display text-base font-bold text-slate-900 leading-snug">
                    {s.title}
                  </h3>
                  <p className="mt-1 text-sm text-slate-700 leading-relaxed whitespace-pre-line">
                    {s.body}
                  </p>
                </section>
              ))}
            </div>
          </aside>
        </div>
      )}
    </>
  );
}

export default HelpDrawer;
