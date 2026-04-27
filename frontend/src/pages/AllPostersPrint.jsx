import React from "react";
import { Link } from "react-router-dom";
import { Printer, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { printReport, maybeAutoPrint } from "@/lib/printReport";
import { PrintWatermark } from "@/components/PrintWatermark";
import CheatSheetCard from "@/components/CheatSheetCard";
import TrenchBoxPosterCard from "@/components/TrenchBoxPosterCard";
import JhaPlansPosterCard from "@/components/JhaPlansPosterCard";

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
    <div className="min-h-screen blueprint-bg print:bg-white">
      <PrintWatermark />
      <div className="caution-stripe no-print" />

      <header className="bg-slate-900 border-b-4 border-red-700 no-print">
        <div className="max-w-5xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between gap-3">
          <Link
            to="/admin"
            className="inline-flex items-center text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide"
            data-testid="all-posters-back"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("Admin")}
          </Link>
          <div className="hidden sm:block font-mono text-xs uppercase tracking-[0.25em] text-red-400">
            {t("All Site Posters · Print 3 sheets")}
          </div>
          <div className="flex items-center gap-2">
            <LangToggle />
            <Button
              onClick={printReport}
              className="h-10 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900"
              data-testid="all-posters-print-btn"
            >
              <Printer className="w-4 h-4 mr-2" /> {t("Print All Posters")}
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-5 sm:px-8 py-8 print:p-0">
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
      </main>

      <style>{`
        @media print {
          @page { size: letter; margin: 0.4in; }
          body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
          .no-print { display: none !important; }
          /* Force each poster onto its own sheet */
          .poster-sheet { page-break-after: always; break-after: page; }
          .poster-sheet:last-child { page-break-after: auto; break-after: auto; }
        }
      `}</style>
    </div>
  );
}
