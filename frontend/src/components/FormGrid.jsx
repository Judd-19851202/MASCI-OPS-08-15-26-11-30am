// FormGrid.jsx — Phase V.5+ · Platform Form Layout Doctrine (revised).
//
// CANONICAL responsive grid for form rows. Replaces the legacy
// `grid grid-cols-1 sm:grid-cols-2 gap-3` pattern AND the prior
// `md:grid-cols-2 gap-x-6` pattern (which still bled on iPad
// portrait per operator-verified production evidence).
//
// Doctrine: GLOBAL_FORM_LAYOUT_ROOT_CAUSE_REPORT.md
//
// Responsive contract (revised after operator-verified bleed on
// iPad portrait at md:768px):
//   • Mobile (<1024px)        → 1 column · 16px row gap
//   • Desktop (≥1024px)       → 2 columns · 32px horiz gap · 16px row gap
//
// Why lg: (1024px) instead of md: (768px)?
//   At iPad portrait 820px width, md:grid-cols-2 produces 345px
//   columns. Mathematically that's ~24px between adjacent input
//   borders — fine on paper, but operator-verified field evidence
//   (mascidocs.com production · iPad Safari) showed the WebKit
//   native input chrome + uppercase monospace labels visually fuse
//   adjacent inputs at this column width. Stacking on iPad portrait
//   eliminates the bleed entirely.
//
// Why gap-x-8 (32px) instead of gap-x-6 (24px)?
//   24px is the bare minimum to clear adjacent native input borders.
//   32px adds proper visual breathing room and makes the row read
//   as two distinct fields rather than one continuous strip.
//
// Usage:
//   <FormGrid>
//     <div>…input 1…</div>
//     <div>…input 2…</div>
//   </FormGrid>
//
//   // 3-col variant (e.g. date / time / duration triplets):
//   <FormGrid columns={3}>…</FormGrid>
//
//   // Tight row gap (compact pairs):
//   <FormGrid compact>…</FormGrid>
//
// Notes:
//   • Do NOT add `gap-*` Tailwind classes inside FormGrid.
//   • Children that should span both columns can opt-out via
//     `className="lg:col-span-2"` on the child wrapper.
//   • For dense 4-5 column filter bars, use <FilterBar> not <FormGrid>.

import React from "react";

export default function FormGrid({
  children,
  className = "",
  compact = false,
  columns = 2,
}) {
  const colsClass = columns === 3 ? "lg:grid-cols-3" : "lg:grid-cols-2";
  const rowGap = compact ? "gap-y-3" : "gap-y-4";
  return (
    <div
      data-testid="form-grid"
      className={`grid grid-cols-1 ${colsClass} gap-x-8 ${rowGap} ${className}`.trim()}
    >
      {children}
    </div>
  );
}

export { FormGrid };
