// Public Trench Safety header — contextual back navigation + HOME.
//
// Sprint: Public Trench Safety UX Correction (post Phase 6, pre Phase 7).
//
// Pattern:
//   [ ← back to <context> ]   [ MASCI mark ]   [ HOME · LangToggle ]
//
// The contextual back link lets crews step one level out of the
// trench-safety stack without being yanked all the way to the
// MASCI landing page. HOME is preserved as an explicit, separate
// affordance per directive.
import React from "react";
import { useT } from "@/lib/i18n";
import { OperationalTopbar } from "@/components/public/OperationalPageFrame";

export default function PublicTrenchHeader({
  backTo = "/trench-safety",
  backLabel = "Back to Trench Safety",
  testIdPrefix = "trench-public",
  accent = "cyan", // cyan | amber | red
}) {
  const { t } = useT();

  return (
    <OperationalTopbar
      backTo={backTo}
      backLabel={t(backLabel)}
      accent={accent}
      familyLabel={t("MASCI Trench Safety")}
      familyMeta={t("Public trench workflow")}
      homeTo="/"
      showHomeLink
      showLangToggle
      testIdPrefix={testIdPrefix}
    />
  );
}
