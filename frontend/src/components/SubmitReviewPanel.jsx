import React from "react";
import { useT } from "@/lib/i18n";
import { CheckCircle2, AlertOctagon, FileText, Truck, Bell, Users, Wrench } from "lucide-react";

/**
 * TRACK 19.11 · Reusable Platform Primitive · SubmitReviewPanel
 * --------------------------------------------------------------
 * Pre-submit review + downstream commitment panel.
 *
 * Consumed by Equipment Pre-Op (Track 19.11 MAIN) and reusable
 * across DVIR / Safety Meeting / Toolbox Meeting.
 *
 * Renders TWO stacked cards:
 *   1) SUMMARY: pass/fail/na tallies + optional OOS banner + any
 *      caller-supplied summary rows (e.g. camera-obstruction status).
 *   2) DOWNSTREAM COMMITMENT: non-technical, operational bullets that
 *      tell the operator exactly what happens after Submit. This is
 *      the standard six-bullet commitment matrix. Bilingual via
 *      useT().
 *
 * Bilingual. Every string routes through i18n. Zero backend.
 */
export function SubmitReviewPanel({
  passCount = 0,
  failCount = 0,
  naCount = 0,
  outOfService = false,
  extraSummaryRows = [],
  commitments = null,          // caller can override to customize per-form
  testId = "submit-review-panel",
}) {
  const { t } = useT();

  const defaultCommitments = commitments || [
    {
      icon: FileText,
      label: t("Inspection will be recorded in the operational history."),
      testId: "commit-history",
    },
    {
      icon: AlertOctagon,
      label: t("Failed items may mark this unit OUT OF SERVICE until shop clears it."),
      testId: "commit-oos",
    },
    {
      icon: Wrench,
      label: t("The shop team may be notified per project routing."),
      testId: "commit-shop",
    },
    {
      icon: Users,
      label: t("Your supervisor and safety may be notified per project routing."),
      testId: "commit-supervisor",
    },
    {
      icon: Truck,
      label: t("Corrective action may be required before the unit is used again."),
      testId: "commit-corrective",
    },
    {
      icon: Bell,
      label: t("A permanent historical record will be created for audits."),
      testId: "commit-audit",
    },
  ];

  return (
    <div className="space-y-4" data-testid={testId}>
      {/* SUMMARY */}
      <div
        className={`rounded-xl border-2 p-4 sm:p-5 ${
          outOfService ? "border-red-700 bg-red-50" : "border-slate-300 bg-white"
        }`}
        data-testid={`${testId}-summary`}
      >
        <div className="flex items-center justify-between gap-2">
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
            {t("Review")}
          </div>
          {outOfService && (
            <span
              className="font-mono text-[10px] uppercase tracking-[0.2em] font-bold bg-red-700 text-white px-2 py-0.5 rounded"
              data-testid={`${testId}-oos-flag`}
            >
              {t("Out of Service")}
            </span>
          )}
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-3 text-sm font-bold">
          <span className="text-emerald-700" data-testid={`${testId}-pass`}>
            {passCount} {t("PASS")}
          </span>
          <span className="text-red-700" data-testid={`${testId}-fail`}>
            {failCount} {t("FAIL")}
          </span>
          <span className="text-slate-600" data-testid={`${testId}-na`}>
            {naCount} {t("N/A")}
          </span>
        </div>
        {extraSummaryRows.length > 0 && (
          <ul className="mt-3 space-y-1.5 text-sm text-slate-700">
            {extraSummaryRows.map((r, i) => (
              <li
                key={i}
                data-testid={`${testId}-extra-${i}`}
                className="flex items-start gap-2"
              >
                <CheckCircle2 className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" aria-hidden />
                <span>{r}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* DOWNSTREAM COMMITMENT */}
      <div
        className="rounded-xl border border-slate-200 bg-slate-50 p-4 sm:p-5"
        data-testid={`${testId}-commitment`}
      >
        <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500 mb-2">
          {t("What happens after you submit")}
        </div>
        <ul className="space-y-2">
          {defaultCommitments.map((c, i) => {
            const Ico = c.icon || CheckCircle2;
            return (
              <li
                key={i}
                className="flex items-start gap-2"
                data-testid={c.testId || `${testId}-commit-${i}`}
              >
                <Ico className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" aria-hidden />
                <span className="text-sm text-slate-800 leading-snug">{c.label}</span>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}

export default SubmitReviewPanel;
