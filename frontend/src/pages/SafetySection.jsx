// iter321 · Safety Section Calm Pass (Safety tile governance closure).
//
// The /safety landing — public OSHA-compliance form surface used by
// crews. Converged to the platform family contract: left-edge stripe
// tiles · interior H1 size · matched section heading style · uppercase
// CTAs. All 7 tile testids preserved.

import React from "react";
import { Link } from "react-router-dom";
import {
  ClipboardCheck, Users, AlertOctagon, FileText, Box, ArrowLeft, Shield, ShieldCheck, IdCard,
} from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";

const STRIPE = {
  red:     "border-l-red-600",
  redDeep: "border-l-red-900",
  amber:   "border-l-amber-500",
  emerald: "border-l-emerald-600",
  slate:   "border-l-slate-500",
  cyan:    "border-l-cyan-600",
};
const BTN = {
  red:     "bg-red-700 hover:bg-red-800",
  redDeep: "bg-red-900 hover:bg-red-950",
  amber:   "bg-amber-700 hover:bg-amber-800",
  emerald: "bg-emerald-700 hover:bg-emerald-800",
  slate:   "bg-slate-700 hover:bg-slate-800",
  cyan:    "bg-cyan-700 hover:bg-cyan-800",
};

function SafetyTile({ to, icon: Icon, title, desc, accent = "red", ctaLabel, testId }) {
  const stripe = STRIPE[accent] || STRIPE.red;
  const btn = BTN[accent] || BTN.red;
  return (
    <Link
      to={to}
      className={`block rounded-lg border border-slate-200 border-l-4 ${stripe} bg-white p-5 hover:shadow-md hover:-translate-y-0.5 hover:border-slate-300 transition-all duration-150 relative`}
      data-testid={testId}
    >
      <div className="flex items-start gap-3">
        <Icon className="w-6 h-6 mt-1 text-slate-700 shrink-0" />
        <div className="flex-1 min-w-0">
          <h3 className="font-display text-lg font-black">{title}</h3>
          <p className="text-sm text-slate-600 mt-1">{desc}</p>
          <span className={`mt-3 inline-flex items-center h-9 px-3 rounded-md ${btn} text-white font-bold uppercase tracking-wide text-xs`}>
            {ctaLabel} →
          </span>
        </div>
      </div>
    </Link>
  );
}

export default function SafetySection() {
  const { t } = useT();

  return (
    <div className="min-h-screen blueprint-bg">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <MasciLogo variant="mark" size="lg" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
          <div className="flex items-center gap-2">
            <LangToggle />
            <CompanyInfoDialog />
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-8">
        <div className="mb-6">
          <Link
            to="/"
            className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.22em] text-slate-600 hover:text-red-700 font-bold"
            data-testid="safety-back-link"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> {t("Home")}
          </Link>
        </div>

        <div className="mb-8 flex items-start gap-4">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-red-700 text-white shrink-0">
            <Shield className="w-6 h-6" />
          </div>
          <div className="flex-1">
            <span className="font-mono text-xs uppercase tracking-[0.22em] text-red-700 font-bold">
              {t("Safety · Compliance")}
            </span>
            <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-1">
              {t("Safety")}
            </h1>
            <p className="text-slate-600 text-base mt-2 max-w-2xl">
              {t("Every form your crews need to stay OSHA-compliant and keep the company defensible.")}
            </p>
          </div>
        </div>

        <div className="mb-4 flex items-baseline gap-3 flex-wrap" data-testid="safety-section-heading">
          <h2 className="font-mono text-xs uppercase tracking-[0.22em] text-slate-700">
            {t("Compliance Forms & References")}
          </h2>
          <span className="hidden sm:inline-block h-px flex-1 bg-slate-200" aria-hidden="true" />
          <span className="text-xs text-slate-500 italic">
            {t("Crew-facing OSHA forms · job hazard plans · field references")}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-12">
          <SafetyTile
            to="/safety/inspections/new"
            icon={ClipboardCheck}
            title={t("Site Inspections")}
            desc={t("Daily and weekly job-site safety inspections. PPE, MOT, fall protection, electrical, and more — graded automatically.")}
            accent="red"
            ctaLabel={t("START FORM")}
            testId="safety-tile-inspections"
          />
          <SafetyTile
            to="/meetings/submit"
            icon={Users}
            title={t("Safety Meetings")}
            desc={t("Toolbox talks and daily huddles. 80+ heavy-civil topics with prefilled hazards — every crew member signs in.")}
            accent="slate"
            ctaLabel={t("START FORM")}
            testId="safety-tile-meetings"
          />
          <SafetyTile
            to="/incidents/submit"
            icon={AlertOctagon}
            title={t("Incident Reports")}
            desc={t("Document near misses, injuries, and damage. Severity tiers, root cause, witnesses, and follow-up — all in one record.")}
            accent="redDeep"
            ctaLabel={t("START FORM")}
            testId="safety-tile-incidents"
          />
          <SafetyTile
            to="/jha"
            icon={FileText}
            title={t("Job Hazard Plans")}
            desc={t("Read your job's Hazard Plan PDF before crew breaks ground. One plan per active MASCI job — uploaded by the office.")}
            accent="amber"
            ctaLabel={t("OPEN PLANS")}
            testId="safety-tile-jha"
          />
          <SafetyTile
            to="/trench-boxes"
            icon={Box}
            title={t("Trench Box Tabulated Data")}
            desc={t("Learn what tabulated data is, why it keeps you alive, and pull the exact manufacturer data sheet for every shield in the MASCI fleet — bilingual.")}
            accent="slate"
            ctaLabel={t("OPEN LIBRARY")}
            testId="safety-tile-trench"
          />
          <SafetyTile
            to="/safety/cards"
            icon={IdCard}
            title={t("Field Safety Cards")}
            desc={t("Bilingual wallet-sized safety cards — English and Español, front and back. Print on letter paper or email the PDF straight to the crew.")}
            accent="redDeep"
            ctaLabel={t("OPEN CARDS")}
            testId="safety-tile-cards"
          />
          <SafetyTile
            to="/safety/forms"
            icon={ShieldCheck}
            title={t("Safety Forms")}
            desc={t("Equipment Issuance & Accountability + Use & Care Training documentation — password-gated for the Safety Department.")}
            accent="redDeep"
            ctaLabel={t("OPEN FORMS")}
            testId="safety-tile-forms"
          />
        </div>
      </main>

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-8 text-center font-mono text-xs uppercase tracking-[0.22em] text-slate-500 border-t-2 border-slate-200">
        {t("MASCI · Safety")}
      </footer>
    </div>
  );
}
