// FilterBar.jsx — Phase V.5+ Pass-5 · Visual Quality Doctrine (final).
//
// CANONICAL responsive grid for filter bars.
//
// Doctrine: VISUAL_LAYOUT_QUALITY_CORRECTION_REPORT.md
//
// Responsive contract (Pass-5 final — operator visual standard):
//   • Phone portrait (<640px)           → 1 column stack
//   • Tablet+ (≥sm, 640px+)             → 2 columns ALWAYS
//
// Why 2-col MAX (not 3/4/5)?
//   Operator visual standard: filter cells must be ≥ 240 px wide
//   AND have visible breathing room. The page container is constrained
//   to `max-w-7xl` (1280 px) by HrPageShell / common shells. Even at
//   ultra-wide (2560 px) viewport, content area = 1280 px → 5-col
//   would give 166 px cells. NEVER meets the 240 px floor.
//
//   Therefore: 2-col is the maximum density that produces readable,
//   breathing filter cells across every viewport.
//
// Numbers (filter cells, accounting for sidebar + padding):
//   • phone 390px:        1 col @ 350 px
//   • phone landscape:    2 col @ ~370 px each
//   • iPad portrait 820:  2 col @ ~350 px each
//   • iPad landscape:     2 col @ ~400 px each
//   • laptop 1366:        2 col @ ~450 px each
//   • desktop 1920+:      2 col @ ~600+ px each
//
// `columns` prop is now ignored — kept for API compatibility.

import React from "react";

export default function FilterBar({
  children,
  className = "",
  align = "end",
  // columns prop retained for compat but ignored — doctrine is 2-col max
   
  columns,
}) {
  const alignClass = align === "end" ? "items-end" : "items-start";
  return (
    <div
      data-testid="filter-bar"
      className={`grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 ${alignClass} ${className}`.trim()}
    >
      {children}
    </div>
  );
}

export { FilterBar };
