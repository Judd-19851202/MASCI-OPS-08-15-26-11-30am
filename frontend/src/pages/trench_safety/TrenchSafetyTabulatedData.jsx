// Tabulated Data — relocated under Safety → Trench Safety per Phase 3.
//
// This page composes the EXISTING TabulatedDataPrimer + TrenchBoxTabulatedLibrary
// components verbatim, so every uploaded PDF, every Spanish translation, every
// folder/scope, and the search/library behaviour remain identical. Only the
// chrome changes: the page now lives inside the Trench Safety shell with the
// tab strip + back-link.
//
// The legacy public /trench-boxes page continues to work; this surface
// adds a Safety-portal home for the same content under the new IA.
import React from "react";
import TrenchSafetyShell from "@/pages/trench_safety/TrenchSafetyShell";
import TabulatedDataPrimer from "@/components/TabulatedDataPrimer";
import TrenchBoxTabulatedLibrary from "@/components/TrenchBoxTabulatedLibrary";
import { useT } from "@/lib/i18n";

export default function TrenchSafetyTabulatedData() {
  const { t } = useT();
  return (
    <TrenchSafetyShell active="tabulated">
      <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900" data-testid="trench-tabdata-title">
        {t("Tabulated Data")}
      </h1>
      <p className="text-slate-600 text-sm max-w-3xl mt-1">
        {t("This is where your trench shield's life-safety data lives. Every box in the MASCI fleet has a manufacturer-engineered data sheet that tells you exactly how deep you can dig, in what soil, with what spreaders, and under what conditions. Read it. Understand it. It's the difference between a safe shift and a collapse.")}
      </p>
      <p className="text-slate-600 text-sm mt-2">
        <strong>{t("Start with the primer below")}</strong>{" "}
        {t("— a plain-English / Spanish walkthrough of what tabulated data is, why OSHA requires it, and how to read it in the field. Then open the")}{" "}
        <strong>{t("Tabulated Data Library")}</strong>{" "}
        {t("to grab the exact PDF for the shield you're using.")}
      </p>

      <div className="mt-6">
        <TabulatedDataPrimer />
      </div>

      <div className="mt-8">
        <TrenchBoxTabulatedLibrary adminMode={false} />
      </div>
    </TrenchSafetyShell>
  );
}
