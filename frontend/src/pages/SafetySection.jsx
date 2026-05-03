import React from "react";
import { Link } from "react-router-dom";
import {
  ClipboardCheck, Users, AlertOctagon, FileText, Box, Plus, ArrowLeft, ArrowRight, BookOpen, Shield, IdCard,
} from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";

// `kind="form"` → "+ Start Form" (red accent) — opens a fillable form.
// `kind="library"` → "Open Library" (slate) — opens a document/reference
// page. Three Safety tiles point at libraries (JHP plans, Trench-box
// tabulated data, Field Safety Cards) — they don't kick off a form, so
// the old "+ Start Form" CTA was misleading.
const FormTile = ({ to, icon: Icon, title, desc, accent = "red", kind = "form", ctaLabel, testId }) => {
  const accentCls =
    accent === "red"     ? "border-red-700 bg-red-700"
    : accent === "amber" ? "border-amber-600 bg-amber-600"
    : accent === "redDeep" ? "border-red-900 bg-red-900"
    : "border-slate-800 bg-slate-800";
  const isLibrary = kind === "library";
  const CtaIcon = isLibrary ? BookOpen : Plus;
  const ctaCls = isLibrary
    ? "text-slate-700 group-hover:text-red-700"
    : "text-red-700";
  return (
    <Link
      to={to}
      className="group relative bg-white border-2 border-slate-300 rounded-md p-6 sm:p-8 hover:border-red-700 hover:-translate-y-0.5 transition-all duration-150 flex flex-col"
      data-testid={testId}
    >
      <div className={`inline-flex items-center justify-center w-14 h-14 rounded-md ${accentCls} text-white mb-4`}>
        <Icon className="w-7 h-7" />
      </div>
      <h3 className="font-display text-2xl font-black tracking-tight text-slate-900">{title}</h3>
      <p className="text-slate-600 text-sm mt-2 flex-1 leading-relaxed">{desc}</p>
      <div className="mt-5 pt-4 border-t-2 border-slate-100 flex items-center justify-end">
        <div className={`inline-flex items-center gap-2 font-mono text-xs uppercase tracking-[0.2em] font-bold group-hover:gap-3 transition-all ${ctaCls}`}>
          <CtaIcon className="w-4 h-4" /> {ctaLabel}
          {isLibrary && <ArrowRight className="w-3.5 h-3.5" />}
        </div>
      </div>
    </Link>
  );
};

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
          <FormTile
            to="/inspections/submit"
            icon={ClipboardCheck}
            title={t("Site Inspections")}
            desc={t("Daily and weekly job-site safety inspections. PPE, MOT, fall protection, electrical, and more — graded automatically.")}
            accent="red"
            kind="form"
            ctaLabel={t("Start Form")}
            testId="safety-tile-inspections"
          />
          <FormTile
            to="/meetings/submit"
            icon={Users}
            title={t("Safety Meetings")}
            desc={t("Toolbox talks and daily huddles. 80+ heavy-civil topics with prefilled hazards — every crew member signs in.")}
            accent="slate"
            kind="form"
            ctaLabel={t("Start Form")}
            testId="safety-tile-meetings"
          />
          <FormTile
            to="/incidents/submit"
            icon={AlertOctagon}
            title={t("Incident Reports")}
            desc={t("Document near misses, injuries, and damage. Severity tiers, root cause, witnesses, and follow-up — all in one record.")}
            accent="redDeep"
            kind="form"
            ctaLabel={t("Start Form")}
            testId="safety-tile-incidents"
          />
          <FormTile
            to="/jha"
            icon={FileText}
            title={t("Job Hazard Plans")}
            desc={t("Read your job's Hazard Plan PDF before crew breaks ground. One plan per active MASCI job — uploaded by the office.")}
            accent="amber"
            kind="library"
            ctaLabel={t("Open Plans")}
            testId="safety-tile-jha"
          />
          <FormTile
            to="/trench-boxes"
            icon={Box}
            title={t("Trench Box Tabulated Data")}
            desc={t("Learn what tabulated data is, why it keeps you alive, and pull the exact manufacturer data sheet for every shield in the MASCI fleet — bilingual.")}
            accent="slate"
            kind="library"
            ctaLabel={t("Open Library")}
            testId="safety-tile-trench"
          />
          <FormTile
            to="/safety/cards"
            icon={IdCard}
            title={t("Field Safety Cards")}
            desc={t("Bilingual wallet-sized safety cards — English and Español, front and back. Print on letter paper or email the PDF straight to the crew.")}
            accent="redDeep"
            kind="library"
            ctaLabel={t("Open Cards")}
            testId="safety-tile-cards"
          />
        </div>
      </main>

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-8 text-center font-mono text-xs uppercase tracking-[0.2em] text-slate-500 border-t-2 border-slate-200">
        {t("MASCI · Safety")}
      </footer>
    </div>
  );
}
