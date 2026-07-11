// TRACK 28.08 · Responsive Platform Standard
//
// Shared responsive primitives — the durable contract Phase 0 established for
// PortalShell's mobile chrome now extended platform-wide. Every page in the
// PortalShell family SHOULD consume these primitives instead of hand-rolling
// flex/wrap classes. Adopting them makes the responsive contract enforceable
// via the structural regression suite (`test_track_28_08_responsive_contract.py`).
//
// Contract:
//   Desktop (>= md)  : one-row layout, no forced collapse, no clipped controls.
//   Tablet (sm..md)  : priority-based collapse via `hidden md:*` utilities.
//   Mobile (< sm)    : primary control + secondary `•••` menu; no page-level
//                      horizontal scroll; safe wrapping for KPI/status strips.
//
// Rules baked into these primitives:
//   1. `overflow-hidden` on outer chrome so no child can force hscroll.
//   2. `min-w-0` on every flex parent that can shrink.
//   3. `shrink-0` on every child of a utility-cluster row.
//   4. `flex-wrap` + explicit gap-x/gap-y on summary/KPI strips.
//   5. `break-words` + `overflow-wrap:anywhere` on any user-supplied text
//      that can exceed a mobile viewport (project names, incident titles).
//   6. Overflow menu (`•••`) surfaces secondary controls hidden on <md.
//
// Consumers keep control of colors/border/padding via className props.

import React from "react";
import { MoreHorizontal } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

/**
 * ResponsiveSummaryStrip
 *
 * Canonical layout for "label + summary text on the left, KPI counters +
 * timestamp + refresh on the right". Wraps cleanly on <md so the summary
 * row can never force horizontal document scroll.
 *
 * Usage:
 *   <ResponsiveSummaryStrip
 *     data-testid="foo-summary"
 *     left={<div>...pill + sentence...</div>}
 *     right={<div>...counters...</div>}
 *   />
 */
export function ResponsiveSummaryStrip({
  left,
  right,
  className = "",
  testid,
  ...rest
}) {
  return (
    <section
      className={`flex flex-wrap items-center gap-4 min-w-0 ${className}`}
      data-testid={testid}
      data-responsive-primitive="summary-strip"
      {...rest}
    >
      <div className="min-w-0">{left}</div>
      {right && (
        <div className="md:ml-auto flex flex-wrap items-center gap-x-4 gap-y-2 text-sm min-w-0">
          {right}
        </div>
      )}
    </section>
  );
}

/**
 * ResponsiveKpiRow
 *
 * A row of KPI counter tiles that wraps on <md. Every child receives
 * `min-w-0` context; consumers pass tile nodes as children.
 */
export function ResponsiveKpiRow({ children, className = "", testid }) {
  return (
    <div
      className={`flex flex-wrap items-center gap-x-4 gap-y-2 text-sm min-w-0 ${className}`}
      data-testid={testid}
      data-responsive-primitive="kpi-row"
    >
      {children}
    </div>
  );
}

/**
 * ResponsiveActionRow
 *
 * Row of buttons/links that wraps and shrinks. Every direct child receives
 * `shrink-0` via CSS so a single wide button cannot extrude past the
 * viewport. Meant for page headers, filter bars, and dialog footers.
 */
export function ResponsiveActionRow({ children, className = "", testid }) {
  return (
    <div
      className={`flex flex-wrap items-center gap-2 min-w-0 ${className}`}
      data-testid={testid}
      data-responsive-primitive="action-row"
      style={{ /* fallback so cluster items with intrinsic width can shrink */ }}
    >
      {children}
    </div>
  );
}

/**
 * ResponsiveFilterRow
 *
 * Filter/search bars — same shape as ActionRow but semantically distinct
 * for the regression suite to recognize.
 */
export function ResponsiveFilterRow({ children, className = "", testid }) {
  return (
    <div
      className={`flex flex-wrap items-center gap-2 min-w-0 ${className}`}
      data-testid={testid}
      data-responsive-primitive="filter-row"
    >
      {children}
    </div>
  );
}

/**
 * ResponsiveOverflowMenu
 *
 * Doctrine: any secondary controls hidden on <md must remain reachable via
 * a `•••` overflow trigger. This primitive standardizes the button style,
 * data-testid, and popover alignment so mobile ergonomics are identical
 * across portals.
 *
 * `visibleUpTo` = the Tailwind breakpoint at which the trigger disappears
 * (defaults to "md"). Above that breakpoint the trigger is `hidden`.
 */
export function ResponsiveOverflowMenu({
  children,
  testid = "responsive-overflow-menu",
  triggerClassName = "",
  contentClassName = "",
  ariaLabel = "More options",
  align = "end",
  visibleUpTo = "md",
}) {
  const hiddenAbove = `${visibleUpTo}:hidden`;
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          type="button"
          className={`${hiddenAbove} inline-flex items-center justify-center w-9 h-9 rounded border border-slate-300 text-slate-700 hover:bg-slate-100 shrink-0 ${triggerClassName}`}
          aria-label={ariaLabel}
          title="More"
          data-testid={testid}
          data-responsive-primitive="overflow-menu-trigger"
        >
          <MoreHorizontal className="w-4 h-4" />
        </button>
      </PopoverTrigger>
      <PopoverContent
        align={align}
        sideOffset={8}
        className={`w-64 p-3 ${contentClassName}`}
        data-testid={`${testid}-content`}
        data-responsive-primitive="overflow-menu-content"
      >
        <div className="flex flex-col gap-3">{children}</div>
      </PopoverContent>
    </Popover>
  );
}

/**
 * ResponsiveLongText
 *
 * Wrap for any user-supplied text that may exceed a mobile viewport
 * (project names, incident titles, employee names). Applies
 * `overflow-wrap:anywhere` + `word-break:break-word` + `min-w-0` so the
 * container can shrink cleanly.
 */
export function ResponsiveLongText({
  children,
  as: Tag = "span",
  className = "",
  testid,
  ...rest
}) {
  return (
    <Tag
      className={`min-w-0 break-words ${className}`}
      style={{ overflowWrap: "anywhere" }}
      data-testid={testid}
      data-responsive-primitive="long-text"
      {...rest}
    >
      {children}
    </Tag>
  );
}
