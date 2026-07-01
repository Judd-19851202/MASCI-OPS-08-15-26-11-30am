import React from "react";
import { useT } from "@/lib/i18n";

/**
 * TRACK 19.11 · Reusable Platform Primitive · PresenceGate
 * ---------------------------------------------------------
 * A three-way "presence question" that governs progressive disclosure
 * for an entire sub-section: Yes → reveal follow-up · No / Not-sure →
 * follow-up hidden. Optional "hard-block" mode marks a specific Yes/No
 * combination as a submission blocker (used by Camera Obstruction Gate).
 *
 * OPT-IN by design. Consumed by Equipment Pre-Op Camera System Check
 * in Track 19.11 MAIN; ready for reuse by DVIR (defect presence,
 * trailer presence) and Safety Meeting (attendance presence,
 * incident-referenced presence) in Tracks 19.12 / 19.13.
 *
 * Zero backend touched. Pure state + slot rendering. Every visible
 * string routes through i18n via useT() — no EN-only strings.
 *
 * Contract:
 *   • value: "yes" | "no" | "unsure" | ""
 *   • onChange(next): parent owns state
 *   • options: array of {v, label} — default is Yes/No/Not sure
 *   • followUpWhen: value that reveals the followUp slot (default "yes")
 *   • followUp: React node rendered under the gate when active
 *   • hardBlock: {when, message} — when value matches, render a red
 *                block panel; the parent form is expected to prevent
 *                submit via its own logic
 */
export function PresenceGate({
  label,
  value,
  onChange,
  options = null,
  followUpWhen = "yes",
  followUp = null,
  testIdPrefix = "presence-gate",
  hardBlock = null,
}) {
  const { t } = useT();
  const opts = options || [
    { v: "yes", label: t("Yes"), testId: `${testIdPrefix}-yes` },
    { v: "no", label: t("No"), testId: `${testIdPrefix}-no` },
    { v: "unsure", label: t("Not sure"), testId: `${testIdPrefix}-unsure` },
  ];
  return (
    <div
      className="rounded-xl border border-slate-200 bg-slate-50 p-3 sm:p-4 space-y-3"
      data-testid={testIdPrefix}
    >
      <div>
        <div className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
          {label}
        </div>
        <div
          className={`mt-2 grid gap-2 ${
            opts.length === 2 ? "grid-cols-2" : "grid-cols-3"
          }`}
        >
          {opts.map((opt) => (
            <button
              key={opt.v}
              type="button"
              data-testid={opt.testId || `${testIdPrefix}-${opt.v}`}
              onClick={() => onChange(opt.v)}
              className={`h-10 rounded-md font-mono text-xs uppercase tracking-[0.15em] border-2 transition-colors ${
                value === opt.v
                  ? "bg-slate-900 text-white border-transparent"
                  : "bg-white text-slate-600 border-slate-300 hover:border-slate-500"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>
      {value === followUpWhen && followUp && (
        <div
          className="pt-2 border-t border-slate-200"
          data-testid={`${testIdPrefix}-followup`}
        >
          {followUp}
        </div>
      )}
      {hardBlock && hardBlock.when === value && (
        <div
          className="rounded-md border-2 border-red-400 bg-red-50 p-3"
          data-testid={`${testIdPrefix}-block`}
        >
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-red-800 font-bold">
            {t("Safety-critical · Submission blocked")}
          </div>
          <p className="mt-1 text-sm text-red-900 leading-snug">
            {hardBlock.message}
          </p>
          {hardBlock.children}
        </div>
      )}
    </div>
  );
}

export default PresenceGate;
