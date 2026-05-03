import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, ClipboardCheck, Layers, Hammer, HardHat } from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { QAQC_KINDS } from "@/lib/qaqcSchema";

const ICONS = {
  "concrete-form": Layers,
  rebar: Hammer,
  "subcontractor-work": HardHat,
};

const ACCENT_CLS = {
  blue: "border-blue-300 bg-blue-50 text-blue-900",
  amber: "border-amber-400 bg-amber-50 text-amber-900",
  slate: "border-slate-300 bg-slate-50 text-slate-900",
};

const ACCENT_ICON = {
  blue: "bg-blue-600 text-white",
  amber: "bg-amber-600 text-white",
  slate: "bg-slate-700 text-white",
};

/**
 * QA/QC section landing page — same card grid pattern as FieldSection /
 * SafetySection. Three cards open the three inspection forms.
 */
export default function QaqcSection() {
  const { t, lang } = useT();

  return (
    <div className="min-h-screen blueprint-bg">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-emerald-600">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <MasciLogo variant="lockup" size="xl" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
          <LangToggle />
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-5 sm:px-8 py-8 sm:py-10">
        <div className="mb-6">
          <Link
            to="/"
            className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.2em] text-slate-600 hover:text-emerald-700 font-bold"
            data-testid="qaqc-back-home"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> {t("Home")}
          </Link>
        </div>

        <div className="mb-10 flex items-start gap-4">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-md bg-emerald-600 text-white shrink-0">
            <ClipboardCheck className="w-7 h-7" />
          </div>
          <div className="flex-1 min-w-0">
            <span className="font-mono text-xs uppercase tracking-[0.25em] text-emerald-700 font-bold">
              {t("Quality Assurance · Quality Control")}
            </span>
            <h1 className="font-display text-3xl sm:text-5xl font-black tracking-tight text-slate-900 mt-1">
              {t("QA / QC Inspections")}
            </h1>
            <p className="text-slate-600 text-sm sm:text-base mt-2 max-w-2xl">
              {t(
                "Quality assurance and quality control inspections for concrete, rebar, and subcontractor work — documented, signed, photographed, routed, and stored.",
              )}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-5 mb-12">
          {QAQC_KINDS.map((kind) => {
            const Icon = ICONS[kind.slug] || ClipboardCheck;
            return (
              <Link
                key={kind.slug}
                to={`/qaqc/${kind.slug}/new`}
                className={
                  "group block border-2 rounded-md p-5 sm:p-6 hover:shadow-lg transition-shadow " +
                  ACCENT_CLS[kind.accent]
                }
                data-testid={`qaqc-tile-${kind.slug}`}
              >
                <div className="flex items-start gap-4">
                  <div
                    className={
                      "inline-flex items-center justify-center w-12 h-12 rounded-md shrink-0 " +
                      ACCENT_ICON[kind.accent]
                    }
                  >
                    <Icon className="w-6 h-6" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-mono text-[10px] uppercase tracking-[0.25em] font-bold opacity-70">
                      {t("Open Form")}
                    </div>
                    <h2 className="font-display text-xl sm:text-2xl font-black tracking-tight mt-0.5">
                      {lang === "es" ? kind.title_es : kind.title}
                    </h2>
                    <p className="text-sm mt-2 leading-snug">
                      {lang === "es" ? kind.blurb_es : kind.blurb}
                    </p>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      </main>

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-8 text-center font-mono text-xs uppercase tracking-[0.2em] text-slate-500 border-t-2 border-slate-200">
        {t("MASCI · QA/QC")}
      </footer>
    </div>
  );
}
