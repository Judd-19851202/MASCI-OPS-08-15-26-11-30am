import React from "react";
import { Link } from "react-router-dom";
import { FileDown, QrCode, Lock, Printer } from "lucide-react";
import { useT } from "@/lib/i18n";
import { TRACKS } from "@/data/training";

/**
 * AdminTrainingResourcesPanel
 *
 * Internal-only mirror of the Shop / PM / Admin training packets and
 * Scan-&-Go QR posters. Lives on the Admin Console because back-office
 * workflows aren't shared outside the company — the public Training Hub
 * page only carries the Field Crew variants.
 *
 * Admin is already authenticated (this panel only renders inside
 * AdminHub) so the packet links hit the auth-aware viewer route which
 * attaches the admin token; the QR poster links open the print-ready
 * page that already gates by audience.
 */
const INTERNAL_TRACKS = Object.values(TRACKS).filter(
  (tr) => tr.audience !== "public"
);

const TIER_LABEL = {
  shop: { en: "Shop", es: "Taller" },
  pm: { en: "PM", es: "Gerente" },
  admin: { en: "Admin", es: "Administrador" },
};

function tierLabel(audience, lang) {
  const m = TIER_LABEL[audience];
  if (!m) return audience;
  return lang === "es" ? m.es : m.en;
}

export default function AdminTrainingResourcesPanel() {
  const { t, lang } = useT();
  return (
    <div
      className="mt-8 rounded-md border-2 border-slate-900 bg-slate-900 text-white p-5 sm:p-6"
      data-testid="admin-training-resources-panel"
    >
      <div className="flex items-start gap-4 flex-wrap">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-amber-500 text-slate-900 shrink-0">
          <FileDown className="w-6 h-6" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-amber-400 font-bold flex items-center gap-2">
            {t("Internal Training Resources")}
          </div>
          <h3 className="font-display text-lg font-black text-white mt-1">
            {t("Shop · PM · Admin packets and QR posters")}
          </h3>
          <p className="text-slate-300 text-sm mt-1 leading-relaxed max-w-3xl">
            {t(
              "Back-office training materials live here, not on the public Training Hub. Field Crew packets remain public for insurance / auditor / new-hire sharing."
            )}
          </p>
        </div>
      </div>

      {/* PDF training packets — internal */}
      <div className="mt-5">
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-400 font-bold mb-2 flex items-center gap-2">
          <FileDown className="w-3.5 h-3.5" /> {t("PDF training packets")}
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          {INTERNAL_TRACKS.map((tr) => {
            const link = (lng) => `/training/${tr.slug}/packet?lang=${lng}`;
            return (
              <div
                key={`pkt-${tr.slug}`}
                className="bg-slate-800 rounded p-3 flex flex-col gap-2 text-xs"
                data-testid={`admin-training-pkt-tile-${tr.slug}`}
              >
                <div className="flex items-center justify-between gap-2 min-w-0">
                  <span className="font-bold truncate flex items-center gap-1.5 min-w-0">
                    <Lock className="w-3 h-3 text-amber-400 shrink-0" />
                    <span className="truncate">
                      {lang === "es" && tr.title_es ? tr.title_es : tr.title}
                    </span>
                  </span>
                  <span className="shrink-0 inline-flex items-center px-1.5 py-0.5 rounded font-mono text-[9px] tracking-[0.15em] uppercase bg-amber-700/30 text-amber-300 border border-amber-700/40">
                    {tierLabel(tr.audience, lang)}
                  </span>
                </div>
                <div className="flex gap-1 shrink-0">
                  <Link
                    to={link("en")}
                    className="inline-flex items-center gap-1 px-2 py-1 rounded bg-slate-700 hover:bg-amber-500 hover:text-slate-900 font-mono font-bold uppercase tracking-wide transition-colors"
                    data-testid={`admin-training-pkt-${tr.slug}-en`}
                  >
                    EN
                  </Link>
                  <Link
                    to={link("es")}
                    className="inline-flex items-center gap-1 px-2 py-1 rounded bg-slate-700 hover:bg-amber-500 hover:text-slate-900 font-mono font-bold uppercase tracking-wide transition-colors"
                    data-testid={`admin-training-pkt-${tr.slug}-es`}
                  >
                    ES
                  </Link>
                  <Link
                    to={link("bi")}
                    className="inline-flex items-center gap-1 px-2 py-1 rounded bg-red-700 hover:bg-red-600 font-mono font-bold uppercase tracking-wide transition-colors"
                    data-testid={`admin-training-pkt-${tr.slug}-bi`}
                    title="Bilingual · side-by-side"
                  >
                    EN+ES
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Scan-&-Go QR posters — internal */}
      <div className="mt-5">
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-400 font-bold mb-2 flex items-center gap-2">
          <QrCode className="w-3.5 h-3.5" /> {t("Scan-&-Go Posters")}
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          {INTERNAL_TRACKS.map((tr) => (
            <div
              key={`qr-${tr.slug}`}
              className="bg-slate-800 rounded p-3 flex flex-col gap-2 text-xs"
              data-testid={`admin-training-qr-tile-${tr.slug}`}
            >
              <div className="flex items-center justify-between gap-2 min-w-0">
                <span className="font-bold truncate flex items-center gap-1.5 min-w-0">
                  <Lock className="w-3 h-3 text-amber-400 shrink-0" />
                  <span className="truncate">
                    {lang === "es" && tr.title_es ? tr.title_es : tr.title}
                  </span>
                </span>
                <span className="shrink-0 inline-flex items-center px-1.5 py-0.5 rounded font-mono text-[9px] tracking-[0.15em] uppercase bg-amber-700/30 text-amber-300 border border-amber-700/40">
                  {tierLabel(tr.audience, lang)}
                </span>
              </div>
              <div className="flex gap-1 shrink-0">
                <Link
                  to={`/training/${tr.slug}/poster`}
                  className="inline-flex items-center gap-1 px-2 py-1 rounded bg-slate-700 hover:bg-slate-600 text-white font-mono font-bold uppercase tracking-wide transition-colors"
                  data-testid={`admin-training-qr-view-${tr.slug}`}
                >
                  {t("View")}
                </Link>
                <Link
                  to={`/training/${tr.slug}/poster?autoprint=1`}
                  className="inline-flex items-center gap-1 px-2 py-1 rounded bg-amber-600 hover:bg-amber-700 text-white font-mono font-bold uppercase tracking-wide transition-colors"
                  data-testid={`admin-training-qr-print-${tr.slug}`}
                >
                  <Printer className="w-3 h-3" />
                  {t("Print")}
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
