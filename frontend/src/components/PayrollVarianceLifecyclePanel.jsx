/**
 * OMEGA · Phase 1A · iter452 · OC-007 Payroll Variance Finalization panel
 * Thin config wrapper around the shared <LifecyclePanel/>.
 */
import React from "react";
import { LifecyclePanel } from "@/components/LifecyclePanel";
import { Search, BadgeCheck, Lock } from "lucide-react";

const CONFIG = {
  workflowKey: "payroll-variance",
  auditWorkflow: "payroll_variance",
  apiBase: "/hr/payroll-variance/batches",
  title: "Payroll Variance Lifecycle",

  stateLabels: {
    OPEN: "Open",
    UNDER_REVIEW: "Under Review",
    APPROVED: "Approved",
    FINALIZED: "Finalized",
  },
  statePill: {
    OPEN: "bg-amber-100 text-amber-900 border-amber-400",
    UNDER_REVIEW: "bg-blue-100 text-blue-900 border-blue-400",
    APPROVED: "bg-violet-100 text-violet-900 border-violet-400",
    FINALIZED: "bg-emerald-100 text-emerald-900 border-emerald-400",
  },
  transitionLabels: {
    UNDER_REVIEW: { label: "Begin Review", Icon: Search },
    APPROVED: { label: "Approve", Icon: BadgeCheck },
    FINALIZED: { label: "Finalize", Icon: Lock },
  },

  closureConfig: {
    targetState: "FINALIZED",
    title: "Finalize Payroll Variance Batch",
    description: (view) =>
      `NO AUTO FINALIZE. Three attestations are required.${
        view?.flagged_rows > 0
          ? ` ${view.flagged_rows} flagged row(s) detected — each must have an explicit decision.`
          : ""
      }`,
    flags: [
      { key: "review_complete", label: "Review complete" },
      { key: "approval_complete", label: "Approval complete" },
      {
        key: "variance_decisions_complete",
        label: "Every flagged variance row has a decision (approve / dispute)",
        emphasis: true,
      },
    ],
    submitLabel: "Finalize Batch",
  },

  reopenConfig: {
    fromState: "FINALIZED",
    targetStates: ["UNDER_REVIEW"],
    title: "Reopen Payroll Variance Batch",
    description: "A written reason is required. This will be recorded permanently in the audit trail.",
    placeholder: "e.g. Discovered overtime miscalculation after finalize.",
  },

  kickbackConfig: {
    fromState: "APPROVED",
    toState: "UNDER_REVIEW",
    title: "Return Batch to Review",
    description: "A written reason is required so reviewers can address the specific issue.",
    placeholder: "e.g. Flagged dispute requires more documentation.",
  },
};

export function PayrollVarianceLifecyclePanel({ batchId }) {
  return <LifecyclePanel recordId={batchId} config={CONFIG} />;
}

export default PayrollVarianceLifecyclePanel;
