// iter320 · QA/QC Section Calm Pass (Platform UX Governance Phase A).
//
// Applies the iter317-C / iter318 / iter319 platform-family calm pattern:
// left-edge stripe tiles · interior-hub H1 size · matched section heading
// style. Three forms, no grouping needed (Rule 4: <6 tiles may skip
// grouping). NO sidebar · NO IA redesign · NO route changes. All 3
// `qaqc-tile-*` testids preserved.

import React from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft, ClipboardCheck, Layers, Hammer, HardHat,
} from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { QAQC_KINDS } from "@/lib/qaqcSchema";

const ICONS = {
  "concrete-form": Layers,
  rebar: Hammer,
  "subcontractor-work": HardHat,
};

const STRIPE = {
  red:     "border-l-red-600",
  amber:   "border-l-amber-500",
  emerald: "border-l-emerald-600",
  blue:    "border-l-blue-600",
  indigo:  "border-l-indigo-600",
  cyan:    "border-l-cyan-600",
  slate:   "border-l-slate-500",
};
const BTN = {
  red:     "bg-red-700 hover:bg-red-800",
  amber:   "bg-amber-700 hover:bg-amber-800",
  emerald: "bg-emerald-700 hover:bg-emerald-800",
  blue:    "bg-blue-700 hover:bg-blue-800",
  indigo:  "bg-indigo-700 hover:bg-indigo-800",
  cyan:    "bg-cyan-700 hover:bg-cyan-800",
  slate:   "bg-slate-700 hover:bg-slate-800",
};

function QaqcTile({ to, icon: Icon, title, desc, accent = "emerald", ctaLabel = "START FORM", testId }) {
  const stripe = STRIPE[accent] || STRIPE.emerald;
  const btn = BTN[accent] || BTN.emerald;
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

export default function QaqcSection() {
  const { t, lang } = useT();

  return (
    <div className="min-h-screen blueprint-bg">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-emerald-600">
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
            className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.22em] text-slate-600 hover:text-emerald-700 font-bold"
            data-testid="qaqc-back-home"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> {t("Home")}
          </Link>
        </div>

        <div className="mb-8 flex items-start gap-4">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-emerald-600 text-white shrink-0">
            <ClipboardCheck className="w-6 h-6" />
          </div>
          <div className="flex-1">
            <span className="font-mono text-xs uppercase tracking-[0.22em] text-emerald-700 font-bold">
              {t("Quality Assurance · Quality Control")}
            </span>
            <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-1">
              {t("QA / QC")}
            </h1>
            <p className="text-slate-600 text-base mt-2 max-w-2xl">
              {t(
                "Quality assurance and quality control inspections for concrete, rebar, and subcontractor work — documented, signed, photographed, routed, and stored.",
              )}
            </p>
          </div>
        </div>

        {/* iter320 · matched section heading style (mono kicker · thin
            divider · italic subtitle) for family parity even on this
            single-group section. */}
        <div className="mb-4 flex items-baseline gap-3 flex-wrap" data-testid="qaqc-section-heading">
          <h2 className="font-mono text-xs uppercase tracking-[0.22em] text-slate-700">
            {t("Inspection Forms")}
          </h2>
          <span className="hidden sm:inline-block h-px flex-1 bg-slate-200" aria-hidden="true" />
          <span className="text-xs text-slate-500 italic">
            {t("Routed, signed, photographed, and stored")}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-12">
          {QAQC_KINDS.map((kind) => {
            const Icon = ICONS[kind.slug] || ClipboardCheck;
            return (
              <QaqcTile
                key={kind.slug}
                to={`/qaqc/${kind.slug}/new`}
                icon={Icon}
                title={lang === "es" ? kind.title_es : kind.title}
                desc={lang === "es" ? kind.blurb_es : kind.blurb}
                accent={kind.accent}
                ctaLabel={t("START FORM")}
                testId={`qaqc-tile-${kind.slug}`}
              />
            );
          })}
        </div>
      </main>

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-8 text-center font-mono text-xs uppercase tracking-[0.22em] text-slate-500 border-t-2 border-slate-200">
        {t("MASCI · QA/QC")}
      </footer>
    </div>
  );
}
