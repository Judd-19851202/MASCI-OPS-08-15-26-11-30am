// FilterBar.jsx — Phase V.5+ · Platform Filter Bar Doctrine.
//
// CANONICAL responsive grid for dense filter bars (4-col / 5-col).
// Replaces the legacy `grid grid-cols-2 md:grid-cols-{4,5} gap-x-4`
// pattern that produced 121-152px cell widths on tablet/iPad and
// visually mashed adjacent fields into "unreadable strips" per
// operator-verified production evidence.
//
// Doctrine: GLOBAL_FORM_LAYOUT_ROOT_CAUSE_REPORT.md
//
// Responsive contract:
//   • Phone portrait (<640px)      → 1 column stack
//   • Phone landscape / Tablet     → 2 columns (sm+)
//   • Desktop wide (≥1280px)       → full N columns (xl+)
//   • Horiz gap: 24px (gap-x-6) · Row gap: 12px (gap-y-3)
//
// Why xl: (1280px) instead of md: (768px)?
//   A 5-cell filter bar at iPad portrait 820px gives 131px cells —
//   unreadable for "Week Ending · Employee · Project# · Supervisor"
//   uppercase labels + date / text inputs. Operator-verified bleed.
//   Forcing 5-col only at xl ≥ 1280px guarantees ≥ 215px per cell.
//
// Why 24px gap instead of 16px?
//   16px is too tight when adjacent cells share the same row.
//   24px matches the form-row contract for visual coherence.
//
// Usage:
//   <FilterBar columns={5}>
//     <div>…filter 1…</div>
//     …
//   </FilterBar>

import React from "react";

export default function FilterBar({
  children,
  columns = 5,
  className = "",
  align = "end",  // "end" | "start" — vertical alignment of cells
}) {
  const colsClass = ({
    3: "xl:grid-cols-3",
    4: "xl:grid-cols-4",
    5: "xl:grid-cols-5",
    6: "xl:grid-cols-6",
  })[columns] || "xl:grid-cols-5";
  const alignClass = align === "end" ? "items-end" : "items-start";
  return (
    <div
      data-testid="filter-bar"
      className={`grid grid-cols-1 sm:grid-cols-2 ${colsClass} gap-x-6 gap-y-3 ${alignClass} ${className}`.trim()}
    >
      {children}
    </div>
  );
}

export { FilterBar };
