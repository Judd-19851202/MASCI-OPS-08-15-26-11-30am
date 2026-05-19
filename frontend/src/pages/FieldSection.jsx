import React from "react";
import { Link } from "react-router-dom";
import {
  ClipboardList, Wrench, ArrowLeft, HardHat, Calculator, Truck,
} from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { LangToggle } from "@/components/LangToggle";
import { SectionTile } from "@/components/SectionTile";
import { useT } from "@/lib/i18n";

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
          <MasciLogo variant="mark" size="lg" className="hidden sm:block" homeLink="/" />
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
            <ArrowLeft className="w-3.5 h-3.5" /> {t("Home")}
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

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5 mb-12">
          <SectionTile
            to="/daily/submit"
            icon={ClipboardList}
            title={t("Daily Reports")}
            desc={t("End-of-day site log: crews, subs, visitors, equipment, materials, weather, photos. Replaces Fieldwire.")}
            accent="red"
            ctaLabel={t("Start Form")}
            testId="field-tile-daily"
          />
          <SectionTile
            to="/equipment/submit"
            icon={Wrench}
            title={t("Equipment Pre-Op")}
            desc={t("Daily OSHA walk-around inspections for Heavy Equipment. PASS / FAIL each item — fail tags the unit out of service.")}
            accent="slate"
            ctaLabel={t("Start Form")}
            testId="field-tile-equipment"
          />
          <SectionTile
            to="/field/calculators"
            icon={Calculator}
            title={t("Material Calculators")}
            desc={t("Quickly estimate aggregate, asphalt, concrete, truck loads, yield, waste, and tons-to-cubic-yard conversions from the field.")}
            accent="amber"
            ctaLabel={t("Open Tools")}
            testId="field-tile-calculators"
          />
          <SectionTile
            to="/fleet/dvir/new"
            icon={Truck}
            title={t("Trucking · Daily DVIR")}
            desc={t("Daily Vehicle Inspection for trucks and trailers. Walk-around · PASS / FAIL each item · Shop sees defects automatically.")}
            accent="amber"
            ctaLabel={t("Start DVIR")}
            testId="field-tile-dvir"
          />
        </div>
      </main>

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-8 text-center font-mono text-xs uppercase tracking-[0.2em] text-slate-500 border-t-2 border-slate-200">
        {t("MASCI · Field")}
      </footer>
    </div>
  );
}
