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
import { OperationalPageFrame } from "@/components/public/OperationalPageFrame";
import { OperationalStatusBadge } from "@/components/public/OperationalStatusBadge";
import TabulatedDataPrimer from "@/components/TabulatedDataPrimer";
import TrenchBoxTabulatedLibrary from "@/components/TrenchBoxTabulatedLibrary";
import { useT } from "@/lib/i18n";

export default function PublicTrenchSafetyTabulatedData() {
  const { t } = useT();
  return (
    <OperationalPageFrame
      testId="public-tabdata-page"
      backTo="/trench-safety"
      backLabel={t("Back to Trench Safety")}
      accent="cyan"
      familyLabel={t("MASCI Trench Safety")}
      familyMeta={t("Public trench workflow")}
      mainWidthClass="max-w-5xl"
      heroIcon={BookOpen}
      kicker={t("MASCI Trench Safety · Tabulated Data")}
      title={t("Tabulated Data Library")}
      description={t("Open the manufacturer-engineered trench box and panel sheets crews need before entry: soil-type limits, spreader configurations, and shield depth ratings by exact asset family.")}
      heroMeta={(
        <>
          <OperationalStatusBadge tone="cyan" testId="public-tabdata-meta-library">{t("Engineered PDFs")}</OperationalStatusBadge>
          <OperationalStatusBadge tone="amber" testId="public-tabdata-meta-osha">{t("OSHA-aligned")}</OperationalStatusBadge>
        </>
      )}
      heroAside={(
        <div className="wp17-panel p-4" data-testid="public-tabdata-hero-aside">
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold mb-2">{t("Need hazard guidance?")}</div>
          <p className="text-sm text-slate-600 mb-3">
            {t("Use this library for the engineered sheet. For stop-work reminders, missing-pin guidance, or crew coaching, open Safety References.")}
          </p>
          <Link to="/trench-safety/references" className="inline-flex items-center gap-1.5 rounded-full border border-cyan-200 bg-cyan-50 px-4 py-2 text-[11px] font-mono font-bold uppercase tracking-[0.18em] text-cyan-800" data-testid="public-tabdata-hero-refs">
            {t("Open Safety References")} <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}
      footerText={t("MASCI Operations Platform · Tabulated-data workflow")}
    >
      <div className="space-y-5">

        <div className="rounded-[1.5rem] border border-amber-300 bg-amber-50 p-4 flex items-start gap-3 shadow-[0_18px_40px_rgba(15,23,42,0.06)]" data-testid="public-tabdata-coaching">
          <ShieldAlert className="w-4 h-4 text-amber-700 mt-0.5 shrink-0" />
          <p className="text-sm text-amber-900">
            <strong>{t("Match the box to the right sheet.")}</strong>{" "}
            {t("Tabulated data is specific to the manufacturer, model, soil type, and configuration. If you can't find the sheet that matches the box on site, stop and contact Safety.")}
          </p>
        </div>

        <div className="wp17-panel p-4 flex items-start gap-2" data-testid="public-tabdata-cross-link">
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

        <section className="wp17-panel p-4 text-xs text-slate-600" data-testid="public-tabdata-qr-help">
          <ScanLine className="w-3.5 h-3.5 inline mr-1 -mt-0.5 text-cyan-700" />
          <strong className="text-slate-700">{t("QR Scan:")}</strong>{" "}
          {t("Scanning the QR on any MASCI trench box opens its asset record with a direct link to its tabulated data. Scanning does not move the asset.")}
        </section>
      </div>
    </OperationalPageFrame>
  );
}
