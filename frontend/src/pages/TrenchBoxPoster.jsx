import React from "react";
import { Link } from "react-router-dom";
import { Printer, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { printReport, maybeAutoPrint } from "@/lib/printReport";
import { PrintWatermark } from "@/components/PrintWatermark";
import TrenchBoxPosterCard from "@/components/TrenchBoxPosterCard";

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
    <div className="min-h-screen blueprint-bg print:bg-white">
      <PrintWatermark />
      <div className="caution-stripe no-print" />

      <header className="bg-slate-900 border-b-4 border-red-700 no-print">
        <div className="max-w-5xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between gap-3">
          <Link
            to="/admin/trench-boxes"
            className="inline-flex items-center text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide"
            data-testid="poster-back"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("Home")}
          </Link>
          <div className="hidden sm:block font-mono text-xs uppercase tracking-[0.25em] text-red-400">
            {t("Trench Box QR Poster")}
          </div>
          <div className="flex items-center gap-2">
            <LangToggle />
            <Button
              onClick={printReport}
              className="h-10 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900"
              data-testid="poster-print-btn"
            >
              <Printer className="w-4 h-4 mr-2" /> {t("Print Poster")}
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-5 sm:px-8 py-8 print:p-0">
        <TrenchBoxPosterCard />
      </main>

      <style>{`
        @media print {
          @page { size: letter; margin: 0.4in; }
          body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
          .no-print { display: none !important; }
        }
      `}</style>
    </div>
  );
}
