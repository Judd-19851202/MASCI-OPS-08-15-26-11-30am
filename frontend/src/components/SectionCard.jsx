// SectionCard.jsx — Pass-6 UX quality primitive.
//
// Canonical card wrapper for a form/filter "section" — header + body + footer.
// Provides consistent padding, border, header typography, and dedicated
// ActionFooter slot so action buttons live in a clearly defined place
// (right-aligned, separated by border) instead of floating mid-form.
//
// Usage:
//   <SectionCard
//     title="Filters"
//     subtitle="Narrow the report window"
//     accent="purple"
//     footer={
//       <ActionFooter
//         meta={<span>Window · 2026-05-25 → 2026-05-31</span>}
//         actions={[
//           <Button variant="outline">Export</Button>,
//           <Button>Apply</Button>,
//         ]}
//       />
//     }
//   >
//     <FormGrid>
//       <div>…</div><div>…</div>
//     </FormGrid>
//   </SectionCard>

import React from "react";
import { Card } from "./ui/card";

const ACCENTS = {
  purple: "border-purple-200 bg-purple-50/30",
  slate:  "border-slate-200 bg-white",
  amber:  "border-amber-300 bg-amber-50/30",
  emerald:"border-emerald-300 bg-emerald-50/30",
  red:    "border-red-300 bg-red-50/30",
};

export default function SectionCard({
  title,
  subtitle,
  accent = "slate",
  className = "",
  footer = null,
  children,
  ...rest
}) {
  const accentCls = ACCENTS[accent] || ACCENTS.slate;
  return (
    <Card className={`p-5 border-2 ${accentCls} ${className}`.trim()} {...rest}>
      {(title || subtitle) ? (
        <div className="mb-4">
          {title ? (
            <h2 className="font-display text-lg font-black text-slate-900 leading-tight">{title}</h2>
          ) : null}
          {subtitle ? (
            <p className="mt-1 text-sm text-slate-600">{subtitle}</p>
          ) : null}
        </div>
      ) : null}
      {children}
      {footer ? <div className="mt-5 pt-4 border-t border-slate-200">{footer}</div> : null}
    </Card>
  );
}

export function ActionFooter({ meta = null, actions = [], align = "between" }) {
  // align: "between" (meta left, actions right) | "end" (actions only, right-aligned)
  const wrapCls = align === "end"
    ? "flex justify-end gap-2"
    : "flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3";
  return (
    <div className={wrapCls} data-testid="action-footer">
      {align === "between" && meta ? (
        <div className="text-[11px] font-mono uppercase tracking-[0.2em] text-slate-500">
          {meta}
        </div>
      ) : null}
      {actions.length ? (
        <div className="flex gap-2 sm:ml-auto shrink-0">
          {actions.map((node, i) => React.cloneElement(node, { key: i }))}
        </div>
      ) : null}
    </div>
  );
}

export { SectionCard };
