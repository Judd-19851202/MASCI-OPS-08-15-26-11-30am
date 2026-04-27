import React from "react";
import { Link } from "react-router-dom";
import { Printer, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { printReport, maybeAutoPrint } from "@/lib/printReport";
import { PrintWatermark } from "@/components/PrintWatermark";
import CheatSheetCard from "@/components/CheatSheetCard";

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
    <div className="min-h-screen blueprint-bg print:bg-white">
      <PrintWatermark />
      <div className="caution-stripe no-print" />

      <header className="bg-slate-900 border-b-4 border-red-700 no-print">
        <div className="max-w-5xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between gap-3">
          <Link
            to="/"
            className="inline-flex items-center text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide"
            data-testid="cheatsheet-back"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("Hub")}
          </Link>
          <div className="hidden sm:block font-mono text-xs uppercase tracking-[0.25em] text-red-400">
            {t("Crew Cheat Sheet")}
          </div>
          <div className="flex items-center gap-2">
            <LangToggle />
            <Button
              onClick={printReport}
              className="h-10 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900"
              data-testid="cheatsheet-print-btn"
            >
              <Printer className="w-4 h-4 mr-2" /> {t("Print")}
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-5 sm:px-8 py-8 print:p-0">
        <CheatSheetCard />
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
