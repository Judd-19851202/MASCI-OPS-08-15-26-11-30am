import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { QRCodeSVG } from "qrcode.react";
import { Printer, ArrowLeft, Box } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { printReport } from "@/lib/printReport";
import { PrintWatermark } from "@/components/PrintWatermark";
import { api } from "@/lib/api";

/**
 * Trench Box QR Poster — printable letter-size handout that lives inside
 * every excavation kit toolbox. Foreman scans the QR with their phone
 * camera, the MASCI Trench Box Data page opens, and they can read every
 * shield's OSHA max-depth before breaking ground.
 *
 * Bilingual via the shared LangToggle. Defaults to English; ES button
 * swaps every visible string. The toggle hides at print time.
 */
export default function TrenchBoxPoster() {
  const { t } = useT();
  const [boxes, setBoxes] = useState([]);
  const [loading, setLoading] = useState(true);

  // Production-locked URL — printed posters keep working even while we
  // build/test on preview URLs.
  const trenchUrl = "https://mascidocs.com/trench-boxes";

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const r = await api.get("/trench-boxes");
        if (alive) setBoxes(r.data || []);
      } catch {
        if (alive) setBoxes([]);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

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
    <div className="min-h-screen blueprint-bg print:bg-white">
      <PrintWatermark />
      <div className="caution-stripe no-print" />

      {/* On-screen toolbar */}
      <header className="bg-slate-900 border-b-4 border-red-700 no-print">
        <div className="max-w-5xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between gap-3">
          <Link
            to="/admin/trench-boxes"
            className="inline-flex items-center text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide"
            data-testid="poster-back"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("Hub")}
          </Link>
          <div className="hidden sm:block font-mono text-xs uppercase tracking-[0.25em] text-red-400">
            {t("Trench Box QR Poster")}
          </div>
          <div className="flex items-center gap-2">
            <LangToggle />
            <Button
              onClick={printReport}
              className="h-10 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900"
              data-testid="poster-print-btn"
            >
              <Printer className="w-4 h-4 mr-2" /> {t("Print Poster")}
            </Button>
          </div>
        </div>
      </header>

      {/* The actual printable page */}
      <main className="max-w-5xl mx-auto px-5 sm:px-8 py-8 print:p-0">
        <div className="bg-white border-2 border-slate-300 print:border-0 rounded-md p-8 sm:p-10 print:p-6 shadow-xl print:shadow-none">
          {/* Top banner: logo + OSHA reference */}
          <div className="flex items-start justify-between gap-6 pb-5 border-b-4 border-red-700">
            <div className="flex-1">
              <MasciLogo variant="lockup" size="2xl" onLight homeLink="/admin" />
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

          {/* Hero: scan-to-open */}
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
                <Box className="w-4 h-4" /> {t("Scan before you dig.")}
              </div>
              <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tight text-slate-900 leading-[0.95] mt-2">
                {t(
                  "Every MASCI trench shield. OSHA max-depth by soil type. One scan, one tap, one answer."
                )}
              </h1>
              <p className="text-slate-700 text-base mt-3 leading-relaxed">
                {t(
                  "Open your phone camera. Point it at the QR. Tap the link. Find your shield. Read its Type-C max depth before the bucket touches dirt."
                )}
              </p>
              <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-slate-500 mt-3 break-all">
                {trenchUrl.replace(/^https?:\/\//, "")}
              </div>
            </div>
          </div>

          {/* Soil-type quick reference */}
          <div className="mt-8">
            <div className="font-mono text-[11px] uppercase tracking-[0.3em] text-red-700 font-black mb-3">
              {t("Soil Type Quick Reference")}
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {soilRows.map((row) => (
                <div
                  key={row.label}
                  className={`border-2 rounded-md p-4 ${toneCls(row.tone)}`}
                >
                  <div className="font-display text-sm font-black leading-tight">
                    {row.label}
                  </div>
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

          {/* Fleet snapshot table */}
          <div className="mt-8">
            <div className="flex items-baseline justify-between mb-3">
              <div className="font-mono text-[11px] uppercase tracking-[0.3em] text-red-700 font-black">
                {t("MASCI Trench Box Fleet at a Glance")}
              </div>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
                {loading
                  ? t("Loading…")
                  : `${boxes.length} ${t("Fleet on file")}`}
              </div>
            </div>
            <div className="border-2 border-slate-300 rounded-md overflow-hidden">
              <table className="w-full text-sm" data-testid="poster-fleet-table">
                <thead>
                  <tr className="bg-slate-900 text-white font-mono text-[10px] uppercase tracking-[0.2em]">
                    <th className="text-left px-3 py-2">
                      {t("Manufacturer · Model")}
                    </th>
                    <th className="text-left px-3 py-2">{t("Type")}</th>
                    <th className="text-right px-3 py-2">{t("Length")}</th>
                    <th className="text-right px-3 py-2">{t("Weight (lbs)")}</th>
                    <th className="text-right px-3 py-2">
                      {t("Type C-60 Max")}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {boxes.length === 0 && !loading && (
                    <tr>
                      <td
                        colSpan={5}
                        className="px-3 py-6 text-center text-slate-500 italic"
                      >
                        {t("No trench boxes have been added yet")}
                      </td>
                    </tr>
                  )}
                  {boxes.map((b, idx) => (
                    <tr
                      key={b.id}
                      className={
                        idx % 2 === 0 ? "bg-white" : "bg-slate-50 print:bg-white"
                      }
                    >
                      <td className="px-3 py-2 font-display font-bold text-slate-900">
                        {b.manufacturer} · {b.model}
                      </td>
                      <td className="px-3 py-2 text-slate-700">
                        {b.box_type || "—"}
                      </td>
                      <td className="px-3 py-2 text-right text-slate-700">
                        {b.length_ft ? `${b.length_ft} ft` : "—"}
                      </td>
                      <td className="px-3 py-2 text-right text-slate-700">
                        {b.weight_lbs || "—"}
                      </td>
                      <td className="px-3 py-2 text-right font-display font-black text-red-700">
                        {b.max_depth_type_c_60_ft
                          ? `${b.max_depth_type_c_60_ft} ft`
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-xs text-slate-500 italic mt-2">
              {t(
                "All depths per OSHA 1926.652. Verify against the manufacturer's tabulated data on every job."
              )}
            </p>
          </div>

          {/* Footer with motto */}
          <div className="mt-8 pt-5 border-t-2 border-black flex flex-col sm:flex-row items-center justify-between gap-2">
            <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-slate-700">
              {t("Post inside every excavation kit toolbox.")}
            </div>
            <div className="font-display font-black text-red-700 tracking-tight text-sm">
              {t("No Shortcuts · No Exceptions")}
            </div>
          </div>
        </div>
      </main>

      {/* Print-only sizing rules */}
      <style>{`
        @media print {
          @page { size: letter; margin: 0.4in; }
          body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
          .no-print { display: none !important; }
        }
      `}</style>
    </div>
  );
}
