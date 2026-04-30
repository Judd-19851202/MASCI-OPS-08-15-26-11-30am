import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import TabulatedDataPrimer from "@/components/TabulatedDataPrimer";
import TrenchBoxTabulatedLibrary from "@/components/TrenchBoxTabulatedLibrary";

export default function TrenchBoxes() {
  const { t } = useT();

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
          <Link to="/" className="inline-flex items-center text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide" data-testid="back-link">
            <ArrowLeft className="w-4 h-4 mr-1" /> Hub
          </Link>
          <MasciLogo variant="mark" size="md" homeLink="/" />
          <LangToggle />
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-10">
        <div className="mb-6">
          <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-700">{t("Trench Box Tabulated Data")}</span>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-1">
            {t("OSHA-compliant trench shields in MASCI fleet")}
          </h1>
          <p className="text-slate-600 text-sm mt-2">
            {t("Tap any box to see its size, weight, and maximum allowable depth by soil type (OSHA 1926 Subpart P).")}
          </p>
        </div>

        <TabulatedDataPrimer />

        <TrenchBoxTabulatedLibrary adminMode={false} />
      </main>
    </div>
  );
}
