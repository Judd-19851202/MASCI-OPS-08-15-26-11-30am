import React from "react";
import { Link } from "react-router-dom";
import { Printer, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { printReport, maybeAutoPrint } from "@/lib/printReport";
import { PrintWatermark } from "@/components/PrintWatermark";
import JhaPlansPosterCard from "@/components/JhaPlansPosterCard";

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
    <div className="min-h-screen blueprint-bg print:bg-white">
      <PrintWatermark />
      <div className="caution-stripe no-print" />

      <header className="bg-slate-900 border-b-4 border-amber-600 no-print">
        <div className="max-w-5xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between gap-3">
          <Link
            to="/admin/jha-plans"
            className="inline-flex items-center text-white hover:text-amber-300 text-sm font-bold uppercase tracking-wide"
            data-testid="jha-poster-back"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("Home")}
          </Link>
          <div className="hidden sm:block font-mono text-xs uppercase tracking-[0.25em] text-amber-400">
            {t("Job Hazard Plans QR Poster")}
          </div>
          <div className="flex items-center gap-2">
            <LangToggle />
            <Button
              onClick={printReport}
              className="h-10 bg-amber-600 hover:bg-amber-700 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-amber-800"
              data-testid="jha-poster-print-btn"
            >
              <Printer className="w-4 h-4 mr-2" /> {t("Print Poster")}
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-5 sm:px-8 py-8 print:p-0">
        <JhaPlansPosterCard />
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
