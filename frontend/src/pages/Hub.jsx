import React from "react";
import { Link } from "react-router-dom";
import {
  ClipboardCheck,
  Users,
  AlertTriangle,
  AlertOctagon,
  ClipboardList,
  Wrench,
  Plus,
} from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";

/**
 * Field-crew Hub.
 *
 * Crews never see how many forms have been submitted, who submitted them, or
 * any prior records. They only see five big tiles to *file* a new form. The
 * office (Admin) side lives at /admin and is gated by a password.
 */

const FormTile = ({ to, icon: Icon, title, desc, accent = "red", testId }) => {
  const accentCls =
    accent === "red"
      ? "border-red-700 bg-red-700"
      : accent === "amber"
      ? "border-amber-600 bg-amber-600"
      : accent === "redDeep"
      ? "border-red-900 bg-red-900"
      : "border-slate-800 bg-slate-800";
  return (
    <Link
      to={to}
      className="group relative bg-white border-2 border-slate-300 rounded-md p-6 sm:p-8 hover:border-red-700 hover:-translate-y-0.5 transition-all duration-150 flex flex-col"
      data-testid={testId}
    >
      <div
        className={`inline-flex items-center justify-center w-14 h-14 rounded-md ${accentCls} text-white mb-4`}
      >
        <Icon className="w-7 h-7" />
      </div>
      <h3 className="font-display text-2xl font-black tracking-tight text-slate-900">
        {title}
      </h3>
      <p className="text-slate-600 text-sm mt-2 flex-1 leading-relaxed">{desc}</p>
      <div className="mt-5 pt-4 border-t-2 border-slate-100 flex items-center justify-end">
        <div className="inline-flex items-center gap-2 font-mono text-xs uppercase tracking-[0.2em] text-red-700 font-bold group-hover:gap-3 transition-all">
          <Plus className="w-4 h-4" /> Start Form
        </div>
      </div>
    </Link>
  );
};

export default function Hub() {
  const { t } = useT();

  return (
    <div className="min-h-screen blueprint-bg">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <MasciLogo variant="lockup" size="2xl" className="hidden sm:block" />
          <MasciLogo variant="mark" size="lg" className="sm:hidden" />
          <div className="flex items-center gap-2">
            <LangToggle />
            <CompanyInfoDialog />
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-8 sm:py-12">
        <div className="mb-10 sm:mb-14">
          <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-700">
            {t("MASCI Safety Hub")}
          </span>
          <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-slate-900 mt-2">
            {t("One front door for every safety form.")}
          </h1>
          <p className="text-slate-600 text-base sm:text-lg mt-3 max-w-2xl">
            {t("Every field-safety form. One digital home.")}
          </p>
          <div className="mt-4 flex items-center gap-3 font-mono text-[11px] uppercase tracking-[0.25em]">
            <span className="text-red-700 font-bold">{t("No Shortcuts")}</span>
            <span className="w-1 h-1 rounded-full bg-red-700" />
            <span className="text-red-700 font-bold">{t("No Exceptions")}</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5 mb-12">
          <FormTile
            to="/daily/new"
            icon={ClipboardList}
            title={t("Daily Reports")}
            desc={t("End-of-day site log: crews, subs, visitors, equipment, materials, weather, photos. Replaces Fieldwire.")}
            accent="red"
            testId="hub-tile-daily"
          />
          <FormTile
            to="/inspect/new"
            icon={ClipboardCheck}
            title={t("Site Inspections")}
            desc={t("Daily and weekly job-site safety inspections. PPE, MOT, fall protection, electrical, and more — graded automatically.")}
            accent="red"
            testId="hub-tile-inspections"
          />
          <FormTile
            to="/meetings/new"
            icon={Users}
            title={t("Safety Meetings")}
            desc={t("Toolbox talks and daily huddles. 80+ heavy-civil topics with prefilled hazards — every crew member signs in.")}
            accent="slate"
            testId="hub-tile-meetings"
          />
          <FormTile
            to="/jha/new"
            icon={AlertTriangle}
            title={t("Job Hazard Analysis")}
            desc={t("Pre-task JHA / JSA. Walk every step, list hazards, document controls, and get the crew sign-off before work starts.")}
            accent="amber"
            testId="hub-tile-jha"
          />
          <FormTile
            to="/incidents/new"
            icon={AlertOctagon}
            title={t("Incident Reports")}
            desc={t("Document near misses, injuries, and damage. Severity tiers, root cause, witnesses, and follow-up — all in one record.")}
            accent="redDeep"
            testId="hub-tile-incidents"
          />
          <FormTile
            to="/equipment/new"
            icon={Wrench}
            title={t("Equipment Pre-Op")}
            desc={t("Daily OSHA walk-around inspections for Heavy Equipment. PASS / FAIL each item — fail tags the unit out of service.")}
            accent="slate"
            testId="hub-tile-equipment"
          />
        </div>
      </main>

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-8 flex flex-col sm:flex-row items-center justify-between gap-4 border-t-2 border-slate-200">
        <span className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500">
          {t("MASCI · Field Safety Reporting Portal")}
        </span>
        <div className="flex items-center gap-3">
          <Link
            to="/cheatsheet"
            className="inline-flex items-center gap-2 h-10 px-3 rounded-md border-2 border-slate-300 text-slate-700 hover:border-red-700 hover:text-red-700 font-mono text-xs uppercase tracking-[0.2em] font-bold transition-colors"
            data-testid="hub-cheatsheet-link"
          >
            {t("Cheat Sheet")}
          </Link>
          <Link
            to="/admin/login"
            className="group inline-flex items-center gap-2 h-10 pl-3 pr-4 rounded-md bg-slate-900 hover:bg-red-700 text-white border-b-2 border-red-700 hover:border-red-900 transition-colors duration-150"
            data-testid="hub-admin-link"
          >
            <span className="inline-flex items-center justify-center w-6 h-6 rounded bg-red-700 group-hover:bg-slate-900 transition-colors">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="w-3.5 h-3.5 text-white"
                aria-hidden="true"
              >
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                <path d="M7 11V7a5 5 0 0 1 10 0v4" />
              </svg>
            </span>
            <span className="font-mono text-xs uppercase tracking-[0.2em] font-bold">
              Admin Sign In
            </span>
          </Link>
        </div>
      </footer>
    </div>
  );
}
