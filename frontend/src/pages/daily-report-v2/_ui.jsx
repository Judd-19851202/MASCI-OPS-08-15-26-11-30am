import React from "react";

/**
 * DR-ROI-001F · Platform-aligned V2 UI primitives.
 *
 * These primitives are the ONLY chrome used by the Daily Report V2
 * shell + section files. They render in the same visual language as
 * the rest of the ForgedOps platform:
 *   · white cards on slate-50 canvas
 *   · slate-200 borders / rounded-2xl radius
 *   · font-mono uppercase micro-labels in slate-700
 *   · red-700 primary accent
 *   · h-12 platform inputs, focus-visible ring
 *
 * Absolutely no AI/agent branding · no dark right rail · no bespoke
 * one-off styling.
 */
export function SectionCard({ id, title, badge, description, action, children }) {
  return (
    <section
      id={id}
      data-testid={`dr-v2-section-${id}`}
      className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6 space-y-4 shadow-sm"
    >
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div className="min-w-0">
          <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
          {description ? (
            <p className="text-sm text-slate-600 mt-1 max-w-2xl">{description}</p>
          ) : null}
        </div>
        <div className="flex items-center gap-2">
          {badge ? (
            <span
              className="text-[10px] font-mono uppercase tracking-[0.2em] rounded-full border border-slate-300 bg-slate-50 text-slate-700 px-2 py-0.5"
              data-testid={`dr-v2-badge-${id}`}
            >
              {badge}
            </span>
          ) : null}
          {action || null}
        </div>
      </div>
      {children}
    </section>
  );
}

/** Empty / placeholder state that matches the platform empty-state look. */
export function PlaceholderPane({ testid, note }) {
  return (
    <div
      className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-sm text-slate-600"
      data-testid={testid}
    >
      {note}
    </div>
  );
}

/** Platform-aligned label above form fields. */
export function FieldLabel({ children, htmlFor }) {
  return (
    <label
      htmlFor={htmlFor}
      className="block font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700"
    >
      {children}
    </label>
  );
}

/** Platform-aligned text input (h-12, red-700 focus ring). */
export const inputCls =
  "h-12 w-full rounded-md border-2 border-slate-300 bg-white px-3 text-base " +
  "text-slate-900 placeholder:text-slate-400 " +
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-600 " +
  "focus-visible:ring-offset-2 disabled:bg-slate-100";

/** Platform-aligned select input. Same visual grammar as inputCls. */
export const selectCls = inputCls;

/** Platform primary button (red-700 solid). */
export const primaryBtn =
  "inline-flex items-center gap-1 rounded-md bg-red-700 hover:bg-red-600 " +
  "text-white text-sm font-semibold px-4 h-11 disabled:bg-red-300 " +
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-600 focus-visible:ring-offset-2";

/** Platform secondary button (outline). */
export const secondaryBtn =
  "inline-flex items-center gap-1 rounded-md border-2 border-slate-300 " +
  "bg-white hover:bg-slate-100 text-slate-800 text-sm font-semibold px-4 h-11 " +
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-600 focus-visible:ring-offset-2";

/** Ghost / text-only button. */
export const ghostBtn =
  "inline-flex items-center gap-1 rounded-md px-3 h-9 text-sm font-semibold " +
  "text-slate-700 hover:bg-slate-100 " +
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-600 focus-visible:ring-offset-2";

/** Add-item dashed CTA (matches V1 daily report "+ Add" affordance). */
export const addItemBtn =
  "w-full h-12 rounded-md border-2 border-dashed border-slate-400 " +
  "bg-white text-slate-700 hover:border-red-700 hover:text-red-700 " +
  "font-bold uppercase tracking-wide text-sm " +
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-600";

/** Chip / status pill. */
export function StatusChip({ tone = "slate", children, testid }) {
  const map = {
    slate: "border-slate-300 bg-slate-50 text-slate-700",
    green: "border-emerald-300 bg-emerald-50 text-emerald-800",
    amber: "border-amber-300 bg-amber-50 text-amber-800",
    red: "border-red-300 bg-red-50 text-red-800",
    blue: "border-sky-300 bg-sky-50 text-sky-800",
  };
  return (
    <span
      className={`inline-flex items-center rounded-full border text-[11px] font-medium uppercase tracking-wider px-2 py-0.5 ${map[tone] || map.slate}`}
      data-testid={testid}
    >
      {children}
    </span>
  );
}

export default { SectionCard, PlaceholderPane, FieldLabel, StatusChip };
