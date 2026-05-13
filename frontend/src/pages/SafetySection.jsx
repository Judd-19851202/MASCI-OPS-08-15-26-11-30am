import React from "react";
import { Link } from "react-router-dom";
import {
  ClipboardCheck, Users, AlertOctagon, FileText, Box, ArrowLeft, Shield, ShieldCheck, IdCard,
} from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { LangToggle } from "@/components/LangToggle";
import { SectionTile } from "@/components/SectionTile";
import { useT } from "@/lib/i18n";

// All Safety tiles use the unified `SectionTile` so they match the main
// Hub tiles exactly. CTA labels differentiate forms vs. libraries:
//   forms     → "Start Form"
//   libraries → "Open Plans" / "Open Library" / "Open Cards"

/**
 * SafetySection — landing for the /safety sub-hub. Compliance-first forms
 * that feed into the Admin dashboards and the auto-email pipeline.
 */
export default function SafetySection() {
  const { t } = useT();

  return (
    <div className="min-h-screen blueprint-bg">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <MasciLogo variant="lockup" size="xl" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
          <div className="flex items-center gap-2">
            <LangToggle />
            <CompanyInfoDialog />
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-8 sm:py-12">
        <div className="mb-6">
          <Link
            to="/"
            className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.2em] text-slate-600 hover:text-red-700 font-bold"
            data-testid="safety-back-link"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> MASCI Hub
          </Link>
        </div>

        <div className="mb-10 sm:mb-14 flex items-start gap-4">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-md bg-red-700 text-white shrink-0">
            <Shield className="w-7 h-7" />
          </div>
          <div className="flex-1">
            <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-700 font-bold">
              {t("Safety · Compliance")}
            </span>
            <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tight text-slate-900 mt-1">
              {t("Safety")}
            </h1>
            <p className="text-slate-600 text-base sm:text-lg mt-2 max-w-2xl">
              {t("Every form your crews need to stay OSHA-compliant and keep the company defensible.")}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5 mb-12">
          <SectionTile
            to="/inspections/submit"
            icon={ClipboardCheck}
            title={t("Site Inspections")}
            desc={t("Daily and weekly job-site safety inspections. PPE, MOT, fall protection, electrical, and more — graded automatically.")}
            accent="red"
            ctaLabel={t("Start Form")}
            testId="safety-tile-inspections"
          />
          <SectionTile
            to="/meetings/submit"
            icon={Users}
            title={t("Safety Meetings")}
            desc={t("Toolbox talks and daily huddles. 80+ heavy-civil topics with prefilled hazards — every crew member signs in.")}
            accent="slate"
            ctaLabel={t("Start Form")}
            testId="safety-tile-meetings"
          />
          <SectionTile
            to="/incidents/submit"
            icon={AlertOctagon}
            title={t("Incident Reports")}
            desc={t("Document near misses, injuries, and damage. Severity tiers, root cause, witnesses, and follow-up — all in one record.")}
            accent="redDeep"
            ctaLabel={t("Start Form")}
            testId="safety-tile-incidents"
          />
          <SectionTile
            to="/jha"
            icon={FileText}
            title={t("Job Hazard Plans")}
            desc={t("Read your job's Hazard Plan PDF before crew breaks ground. One plan per active MASCI job — uploaded by the office.")}
            accent="amber"
            ctaLabel={t("Open Plans")}
            testId="safety-tile-jha"
          />
          <SectionTile
            to="/trench-boxes"
            icon={Box}
            title={t("Trench Box Tabulated Data")}
            desc={t("Learn what tabulated data is, why it keeps you alive, and pull the exact manufacturer data sheet for every shield in the MASCI fleet — bilingual.")}
            accent="slate"
            ctaLabel={t("Open Library")}
            testId="safety-tile-trench"
          />
          <SectionTile
            to="/safety/cards"
            icon={IdCard}
            title={t("Field Safety Cards")}
            desc={t("Bilingual wallet-sized safety cards — English and Español, front and back. Print on letter paper or email the PDF straight to the crew.")}
            accent="redDeep"
            ctaLabel={t("Open Cards")}
            testId="safety-tile-cards"
          />
          <SectionTile
            to="/safety/forms"
            icon={ShieldCheck}
            title={t("Safety Forms")}
            desc={t("Equipment Issuance & Accountability + Use & Care Training documentation — password-gated for the Safety Department.")}
            accent="redDeep"
            ctaLabel={t("Open Forms")}
            testId="safety-tile-forms"
          />
        </div>
      </main>

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-8 text-center font-mono text-xs uppercase tracking-[0.2em] text-slate-500 border-t-2 border-slate-200">
        {t("MASCI · Safety")}
      </footer>
    </div>
  );
}
