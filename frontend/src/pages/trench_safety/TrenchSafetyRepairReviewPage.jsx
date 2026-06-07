// Trench Safety · Safety Repair Review (page wrapper)
import React from "react";
import TrenchSafetyShell from "@/pages/trench_safety/TrenchSafetyShell";
import { SafetyRepairReview } from "@/pages/trench_safety/TrenchSafetyOpsCenter";
import { useT } from "@/lib/i18n";

export default function TrenchSafetyRepairReviewPage({ adminPortal = false }) {
  const { t } = useT();
  return (
    <TrenchSafetyShell active="repair-review" adminPortal={adminPortal}>
      <header className="mb-4">
        <h1 className="font-display text-3xl font-black tracking-tight text-slate-900" data-testid="rr-title">
          {t("Repair Review")}
        </h1>
        <p className="text-sm text-slate-600 mt-1">
          {t("Safety verifies every Shop repair before the asset returns to service.")}
        </p>
      </header>
      <SafetyRepairReview adminPortal={adminPortal} />
    </TrenchSafetyShell>
  );
}
