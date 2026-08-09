// Phase 10A-B · OSHA Coaching Block (Correction 6)
//
// Contextual coaching strip shown next to OSHA decision points on the
// Public Excavation form. Renders the six standard sections:
//   • Why This Matters
//   • OSHA Requirement
//   • Example
//   • Common Mistakes
//   • When To Escalate
//   • If Unsure
//
// Field-first, non-punitive, superintendent-friendly. Collapsible by
// default so the form stays scan-friendly on a phone.
import React from "react";
import { ShieldAlert } from "lucide-react";
import { useT } from "@/lib/i18n";
import { WorkflowCoachingDisclosure } from "@/components/WorkflowCoachingDisclosure";

export default function OshaCoachingBlock({ title, why, requirement, example, mistakes, escalate, ifUnsure, testId, tone = "amber" }) {
  const { t } = useT();

  return (
    <WorkflowCoachingDisclosure
      title={`${t("OSHA Coaching")} · ${t(title)}`}
      description={t(why)}
      icon={ShieldAlert}
      testIdPrefix={testId}
      containerTestId={testId}
      triggerTestId={`${testId}-toggle`}
      panelTestId={`${testId}-body`}
      collapsedCounterLabel={`${t("OSHA Coaching")} · ${t(title)}`}
      defaultOpen={false}
      blocks={[
        { label: t("Why This Matters"), body: t(why), tone, testId: `${testId}-why` },
        requirement ? { label: t("OSHA Requirement"), body: t(requirement), tone, testId: `${testId}-requirement` } : null,
        example ? { label: t("Example"), body: t(example), tone, testId: `${testId}-example` } : null,
        mistakes ? { label: t("Common Mistakes"), body: t(mistakes), tone, testId: `${testId}-mistakes` } : null,
        escalate ? { label: t("When To Escalate"), body: t(escalate), tone, testId: `${testId}-escalate` } : null,
        ifUnsure ? { label: t("If Unsure"), body: t(ifUnsure), tone, testId: `${testId}-if-unsure` } : null,
      ].filter(Boolean)}
    />
  );
}
