// Public Trench Safety · Tabulated Data
//
// Sprint: Public Trench Safety UX Correction.
//
// This is the field-facing tabulated-data surface. It composes the
// existing TabulatedDataPrimer + TrenchBoxTabulatedLibrary unchanged
// (every uploaded PDF, every Spanish translation, every folder/scope
// remains identical). Only the chrome changes — contextual back to
// /trench-safety and field-first coaching.
//
// Distinct from /trench-safety/references — that surface holds OSHA
// guidance, competent-person reminders, stop-work, and unsafe-condition
// examples; this surface holds the engineered PDFs and load limits.
//
// Route: /trench-safety/tabulated-data  (public, no auth)
import React from "react";
import { Link } from "react-router-dom";
import { BookOpen, ScanLine, ShieldAlert, ArrowRight, FileWarning } from "lucide-react";
import PublicTrenchHeader from "@/components/trench/PublicTrenchHeader";
import TabulatedDataPrimer from "@/components/TabulatedDataPrimer";
import TrenchBoxTabulatedLibrary from "@/components/TrenchBoxTabulatedLibrary";
import { useT } from "@/lib/i18n";

export default function PublicTrenchSafetyTabulatedData() {
  const { t } = useT();
  return (
    <div className="min-h-screen bg-slate-50" data-testid="public-tabdata-page">
      <div className="caution-stripe" />
      <PublicTrenchHeader
        backTo="/trench-safety"
        backLabel="Back to Trench Safety"
        testIdPrefix="public-tabdata"
        accent="cyan"
      />

      <main className="max-w-3xl mx-auto px-4 sm:px-6 py-5">
        <div className="text-center mb-4">
          <BookOpen className="w-7 h-7 mx-auto text-cyan-700" />
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-cyan-700 font-bold mt-1">
            {t("MASCI Trench Safety")} · {t("Tabulated Data")}
          </div>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-1" data-testid="public-tabdata-title">
            {t("Tabulated Data Library")}
          </h1>
          <p className="text-slate-600 text-sm max-w-2xl mx-auto mt-2">
            {t("Manufacturer-engineered, OSHA-compliant data for every MASCI trench box. Per-box PDFs, soil-type limits, spreader configurations, and shield depth ratings.")}
          </p>
        </div>

        <div className="bg-amber-50 border border-amber-300 rounded-md p-3 flex items-start gap-2 mb-5" data-testid="public-tabdata-coaching">
          <ShieldAlert className="w-4 h-4 text-amber-700 mt-0.5 shrink-0" />
          <p className="text-sm text-amber-900">
            <strong>{t("Match the box to the right sheet.")}</strong>{" "}
            {t("Tabulated data is specific to the manufacturer, model, soil type, and configuration. If you can't find the sheet that matches the box on site, stop and contact Safety.")}
          </p>
        </div>

        <div className="bg-white border border-slate-200 rounded-md p-3 mb-5 flex items-start gap-2" data-testid="public-tabdata-cross-link">
          <FileWarning className="w-4 h-4 text-cyan-700 mt-0.5 shrink-0" />
          <div className="text-xs text-slate-700">
            {t("Looking for OSHA general guidance, competent-person reminders, or what to do if pins/labels are missing?")}{" "}
            <Link to="/trench-safety/references" className="text-cyan-800 underline font-bold inline-flex items-center gap-0.5" data-testid="public-tabdata-to-refs">
              {t("Open Safety References")} <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
        </div>

        <TabulatedDataPrimer />

        <div className="mt-8">
          <TrenchBoxTabulatedLibrary adminMode={false} />
        </div>

        <section className="mt-8 p-3 border border-slate-200 bg-white rounded text-xs text-slate-600" data-testid="public-tabdata-qr-help">
          <ScanLine className="w-3.5 h-3.5 inline mr-1 -mt-0.5 text-cyan-700" />
          <strong className="text-slate-700">{t("QR Scan:")}</strong>{" "}
          {t("Scanning the QR on any MASCI trench box opens its asset record with a direct link to its tabulated data. Scanning does not move the asset.")}
        </section>

        <footer className="mt-8 text-center text-[10px] uppercase tracking-[0.2em] text-slate-400 font-mono">
          {t("MASCI Operations Platform")} · {t("Field-safe view")}
        </footer>
      </main>
    </div>
  );
}
