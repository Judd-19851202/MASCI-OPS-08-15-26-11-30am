/**
 * OMEGA · Phase 1A · iter452 · OC-002 Daily Report Office Review panel
 * Thin config wrapper around the shared <LifecyclePanel/>.
 */
import React from "react";
import { LifecyclePanel } from "@/components/LifecyclePanel";
import { Send, ClipboardCheck, Lock, Undo2 } from "lucide-react";

const CONFIG = {
  workflowKey: "daily-report",
  auditWorkflow: "daily_report",
  apiBase: "/daily-reports",
  title: "Office Review Lifecycle",

  stateLabels: {
    OPEN: "Open (Field)",
    PENDING_REVIEW: "Pending Office Review",
    REVIEWED: "Reviewed",
    CLOSED: "Closed",
  },
  statePill: {
    OPEN: "bg-amber-100 text-amber-900 border-amber-400",
    PENDING_REVIEW: "bg-blue-100 text-blue-900 border-blue-400",
    REVIEWED: "bg-violet-100 text-violet-900 border-violet-400",
    CLOSED: "bg-emerald-100 text-emerald-900 border-emerald-400",
  },
  transitionLabels: {
    PENDING_REVIEW: { label: "Submit for Office Review", Icon: Send },
    OPEN: { label: "Return to Field", Icon: Undo2 },
    REVIEWED: { label: "Mark Reviewed", Icon: ClipboardCheck },
    CLOSED: { label: "Close Report", Icon: Lock },
  },

  closureConfig: {
    targetState: "CLOSED",
    title: "Close Daily Report",
    description: "Both attestations are required before close. This locks the report and feeds Payroll Variance verification.",
    flags: [
      { key: "office_review_complete", label: "Office review complete (entries cross-checked)" },
      { key: "payroll_inputs_verified", label: "Payroll inputs verified for this date" },
    ],
    submitLabel: "Close Report",
  },

  reopenConfig: {
    fromState: "CLOSED",
    targetStates: ["PENDING_REVIEW"],
    title: "Reopen Daily Report",
    description: "A written reason is required. This will be recorded permanently in the audit trail.",
    placeholder: "e.g. Discovered missing material entry after closeout.",
  },

  kickbackConfig: {
    fromState: "PENDING_REVIEW",
    toState: "OPEN",
    title: "Return Daily Report to the Field",
    description: "A written reason is required so the foreman knows what to fix.",
    placeholder: "e.g. Missing crew hours from foreman.",
  },
};

export function DailyReportLifecyclePanel({ reportId }) {
  return <LifecyclePanel recordId={reportId} config={CONFIG} />;
}

export default DailyReportLifecyclePanel;
