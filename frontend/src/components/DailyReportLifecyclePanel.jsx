/**
 * OMEGA · Phase 1A · iter452 · OC-002 Daily Report Office Review panel
 * Thin config wrapper around the shared <LifecyclePanel/>.
 */
import React from "react";
import { LifecyclePanel } from "@/components/LifecyclePanel";
import { Send, ClipboardCheck, Lock, Undo2 } from "lucide-react";
import { useT } from "@/lib/i18n";

export function DailyReportLifecyclePanel({ reportId }) {
  const { t } = useT();

  const config = {
    workflowKey: "daily-report",
    auditWorkflow: "daily_report",
    apiBase: "/daily-reports",
    title: t("Office Review Lifecycle"),
    stateLabels: {
      OPEN: t("Open (Field)"),
      PENDING_REVIEW: t("Pending Office Review"),
      REVIEWED: t("Reviewed"),
      CLOSED: t("Closed"),
    },
    statePill: {
      OPEN: "bg-amber-100 text-amber-900 border-amber-400",
      PENDING_REVIEW: "bg-blue-100 text-blue-900 border-blue-400",
      REVIEWED: "bg-violet-100 text-violet-900 border-violet-400",
      CLOSED: "bg-emerald-100 text-emerald-900 border-emerald-400",
    },
    transitionLabels: {
      PENDING_REVIEW: { label: t("Submit for Office Review"), Icon: Send },
      OPEN: { label: t("Return to Field"), Icon: Undo2 },
      REVIEWED: { label: t("Mark Reviewed"), Icon: ClipboardCheck },
      CLOSED: { label: t("Close Report"), Icon: Lock },
    },
    closureConfig: {
      targetState: "CLOSED",
      title: t("Close Daily Report"),
      description: t("Both attestations are required before close. This locks the report and feeds Payroll Variance verification."),
      flags: [
        { key: "office_review_complete", label: t("Office review complete (entries cross-checked)") },
        { key: "payroll_inputs_verified", label: t("Payroll inputs verified for this date") },
      ],
      submitLabel: t("Close Report"),
    },
    reopenConfig: {
      fromState: "CLOSED",
      targetStates: ["PENDING_REVIEW"],
      title: t("Reopen Daily Report"),
      description: t("A written reason is required. This will be recorded permanently in the audit trail."),
      placeholder: t("e.g. Discovered missing material entry after closeout."),
    },
    kickbackConfig: {
      fromState: "PENDING_REVIEW",
      toState: "OPEN",
      title: t("Return Daily Report to the Field"),
      description: t("A written reason is required so the foreman knows what to fix."),
      placeholder: t("e.g. Missing crew hours from foreman."),
    },
  };

  return <LifecyclePanel recordId={reportId} config={config} />;
}

export default DailyReportLifecyclePanel;
