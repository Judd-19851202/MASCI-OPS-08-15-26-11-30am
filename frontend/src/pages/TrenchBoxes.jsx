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
          <Link to="/" className="inline-flex items-center min-h-[44px] -ml-2 px-2 text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide" data-testid="back-link">
            <ArrowLeft className="w-4 h-4 mr-1" /> Home
          </Link>
          <MasciLogo variant="mark" size="md" homeLink="/" />
          <LangToggle />
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-10">
        <div className="mb-6">
          <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-700">{t("Know Before You Dig")}</span>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-1">
            {t("Trench Box Tabulated Data")}
          </h1>
          <p className="text-slate-600 text-sm mt-2">
            {t("This is where your trench shield's life-safety data lives. Every box in the MASCI fleet has a manufacturer-engineered data sheet that tells you exactly how deep you can dig, in what soil, with what spreaders, and under what conditions. Read it. Understand it. It's the difference between a safe shift and a collapse.")}
          </p>
          <p className="text-slate-600 text-sm mt-2">
            <strong>{t("Start with the primer below")}</strong> {t("— a plain-English / Spanish walkthrough of what tabulated data is, why OSHA requires it, and how to read it in the field. Then open the")} <strong>{t("Tabulated Data Library")}</strong> {t("to grab the exact PDF for the shield you're using.")}
          </p>
        </div>

        <TabulatedDataPrimer />

        <TrenchBoxTabulatedLibrary adminMode={false} />
      </main>
    </div>
  );
}
