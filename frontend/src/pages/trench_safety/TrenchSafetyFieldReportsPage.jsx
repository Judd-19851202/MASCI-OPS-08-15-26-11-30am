// Trench Safety · Field Reports Inbox (page wrapper)
import React from "react";
import TrenchSafetyShell from "@/pages/trench_safety/TrenchSafetyShell";
import { SafetyFieldReports } from "@/pages/trench_safety/TrenchSafetyOpsCenter";
import { useT } from "@/lib/i18n";

export default function TrenchSafetyFieldReportsPage({ adminPortal = false }) {
  const { t } = useT();
  return (
    <TrenchSafetyShell active="field-reports" adminPortal={adminPortal}>
      <header className="mb-4">
        <h1 className="font-display text-3xl font-black tracking-tight text-slate-900" data-testid="fr-title">
          {t("Field Reports")}
        </h1>
        <p className="text-sm text-slate-600 mt-1">
          {t("Damage, unsafe conditions, missing pins, missing labels — every public report lands here for triage.")}
        </p>
      </header>
      <SafetyFieldReports adminPortal={adminPortal} />
    </TrenchSafetyShell>
  );
}
