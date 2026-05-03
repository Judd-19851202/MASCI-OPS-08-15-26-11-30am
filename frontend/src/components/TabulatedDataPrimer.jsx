import React from "react";
import { BookOpen, AlertTriangle } from "lucide-react";
import { TABULATED_DATA_PRIMER } from "@/lib/tabulatedDataPrimer";
import { useT } from "@/lib/i18n";

/**
 * TabulatedDataPrimer — bilingual explainer shown on the crew-facing
 * /trench-boxes page AND the /admin/trench-boxes workspace.
 *
 * Language is driven entirely by the global EN/ES toggle in the page
 * header (via useT()). There is intentionally no second toggle inside
 * this card — every page on MASCI Hub translates from the single
 * top-of-page switch. Content is adapted from the United Rentals
 * training PDF + translated for MASCI.
 */
export default function TabulatedDataPrimer() {
  const { lang } = useT();
  const t = (k) => TABULATED_DATA_PRIMER[k][lang];

  return (
    <section
      className="border-2 border-amber-400 rounded-md bg-amber-50 p-5 sm:p-7 mb-6"
      data-testid="tabulated-data-primer"
    >
      <header className="flex items-start gap-3 mb-4">
        <div className="inline-flex items-center justify-center w-11 h-11 rounded-md bg-amber-500 text-white shrink-0">
          <BookOpen className="w-5 h-5" />
        </div>
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-amber-800 font-bold">
            {lang === "en" ? "Read Before You Enter The Box" : "Leer Antes de Entrar al Escudo"}
          </div>
          <h2 className="font-display text-xl sm:text-2xl font-black text-slate-900 leading-none mt-1">
            {t("intro").title}
          </h2>
          <p className="text-sm text-slate-700 mt-1">{t("intro").subtitle}</p>
        </div>
      </header>

      <div className="bg-white border-2 border-amber-300 rounded p-4 mb-5 flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
        <p className="text-sm text-slate-900 font-medium leading-relaxed">
          {t("intro").hook}
        </p>
      </div>

      <div className="space-y-4">
        {TABULATED_DATA_PRIMER.sections.map((sec) => {
          const body = sec[lang];
          return (
            <div
              key={sec.id}
              className="bg-white border border-slate-200 rounded p-4"
              data-testid={`primer-section-${sec.id}`}
            >
              <h3 className="font-display font-black text-slate-900 text-base mb-2">
                {body.heading}
              </h3>
              <ul className="space-y-1.5">
                {body.body.map((line, i) => (
                  <li
                    key={i}
                    className="text-sm text-slate-700 leading-relaxed pl-4 relative before:content-['•'] before:absolute before:left-0 before:text-amber-600 before:font-black"
                  >
                    {line}
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>

      <footer className="mt-5 p-4 bg-slate-900 text-white rounded">
        <p className="text-sm leading-relaxed font-medium">
          {TABULATED_DATA_PRIMER.footer[lang].cta}
        </p>
      </footer>
    </section>
  );
}
