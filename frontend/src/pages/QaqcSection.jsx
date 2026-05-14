import React from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft, ClipboardCheck, Layers, Hammer, HardHat,
} from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { LangToggle } from "@/components/LangToggle";
import { SectionTile } from "@/components/SectionTile";
import { useT } from "@/lib/i18n";
import { QAQC_KINDS } from "@/lib/qaqcSchema";

const ICONS = {
  "concrete-form": Layers,
  rebar: Hammer,
  "subcontractor-work": HardHat,
};

/**
 * QA/QC section landing page — matches FieldSection / SafetySection chrome
 * exactly (slate-900 header, eyebrow + 4xl/5xl headline, white-card FormTile
 * grid). Three cards open the three inspection forms.
 */
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

      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-8 sm:py-12">
        <div className="mb-6">
          <Link
            to="/"
            className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.2em] text-slate-600 hover:text-emerald-700 font-bold"
            data-testid="qaqc-back-home"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> {t("Home")}
          </Link>
        </div>

        <div className="mb-10 sm:mb-14 flex items-start gap-4">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-md bg-emerald-600 text-white shrink-0">
            <ClipboardCheck className="w-7 h-7" />
          </div>
          <div className="flex-1">
            <span className="font-mono text-xs uppercase tracking-[0.25em] text-emerald-700 font-bold">
              {t("Quality Assurance · Quality Control")}
            </span>
            <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tight text-slate-900 mt-1">
              {t("QA / QC")}
            </h1>
            <p className="text-slate-600 text-base sm:text-lg mt-2 max-w-2xl">
              {t(
                "Quality assurance and quality control inspections for concrete, rebar, and subcontractor work — documented, signed, photographed, routed, and stored.",
              )}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5 mb-12">
          {QAQC_KINDS.map((kind) => {
            const Icon = ICONS[kind.slug] || ClipboardCheck;
            return (
              <SectionTile
                key={kind.slug}
                to={`/qaqc/${kind.slug}/new`}
                icon={Icon}
                title={lang === "es" ? kind.title_es : kind.title}
                desc={lang === "es" ? kind.blurb_es : kind.blurb}
                accent={kind.accent}
                ctaLabel={t("Start Form")}
                testId={`qaqc-tile-${kind.slug}`}
              />
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
