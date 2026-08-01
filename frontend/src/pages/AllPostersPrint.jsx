import React from "react";
import { Printer } from "lucide-react";
import { useT } from "@/lib/i18n";
import { maybeAutoPrint } from "@/lib/printReport";
import CheatSheetCard from "@/components/CheatSheetCard";
import TrenchBoxPosterCard from "@/components/TrenchBoxPosterCard";
import JhaPlansPosterCard from "@/components/JhaPlansPosterCard";
import { OperationalPrintPageFrame } from "@/components/public/OperationalPrintPageFrame";

/**
 * "Print all 3 site posters" combined page. Stacks the Cheat Sheet, Trench
 * Box QR, and Job Hazard Plans QR cards with a CSS page break between
 * each so a single Cmd+P → 3 letter-size sheets.
 *
 * Accepts ?autoprint=1 to fire the print dialog automatically — that's the
 * one-click experience triggered from the AdminHub Site Posters panel.
 */
export default function AllPostersPrint() {
  const { t } = useT();
  React.useEffect(() => {
    maybeAutoPrint();
  }, []);

  return (
    <OperationalPrintPageFrame
      testId="all-posters-page"
      accent="red"
      backTo="/admin"
      backLabel={t("Back to Admin")}
      familyLabel={t("MASCI Operations Platform")}
      familyMeta={t("Poster set")}
      heroIcon={Printer}
      kicker={t("Site Posters · Batch print")}
      title={t("All Site Posters")}
      description={t("Preview and print the full three-sheet trailer set in one pass: crew cheat sheet, trench-safety poster, and job hazard plans poster.")}
      printLabel={t("Print All Posters")}
      footerText={t("MASCI Operations Platform · Batch poster workflow")}
    >
        {/* Sheet 1 — Cheat Sheet (foreman) */}
        <div className="poster-sheet">
          <CheatSheetCard />
        </div>
        {/* Sheet 2 — Trench Box QR (excavation kits) */}
        <div className="poster-sheet mt-10 print:mt-0">
          <TrenchBoxPosterCard />
        </div>
        {/* Sheet 3 — Job Hazard Plans QR (job trailers) */}
        <div className="poster-sheet mt-10 print:mt-0">
          <JhaPlansPosterCard />
        </div>
      <style>{`
        @media print {
          .poster-sheet { page-break-after: always; break-after: page; }
          .poster-sheet:last-child { page-break-after: auto; break-after: auto; }
        }
      `}</style>
    </OperationalPrintPageFrame>
  );
}
