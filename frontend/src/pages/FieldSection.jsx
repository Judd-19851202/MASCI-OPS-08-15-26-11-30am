// iter319 · Field Hub Calm Pass (Platform UX Governance Phase A).
//
// Apply the iter317-C / iter318 / iter319-FL calm pattern: left-edge
// stripe tiles, H1 toned down to interior-hub size, three lightweight
// operational groups (Daily Ops · Weekly Checks · Tools). NO sidebar,
// NO IA redesign, NO route changes. All 6 tile testids preserved.

import React from "react";
import { Link } from "react-router-dom";
import {
  ClipboardList, Wrench, ArrowLeft, HardHat, Calculator, Truck, Send,
} from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";

const STRIPE = {
  red:     "border-l-red-600",
  amber:   "border-l-amber-500",
  emerald: "border-l-emerald-600",
  slate:   "border-l-slate-500",
};
const BTN = {
  red:     "bg-red-700 hover:bg-red-800",
  amber:   "bg-amber-700 hover:bg-amber-800",
  emerald: "bg-emerald-700 hover:bg-emerald-800",
  slate:   "bg-slate-700 hover:bg-slate-800",
};

function FieldTile({ to, icon: Icon, title, desc, accent = "amber", ctaLabel, testId }) {
  const stripe = STRIPE[accent] || STRIPE.amber;
  const btn = BTN[accent] || BTN.amber;
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

function SectionHeading({ title, sub, testId }) {
  return (
    <div className="mb-4 flex items-baseline gap-3 flex-wrap">
      <h2
        className="font-mono text-xs uppercase tracking-[0.22em] text-slate-700"
        data-testid={testId}
      >
        {title}
      </h2>
      <span className="hidden sm:inline-block h-px flex-1 bg-slate-200" aria-hidden="true" />
      <span className="text-xs text-slate-500 italic">{sub}</span>
    </div>
  );
}

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

      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-8">
        <div className="mb-6">
          <Link
            to="/"
            className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.2em] text-slate-600 hover:text-amber-700 font-bold"
            data-testid="field-back-link"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> {t("Home")}
          </Link>
        </div>

        <div className="mb-8 flex items-start gap-4">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-amber-600 text-white shrink-0">
            <HardHat className="w-6 h-6" />
          </div>
          <div className="flex-1">
            <span className="font-mono text-xs uppercase tracking-[0.2em] text-amber-700 font-bold">
              {t("Field · Daily Ops")}
            </span>
            <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-1">
              {t("Field")}
            </h1>
            <p className="text-slate-600 text-base mt-2 max-w-2xl">
              {t("What the crew fills out every day, before and after the shift.")}
            </p>
          </div>
        </div>

        <div className="space-y-10 mb-12">
          {/* Group 01 · Field Reporting — operational memory continuity */}
          <section data-testid="field-group-reporting">
            <SectionHeading
              title={t("Field Reporting")}
              sub={t("End-of-day operational memory")}
              testId="field-group-heading-reporting"
            />
            {/* Slightly emphasized: single tile in a max-width container
                so it visually "leads" without becoming a banner. */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <FieldTile
                to="/daily/submit"
                icon={ClipboardList}
                title={t("Daily Reports")}
                desc={t("End-of-day site log: crews, subs, visitors, equipment, materials, weather, photos. Replaces Fieldwire.")}
                accent="red"
                ctaLabel={t("START FORM")}
                testId="field-tile-daily"
              />
            </div>
          </section>

          {/* Group 02 · Equipment Operations */}
          <section data-testid="field-group-equipment">
            <SectionHeading
              title={t("Equipment Operations")}
              sub={t("Daily OSHA equipment readiness")}
              testId="field-group-heading-equipment"
            />
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <FieldTile
                to="/equipment/submit"
                icon={Wrench}
                title={t("Equipment Pre-Op")}
                desc={t("Daily OSHA walk-around inspections for Heavy Equipment. PASS / FAIL each item — fail tags the unit out of service.")}
                accent="slate"
                ctaLabel={t("START FORM")}
                testId="field-tile-equipment"
              />
            </div>
          </section>

          {/* Group 03 · Trucking Operations — the driver's operational lane */}
          <section data-testid="field-group-trucking">
            <SectionHeading
              title={t("Trucking Operations")}
              sub={t("Shift activation · daily readiness · recurring continuity")}
              testId="field-group-heading-trucking"
            />
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <FieldTile
                to="/shift"
                icon={Send}
                title={t("Driver Shift Start")}
                desc={t("Truck drivers check in here at the start of every shift. Pick your name and truck — no password, no app.")}
                accent="amber"
                ctaLabel={t("START SHIFT")}
                testId="field-tile-shift-start"
              />
              <FieldTile
                to="/fleet/dvir/new"
                icon={Truck}
                title={t("Trucking · Daily DVIR")}
                desc={t("Daily Vehicle Inspection for trucks and trailers. Walk-around · PASS / FAIL each item · Shop sees defects automatically.")}
                accent="amber"
                ctaLabel={t("START DVIR")}
                testId="field-tile-dvir"
              />
              <FieldTile
                to="/fleet/weekly-lead/new"
                icon={Truck}
                title={t("Weekly · Lead Inspection")}
                desc={t("Quick weekly check by the lead — operational hygiene, recurring issues, key safety items. Reuses the DVIR flow.")}
                accent="amber"
                ctaLabel={t("START LEAD INSPECTION")}
                testId="field-tile-weekly-lead"
              />
              <FieldTile
                to="/fleet/weekly-emergency/new"
                icon={Truck}
                title={t("Weekly · Emergency Equipment")}
                desc={t("Fire extinguishers, triangles, first aid, PPE, alarms. Present · charged · within date.")}
                accent="amber"
                ctaLabel={t("START EMERGENCY CHECK")}
                testId="field-tile-weekly-emergency"
              />
            </div>
          </section>

          {/* Group 04 · Calculators & Tools — supporting utilities */}
          <section
            data-testid="field-group-tools"
            className="pt-6 border-t border-slate-200"
          >
            <SectionHeading
              title={t("Calculators & Tools")}
              sub={t("Supporting field calculators")}
              testId="field-group-heading-tools"
            />
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <FieldTile
                to="/field/calculators"
                icon={Calculator}
                title={t("Material Calculators")}
                desc={t("Quickly estimate aggregate, asphalt, concrete, truck loads, yield, waste, and tons-to-cubic-yard conversions from the field.")}
                accent="slate"
                ctaLabel={t("OPEN TOOLS")}
                testId="field-tile-calculators"
              />
            </div>
          </section>
        </div>
      </main>

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-8 text-center font-mono text-xs uppercase tracking-[0.2em] text-slate-500 border-t-2 border-slate-200">
        {t("MASCI · Field")}
      </footer>
    </div>
  );
}
