// FormGrid.jsx — Phase V.5 · Platform Form Layout Doctrine.
//
// CANONICAL responsive grid for form rows across every form on the
// platform. Replaces the legacy ad-hoc `grid grid-cols-1 sm:grid-cols-2
// gap-3` pattern that caused live iPad field-bleed in Daily Reports,
// Equipment / Operator forms, Safety Meetings, QA/QC inspections, etc.
//
// Doctrine: FORM_SPACING_DOCTRINE.md
//
// Responsive contract:
//   • Mobile (<768px)        → 1 column · 16px row gap
//   • iPad/Tablet (≥768px)   → 2 columns · 24px horiz gap · 16px row gap
//   • Desktop (≥1024px)      → 2 columns · 24px horiz gap · 16px row gap
//
// Why 24px horizontal gap?
//   Tailwind `gap-3` (12px) leaves only ~6px of safe space between
//   adjacent native iOS / iPadOS input borders once you factor in the
//   inputs' internal padding and the heavier WebKit chrome on iPad.
//   24px (`gap-x-6`) guarantees inputs never visually collide and
//   matches the platform's own card / section spacing rhythm.
//
// Why md: (768px) instead of sm: (640px)?
//   The 640px breakpoint forces 2-col on small phones in landscape
//   (e.g. iPhone Plus 736px), packing two inputs into ~310px each
//   minus padding — too tight, visually bleeds. 768px guarantees
//   iPad portrait (768 / 810 / 834px) gets clean 2-col without
//   risking phone-landscape squeeze.
//
// Usage:
//   <FormGrid>
//     <div>…input 1…</div>
//     <div>…input 2…</div>
//   </FormGrid>
//
//   // Optional override for compact rows (e.g. date + time pair):
//   <FormGrid compact>…</FormGrid>
//
//   // Optional full-width-on-tablet row:
//   <FormGrid stackUntil="lg">…</FormGrid>
//
// Notes:
//   • Do NOT add `gap-*` Tailwind classes inside FormGrid — the
//     component owns the gap rhythm.
//   • Children that should span both columns can opt-out via
//     `className="md:col-span-2"` on the child wrapper.
//   • No business logic. Pure layout primitive.

import React from "react";

/**
 * @param {Object}   props
 * @param {React.ReactNode} props.children
 * @param {string=}  props.className   — extra utility classes (e.g. mt-*).
 * @param {boolean=} props.compact     — reduce row gap from 16px → 12px
 *                                       (use only for tight date/time pairs).
 * @param {"sm"|"md"|"lg"=} props.stackUntil
 *                                     — breakpoint at which 2-col activates.
 *                                       Default "md" (768px). Use "lg" to
 *                                       keep iPad portrait in 1-col when
 *                                       inputs are visually heavy.
 */
export default function FormGrid({
  children,
  className = "",
  compact = false,
  stackUntil = "md",
}) {
  const colsClass = {
    sm: "sm:grid-cols-2",
    md: "md:grid-cols-2",
    lg: "lg:grid-cols-2",
  }[stackUntil] || "md:grid-cols-2";

  const rowGap = compact ? "gap-y-3" : "gap-y-4";

  return (
    <div
      data-testid="form-grid"
      className={`grid grid-cols-1 ${colsClass} gap-x-6 ${rowGap} ${className}`.trim()}
    >
      {children}
    </div>
  );
}

export { FormGrid };
