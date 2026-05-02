import React from "react";
import { QRCodeSVG } from "qrcode.react";
import { Box, BookOpen, ScanLine } from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { useHubHome } from "@/components/HubBackLink";
import { useT } from "@/lib/i18n";

/**
 * Trench Box QR Poster — Tabulated Data Library edition.
 *
 * The poster has been pivoted from the old fleet-table format to the new
 * crew-education direction. It still keeps the OSHA soil-type quick
 * reference (the most useful thing for a foreman in the field) but the
 * call to action is now: scan → bilingual "What is Tabulated Data?"
 * primer + manufacturer PDFs for every shield.
 */
export default function TrenchBoxPosterCard() {
  const { t } = useT();
  const hubHome = useHubHome();

  const trenchUrl = "https://mascidocs.com/trench-boxes";

  const soilRows = [
    {
      label: t("Type A — Cohesive (clay)"),
      desc: t("Most stable. Compact, fine-grained."),
      tone: "emerald",
    },
    {
      label: t("Type B — Cohesive or granular"),
      desc: t("Average. Silty clay, dry rock."),
      tone: "amber",
    },
    {
      label: t("Type C — Granular / submerged"),
      desc: t("Least stable. Sand, gravel, water."),
      tone: "red",
    },
  ];

  const toneCls = (tone) =>
    tone === "emerald"
      ? "border-emerald-600 bg-emerald-50 text-emerald-900"
      : tone === "amber"
      ? "border-amber-600 bg-amber-50 text-amber-900"
      : "border-red-700 bg-red-50 text-red-900";

  return (
    <div
      className="bg-white border-2 border-slate-300 print:border-0 rounded-md p-8 sm:p-10 print:p-6 shadow-xl print:shadow-none"
      data-testid="trench-poster-card"
    >
      {/* Top banner */}
      <div className="flex items-start justify-between gap-6 pb-5 border-b-4 border-red-700">
        <div className="flex-1">
          <MasciLogo variant="lockup" size="2xl" onLight homeLink={hubHome} />
          <div className="mt-3 font-mono text-[11px] uppercase tracking-[0.3em] text-red-700 font-bold">
            {t("OSHA 1926 Subpart P · Excavations")}
          </div>
        </div>
        <div className="text-right">
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500">
            {t("Office")}
          </div>
          <div className="font-display font-black text-slate-900 text-xl leading-none mt-1">
            386-322-4500
          </div>
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-1">
            safety@mascigc.com
          </div>
        </div>
      </div>

      {/* Hero */}
      <div className="grid grid-cols-1 sm:grid-cols-[auto,1fr] gap-6 mt-7 items-center">
        <div className="bg-slate-900 p-4 rounded-md inline-flex items-center justify-center">
          <QRCodeSVG
            value={trenchUrl}
            size={200}
            bgColor="#0F172A"
            fgColor="#FFFFFF"
            level="M"
            marginSize={1}
            data-testid="poster-qr"
          />
        </div>
        <div>
          <div className="font-mono text-[11px] uppercase tracking-[0.3em] text-red-700 font-bold inline-flex items-center gap-2">
            <ScanLine className="w-4 h-4" /> {t("Know before you dig.")}
          </div>
          <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tight text-slate-900 leading-[0.95] mt-2">
            {t("Tabulated Data Library")}
          </h1>
          <h2 className="font-display text-lg sm:text-xl font-bold text-slate-700 mt-2 leading-snug">
            {t(
              "One scan. Every MASCI trench shield. Manufacturer-stamped depth, width, and soil-type ratings."
            )}
          </h2>

          {/* Bilingual primer tagline */}
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="border-l-4 border-red-700 pl-3 py-1">
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-red-700 font-bold">
                EN · What is tabulated data?
              </div>
              <p className="text-slate-800 text-sm mt-1 leading-snug">
                {t(
                  "The manufacturer's engineered chart that tells you the deepest hole this exact shield is rated for in your soil type. No chart on site = no protective system."
                )}
              </p>
            </div>
            <div className="border-l-4 border-red-700 pl-3 py-1">
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-red-700 font-bold">
                ES · ¿Qué son los datos tabulados?
              </div>
              <p className="text-slate-800 text-sm mt-1 leading-snug">
                La tabla de ingeniería del fabricante que indica la profundidad
                máxima permitida para esta caja en tu tipo de suelo. Sin tabla
                en el sitio = sin sistema de protección.
              </p>
            </div>
          </div>

          <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-slate-500 mt-4 break-all">
            {trenchUrl.replace(/^https?:\/\//, "")}
          </div>
        </div>
      </div>

      {/* Soil type quick reference */}
      <div className="mt-8">
        <div className="font-mono text-[11px] uppercase tracking-[0.3em] text-red-700 font-black mb-3">
          {t("Soil Type Quick Reference")}
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {soilRows.map((row) => (
            <div key={row.label} className={`border-2 rounded-md p-4 ${toneCls(row.tone)}`}>
              <div className="font-display text-sm font-black leading-tight">{row.label}</div>
              <div className="text-xs mt-1.5 leading-relaxed">{row.desc}</div>
            </div>
          ))}
        </div>
        <p className="text-slate-700 text-sm mt-3 leading-relaxed">
          <span className="font-black text-red-700">·</span>{" "}
          {t(
            "When in doubt — call it Type C and get a Competent Person on site before the next bucket."
          )}
        </p>
      </div>

      {/* How to use the library */}
      <div className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="border-2 border-slate-300 rounded-md p-4 bg-slate-50">
          <div className="inline-flex items-center justify-center w-9 h-9 rounded-md bg-red-700 text-white mb-2">
            <ScanLine className="w-5 h-5" />
          </div>
          <div className="font-display font-black text-slate-900 text-sm leading-tight">
            1. {t("Scan the QR")}
          </div>
          <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
            {t("Open your phone camera. Point at the code. Tap the link.")}
          </p>
        </div>
        <div className="border-2 border-slate-300 rounded-md p-4 bg-slate-50">
          <div className="inline-flex items-center justify-center w-9 h-9 rounded-md bg-red-700 text-white mb-2">
            <Box className="w-5 h-5" />
          </div>
          <div className="font-display font-black text-slate-900 text-sm leading-tight">
            2. {t("Pick your shield")}
          </div>
          <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
            {t(
              "Find the manufacturer + model stamped on the box. Tap it in the library."
            )}
          </p>
        </div>
        <div className="border-2 border-slate-300 rounded-md p-4 bg-slate-50">
          <div className="inline-flex items-center justify-center w-9 h-9 rounded-md bg-red-700 text-white mb-2">
            <BookOpen className="w-5 h-5" />
          </div>
          <div className="font-display font-black text-slate-900 text-sm leading-tight">
            3. {t("Read the chart")}
          </div>
          <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
            {t(
              "Match your soil type to the max depth before the bucket touches dirt."
            )}
          </p>
        </div>
      </div>

      {/* Footer */}
      <div className="mt-8 pt-5 border-t-2 border-black flex flex-col sm:flex-row items-center justify-between gap-2">
        <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-slate-700">
          {t("Post inside every excavation kit toolbox.")}
        </div>
        <div className="font-display font-black text-red-700 tracking-tight text-sm">
          {t("Accountability · Adapt · Overcome")}
        </div>
      </div>

      {/* Developer credit */}
      <div className="mt-3 text-center font-mono text-[9px] uppercase tracking-[0.3em] text-slate-400">
        © {new Date().getFullYear()} MASCI · {t("Developed by")} The Judd Group LLC
      </div>
    </div>
  );
}
