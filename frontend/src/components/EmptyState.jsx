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
import { EmptyState as GovernedEmptyState } from "@/components/ui/PortalStates";

export function EmptyState({
  icon: Icon = Inbox,
  title = "Nothing here yet",
  hint,
  body,
  message,
  explanation,
  action,
  className = "",
  testId = "empty-state",
  "data-testid": dataTestId,
}) {
  const resolvedBody = body || hint || message || explanation;

  return (
    <div className={className}>
      <GovernedEmptyState
        icon={Icon}
        title={title}
        body={resolvedBody}
        testId={dataTestId || testId}
        action={action ? (
          <Button
            size="sm"
            onClick={action.onClick}
            data-testid={action.testId || `${testId}-action`}
          >
            {action.label}
          </Button>
        ) : null}
      />
    </div>
  );
}

export default EmptyState;
