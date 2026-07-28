// EmptyState.jsx — Iter B unification.
//
// Shared "no records / no results" surface used across every major
// list/table page. Replaces blank screens (87 pages had no explicit
// empty copy per the platform audit).
//
// Usage:
//   <EmptyState icon={Inbox} title="No POs yet" hint="Submit one from Field Leadership."
//               action={{ label: "New PO", onClick: openNew, testId: 'empty-new-po' }} />
import React from "react";
import { Inbox } from "lucide-react";
import { Button } from "@/components/ui/button";

export function EmptyState({
  icon: Icon = Inbox,
  title = "Nothing here yet",
  hint,
  action,
  className = "",
  testId = "empty-state",
}) {
  return (
    <div
      className={`flex flex-col items-center justify-center py-10 px-6 text-center bg-white rounded-md border-2 border-dashed border-slate-200 ${className}`}
      data-testid={testId}
    >
      <Icon className="w-10 h-10 text-slate-300 mb-3" strokeWidth={1.5} />
      <div className="text-sm font-semibold text-slate-800 mb-1">{title}</div>
      {hint && (
        <div className="text-sm text-slate-500 max-w-md leading-relaxed">
          {hint}
        </div>
      )}
      {action && (
        <Button
          size="sm"
          onClick={action.onClick}
          className="mt-4 text-xs"
          data-testid={action.testId || `${testId}-action`}
        >
          {action.label}
        </Button>
      )}
    </div>
  );
}

export default EmptyState;
