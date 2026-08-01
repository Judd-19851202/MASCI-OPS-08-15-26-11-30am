import React from "react";
import { Box } from "lucide-react";
import { useT } from "@/lib/i18n";
import { maybeAutoPrint } from "@/lib/printReport";
import TrenchBoxPosterCard from "@/components/TrenchBoxPosterCard";
import { OperationalPrintPageFrame } from "@/components/public/OperationalPrintPageFrame";

/**
 * Trench Box QR Poster — printable letter-size handout. Card content lives
 * in <TrenchBoxPosterCard /> so it can be reused by the combined
 * /admin/posters/print-all page.
 */
export default function TrenchBoxPoster() {
  const { t } = useT();
  React.useEffect(() => {
    maybeAutoPrint();
  }, []);

  return (
    <OperationalPrintPageFrame
      testId="trench-poster-page"
      accent="red"
      backTo="/admin/trench-boxes"
      backLabel={t("Back to Trench Boxes")}
      familyLabel={t("MASCI Trench Safety")}
      familyMeta={t("Poster route")}
      heroIcon={Box}
      kicker={t("Trench Safety · Printable poster")}
      title={t("Trench Box QR Poster")}
      description={t("A field-safe poster for excavation kits: scan to open the live tabulated-data library, soil-type reminders, and trench-box primer.")}
      printLabel={t("Print Poster")}
      footerText={t("MASCI Operations Platform · Trench poster workflow")}
    >
        <TrenchBoxPosterCard />
    </OperationalPrintPageFrame>
  );
}
