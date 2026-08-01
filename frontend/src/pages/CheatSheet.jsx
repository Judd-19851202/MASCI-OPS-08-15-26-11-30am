import React from "react";
import { ClipboardCheck } from "lucide-react";
import { useT } from "@/lib/i18n";
import { maybeAutoPrint } from "@/lib/printReport";
import CheatSheetCard from "@/components/CheatSheetCard";
import { OperationalPrintPageFrame } from "@/components/public/OperationalPrintPageFrame";

/**
 * Crew Cheat Sheet — printable 1-page handout for foremen.
 * Card content lives in <CheatSheetCard /> so it can be reused by the
 * combined /admin/posters/print-all page.
 */
export default function CheatSheet() {
  const { t } = useT();
  React.useEffect(() => {
    maybeAutoPrint();
  }, []);

  return (
    <OperationalPrintPageFrame
      testId="cheatsheet-page"
      accent="red"
      backTo="/"
      backLabel={t("Back to Hub")}
      familyLabel={t("MASCI Operations Platform")}
      familyMeta={t("Field help")}
      heroIcon={ClipboardCheck}
      kicker={t("Field Help · Trailer Handout")}
      title={t("Crew Cheat Sheet")}
      description={t("The one-page field handout for site trailers: where to go, what to file, and what to do first when the day gets busy.")}
      printLabel={t("Print Cheat Sheet")}
      footerText={t("MASCI Operations Platform · Printable crew cheat sheet")}
    >
        <CheatSheetCard />
    </OperationalPrintPageFrame>
  );
}
