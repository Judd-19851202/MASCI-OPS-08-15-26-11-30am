import React from "react";
import { FileText } from "lucide-react";
import { useT } from "@/lib/i18n";
import { maybeAutoPrint } from "@/lib/printReport";
import JhaPlansPosterCard from "@/components/JhaPlansPosterCard";
import { OperationalPrintPageFrame } from "@/components/public/OperationalPrintPageFrame";

/**
 * Job Hazard Plans QR Poster — printable letter-size handout. Drops in
 * every job trailer so foremen can scan the QR and read the live Hazard
 * Plan PDF for their job before crew breaks ground.
 */
export default function JhaPlansPoster() {
  const { t } = useT();
  React.useEffect(() => {
    maybeAutoPrint();
  }, []);

  return (
    <OperationalPrintPageFrame
      testId="jha-poster-page"
      accent="amber"
      backTo="/admin/jha-plans"
      backLabel={t("Back to Hazard Plans")}
      familyLabel={t("MASCI Safety")}
      familyMeta={t("Poster route")}
      heroIcon={FileText}
      kicker={t("Hazard Plans · Printable poster")}
      title={t("Job Hazard Plans QR Poster")}
      description={t("A trailer poster that points crews to the live hazard-plan library for every active job before the first bucket breaks ground.")}
      printLabel={t("Print Poster")}
      footerText={t("MASCI Operations Platform · Hazard-plan poster workflow")}
    >
        <JhaPlansPosterCard />
    </OperationalPrintPageFrame>
  );
}
