import React from "react";
import { Link } from "react-router-dom";
import {
  ClipboardList, Wrench, Plus, ArrowLeft, HardHat, Calculator,
} from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";

const FormTile = ({ to, icon: Icon, title, desc, accent = "red", testId }) => {
  const accentCls =
    accent === "red"     ? "border-red-700 bg-red-700"
    : accent === "amber" ? "border-amber-600 bg-amber-600"
    : "border-slate-800 bg-slate-800";
  return (
    <Link
      to={to}
      className="group relative bg-white border-2 border-slate-300 rounded-md p-6 sm:p-8 hover:border-amber-600 hover:-translate-y-0.5 transition-all duration-150 flex flex-col"
      data-testid={testId}
    >
      <div className={`inline-flex items-center justify-center w-14 h-14 rounded-md ${accentCls} text-white mb-4`}>
        <Icon className="w-7 h-7" />
      </div>
      <h3 className="font-display text-2xl font-black tracking-tight text-slate-900">{title}</h3>
      <p className="text-slate-600 text-sm mt-2 flex-1 leading-relaxed">{desc}</p>
      <div className="mt-5 pt-4 border-t-2 border-slate-100 flex items-center justify-end">
        <div className="inline-flex items-center gap-2 font-mono text-xs uppercase tracking-[0.2em] text-amber-700 font-bold group-hover:gap-3 transition-all">
          <Plus className="w-4 h-4" /> Start Form
        </div>
      </div>
    </Link>
  );
};

/**
 * FieldSection — landing for the /field sub-hub. Daily operational logs
 * used by crews and operators at the start/end of every shift.
 */
export default function FieldSection() {
  const { t } = useT();

  return (
    <div className="min-h-screen blueprint-bg">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-amber-600">
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
            className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.2em] text-slate-600 hover:text-amber-600 font-bold"
            data-testid="field-back-link"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> MASCI Hub
          </Link>
        </div>

        <div className="mb-10 sm:mb-14 flex items-start gap-4">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-md bg-amber-600 text-white shrink-0">
            <HardHat className="w-7 h-7" />
          </div>
          <div className="flex-1">
            <span className="font-mono text-xs uppercase tracking-[0.25em] text-amber-700 font-bold">
              {t("Field · Daily Ops")}
            </span>
            <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tight text-slate-900 mt-1">
              {t("Field")}
            </h1>
            <p className="text-slate-600 text-base sm:text-lg mt-2 max-w-2xl">
              {t("What the crew fills out every day, before and after the shift.")}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-5 mb-12">
          <FormTile
            to="/daily/submit"
            icon={ClipboardList}
            title={t("Daily Reports")}
            desc={t("End-of-day site log: crews, subs, visitors, equipment, materials, weather, photos. Replaces Fieldwire.")}
            accent="red"
            testId="field-tile-daily"
          />
          <FormTile
            to="/equipment/submit"
            icon={Wrench}
            title={t("Equipment Pre-Op")}
            desc={t("Daily OSHA walk-around inspections for Heavy Equipment. PASS / FAIL each item — fail tags the unit out of service.")}
            accent="slate"
            testId="field-tile-equipment"
          />
          <FormTile
            to="/field/calculators"
            icon={Calculator}
            title={t("Material Calculators")}
            desc={t("Quickly estimate aggregate, asphalt, concrete, truck loads, yield, waste, and tons-to-cubic-yard conversions from the field.")}
            accent="amber"
            testId="field-tile-calculators"
          />
        </div>
      </main>

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-8 text-center font-mono text-xs uppercase tracking-[0.2em] text-slate-500 border-t-2 border-slate-200">
        {t("MASCI · Field")}
      </footer>
    </div>
  );
}
