import React from "react";
import { cn } from "@/lib/utils";
import { useT } from "@/lib/i18n";

// Track 14.0-F1 · accent palette for departmental colour coding without
// forking the canonical primitive. Default red (MASCI Operations).
const ACCENT_TEXT = {
  red: "text-red-700",
  amber: "text-amber-700",
  cyan: "text-cyan-700",
  emerald: "text-emerald-700",
  sky: "text-sky-700",
  slate: "text-slate-700",
};
const ACCENT_RING = {
  red: "border-red-500 ring-2 ring-red-100",
  amber: "border-amber-500 ring-2 ring-amber-100",
  cyan: "border-cyan-500 ring-2 ring-cyan-100",
  emerald: "border-emerald-500 ring-2 ring-emerald-100",
  sky: "border-sky-500 ring-2 ring-sky-100",
  slate: "border-slate-500 ring-2 ring-slate-100",
};
const ACCENT_BADGE = {
  red: "bg-red-700 text-white",
  amber: "bg-amber-700 text-white",
  cyan: "bg-cyan-700 text-white",
  emerald: "bg-emerald-700 text-white",
  sky: "bg-sky-700 text-white",
  slate: "bg-slate-700 text-white",
};

/**
 * Canonical MASCI form Section.
 *
 * Props (all back-compatible · existing callers untouched):
 *   number       — section number / id (string|number)
 *   title        — section title
 *   aside        — right-hand slot
 *   className    — extra classes
 *   accent       — "red" (default) | "amber" | "cyan" | "emerald" | "sky" | "slate"
 *                  Drives the eyebrow colour. Lets public/department forms
 *                  carry their own identity without forking the primitive.
 *   dense        — boolean. When true, uses tighter padding (p-4) for
 *                  mobile-heavy public forms that stack many sections.
 *   highlight    — when true, ring + bold border in the accent colour.
 *                  Used by "smart trigger" patterns in the trench excavation
 *                  form to signal conditionally surfaced sections.
 *   highlightLabel — short text rendered next to the title when highlighted.
 *                  Defaults to "Smart Trigger".
 *   testId       — override the default `section-{number}` test id.
 */
export const Section = ({
  number,
  title,
  aside,
  children,
  className = "",
  accent = "red",
  dense = false,
  highlight = false,
  highlightLabel,
  testId,
}) => {
  const { t } = useT();
  const eyebrow = ACCENT_TEXT[accent] || ACCENT_TEXT.red;
  const ring = highlight ? (ACCENT_RING[accent] || ACCENT_RING.red) : "border-slate-200";
  const badge = ACCENT_BADGE[accent] || ACCENT_BADGE.red;
  return (
    <section
      className={cn(
        "bg-white border rounded-md print:break-inside-avoid transition",
        dense ? "p-4 mt-3" : "p-5 sm:p-7",
        ring,
        className
      )}
      data-testid={testId || `section-${number}`}
    >
      <div
        className={cn(
          "flex items-start sm:items-center justify-between gap-3 flex-wrap",
          dense ? "mb-3" : "mb-5 pb-3 border-b-2 border-slate-200"
        )}
      >
        <div className="flex items-baseline gap-3 min-w-0">
          <span className={cn("font-mono uppercase font-bold", dense ? "text-[10px] tracking-[0.18em]" : "text-xs tracking-[0.2em]", eyebrow)}>
            {dense ? `${number} · ` : `${t("Section")} ${number}`}
            {dense ? title : null}
          </span>
          {!dense && (
            <h2 className="font-display text-xl sm:text-2xl font-bold text-slate-900 min-w-0 break-words">
              {title}
            </h2>
          )}
          {highlight && (
            <span
              className={cn("px-1.5 py-0.5 rounded text-[9px] tracking-[0.14em]", badge)}
              data-testid={`${testId || `section-${number}`}-smart-trigger`}
            >
              {highlightLabel || t("Smart Trigger")}
            </span>
          )}
        </div>
        {aside && <div className="shrink-0 max-w-full">{aside}</div>}
      </div>
      <div className={dense ? "" : "space-y-5"}>{children}</div>
    </section>
  );
};

export const ChecklistRow = ({ label, children, testId, autoFail = false }) => (
  <div
    className="grid grid-cols-1 md:grid-cols-[1fr_220px] gap-3 md:gap-6 items-start md:items-center py-3 border-b border-slate-100 last:border-b-0"
    data-testid={testId}
  >
    <span className="text-base text-slate-800 leading-snug flex items-start gap-2">
      <span>{label}</span>
      {autoFail && (
        <span
          className="shrink-0 inline-flex items-center px-1.5 py-0.5 mt-0.5 bg-red-600 text-white text-[9px] font-mono font-bold uppercase tracking-wider rounded"
          title="Failing this item triggers an automatic safety failure"
        >
          Auto-Fail
        </span>
      )}
    </span>
    <div>{children}</div>
  </div>
);
