import React from "react";
import { SectionCard, PlaceholderPane } from "../_ui";
export default function SupervisorApprovalPanel({ draft }) {
  const state = draft?.supervisor_ai_approval_state || "unreviewed";
  return (
    <SectionCard id="panel-approval" title="Supervisor Approval" badge={state}>
      <PlaceholderPane testid="dr-v2-panel-approval-placeholder" note="Accept · Edit · Regenerate · Show Sources. Every action is written to ai_approval_log[]. Supervisor is the final source of truth." />
    </SectionCard>
  );
}
