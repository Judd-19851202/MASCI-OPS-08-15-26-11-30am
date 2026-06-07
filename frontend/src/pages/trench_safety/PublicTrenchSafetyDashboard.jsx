// Public Trench Safety Dashboard — field-facing, read-only.
//
// Sprint: Public Trench Safety UX Correction.
//
// This is the field command center for trench safety. It surfaces:
//   • Trench Safety purpose
//   • Asset Lookup
//   • QR Scan guidance
//   • Tabulated Data access  → /trench-safety/tabulated-data
//   • Safety References      → /trench-safety/references
//   • Report a Problem       → /trench-safety/report
//   • Fleet overview         (counts only, no PII)
//   • "Scanning does not move this asset" coaching
//
// Distinct surfaces: Tabulated Data and Safety References live on
// separate public routes — Tabulated Data holds engineered PDFs and
// limits, References holds OSHA / competent-person / stop-work content.
//
// NOT allowed (per directive):
//   • Administration / management / edit
//   • Scan counters / statistics / usage metrics / gamification
//
// Route: /trench-safety  (public, no auth)
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import {
  ShieldAlert, BookOpen, AlertTriangle, ScanLine, Loader2,
  FileWarning, Search, ArrowRight, OctagonAlert, HardHat,
} from "lucide-react";
import PublicTrenchHeader from "@/components/trench/PublicTrenchHeader";
import { useT } from "@/lib/i18n";
import PublicAssetLookup from "@/pages/trench_safety/PublicAssetLookup";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function Stat({ label, value, tone = "default", testId }) {
  const toneClass = tone === "warn"
    ? "text-amber-700"
    : tone === "danger"
      ? "text-red-700"
      : "text-slate-900";
  return (
    <div className="bg-white border border-slate-200 rounded-md p-4 text-center" data-testid={testId}>
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500">{label}</div>
      <div className={`font-display text-3xl font-black mt-1 leading-none ${toneClass}`}>{value}</div>
    </div>
  );
}

function ActionTile({ to, onClick, icon: Icon, title, body, tone = "default", testId }) {
  const toneClasses = {
    default: "border-slate-200 hover:border-cyan-600",
    danger:  "border-red-300 hover:border-red-500 bg-red-50/30",
    warn:    "border-amber-300 hover:border-amber-500 bg-amber-50/30",
  }[tone];
  const iconColor = {
    default: "text-cyan-700",
    danger:  "text-red-700",
    warn:    "text-amber-700",
  }[tone];
  const inner = (
    <>
      <Icon className={`w-5 h-5 ${iconColor}`} />
      <div className="font-display text-base font-black text-slate-900 mt-2 leading-tight">{title}</div>
      <div className="text-xs text-slate-600 mt-1 leading-snug">{body}</div>
      <div className="text-[10px] uppercase tracking-[0.14em] font-bold text-cyan-700 mt-2 inline-flex items-center gap-0.5">
        {/* contextual open hint */}
        Open <ArrowRight className="w-3 h-3" />
      </div>
    </>
  );
  if (to) {
    return (
      <Link to={to} className={`block bg-white border rounded-md p-4 transition hover:shadow ${toneClasses}`} data-testid={testId}>
        {inner}
      </Link>
    );
  }
  return (
    <button
      type="button"
      onClick={onClick}
      className={`text-left bg-white border rounded-md p-4 transition hover:shadow ${toneClasses}`}
      data-testid={testId}
    >
      {inner}
    </button>
  );
}

export default function PublicTrenchSafetyDashboard() {
  const { t } = useT();
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await axios.get(`${API}/trench-safety/public/overview`);
        if (!cancelled) setOverview(r.data);
      } catch (e) {
        if (!cancelled) setErr(e?.response?.data?.detail || e?.message || t("Could not load overview."));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [t]);

  const totals = overview?.counts_by_status || {};
  const typeTotals = overview?.counts_by_type || {};

  return (
    <div className="min-h-screen bg-slate-50" data-testid="public-dash-page">
      <div className="caution-stripe" />
      <PublicTrenchHeader
        backTo="/safety"
        backLabel="Back to Safety"
        testIdPrefix="public-dash"
        accent="cyan"
      />

      <main className="max-w-3xl mx-auto px-4 sm:px-6 py-5">
        {/* Title */}
        <div className="text-center mb-4">
          <ScanLine className="w-7 h-7 mx-auto text-cyan-700" />
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-cyan-700 font-bold mt-1">
            {t("MASCI Trench Safety")} · {t("Field Command")}
          </div>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-1" data-testid="public-dash-title">
            {t("Trench Safety")}
          </h1>
          <p className="text-slate-600 text-sm max-w-2xl mx-auto mt-2" data-testid="public-dash-purpose">
            {t("Every MASCI trench box, end panel, spreader, and shore — tracked, inspected, certified, and field-ready. This is your live reference: look up an asset, scan a QR, open OSHA-aligned references, or report a problem the moment you see it.")}
          </p>
        </div>

        {/* Stop-work + coaching strip */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-4" data-testid="public-dash-coaching-row">
          <div className="bg-red-50 border-2 border-red-300 rounded-md p-3 flex items-start gap-2" data-testid="public-dash-stopwork">
            <OctagonAlert className="w-4 h-4 text-red-700 mt-0.5 shrink-0" />
            <p className="text-xs text-red-900 leading-snug">
              <strong className="uppercase tracking-[0.08em]">{t("Stop-Work Authority.")}</strong>{" "}
              {t("If anything looks wrong, stop the job. You will never be punished for keeping a crew alive.")}
            </p>
          </div>
          <div className="bg-amber-50 border border-amber-300 rounded-md p-3 flex items-start gap-2" data-testid="public-dash-coaching">
            <ShieldAlert className="w-4 h-4 text-amber-700 mt-0.5 shrink-0" />
            <p className="text-xs text-amber-900 leading-snug">
              <strong>{t("Match the box to its tabulated data.")}</strong>{" "}
              {t("If the serial plate or data sheet is missing, stop and contact Safety.")}
            </p>
          </div>
        </div>

        {/* Asset Lookup — primary action */}
        <section className="mt-2" data-testid="public-dash-lookup-section">
          <div className="bg-slate-900 border-l-4 border-cyan-500 rounded-md p-4">
            <div className="flex items-center gap-2 mb-2">
              <Search className="w-4 h-4 text-cyan-400" />
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-cyan-300 font-bold">
                {t("Asset Lookup")}
              </div>
            </div>
            <div className="text-xs text-slate-300 mb-3">
              {t("Type the asset tag printed on any MASCI trench box (TB-07, EP-001, SP-001…) to see its status, last inspection, and tabulated data.")}
            </div>
            <div className="bg-white rounded p-3">
              <PublicAssetLookup compact />
            </div>
          </div>
        </section>

        {/* QR scan guidance */}
        <section className="mt-3 p-3 border border-cyan-200 bg-cyan-50/60 rounded text-xs text-cyan-900" data-testid="public-dash-qr-help">
          <div className="flex items-start gap-2">
            <ScanLine className="w-4 h-4 text-cyan-700 mt-0.5 shrink-0" />
            <div>
              <strong className="text-cyan-900 uppercase tracking-[0.06em]">{t("QR Scan Guidance.")}</strong>{" "}
              {t("Scan the QR label on any MASCI trench box to open its asset record. Confirm the asset ID, status, serial number, and tabulated-data link before use.")}{" "}
              <strong>{t("Scanning does not move this asset")}</strong>{" "}
              {t("— location only updates when the asset is assigned, transported, or returned.")}
            </div>
          </div>
        </section>

        {/* Action tiles — Tabulated Data · References · Report */}
        <section className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-2" data-testid="public-dash-actions">
          <ActionTile
            to="/trench-safety/tabulated-data"
            icon={BookOpen}
            title={t("Tabulated Data")}
            body={t("Manufacturer-engineered OSHA PDFs · per-box data sheets · soil-type, spreader, and depth limits.")}
            testId="public-dash-tabdata"
          />
          <ActionTile
            to="/trench-safety/references"
            icon={FileWarning}
            title={t("Safety References")}
            body={t("OSHA guidance · competent-person reminders · stop-work · missing pins/labels · unsafe-condition examples.")}
            tone="warn"
            testId="public-dash-references"
          />
          <ActionTile
            to="/trench-safety/report"
            icon={AlertTriangle}
            title={t("Report a Problem")}
            body={t("Damage · Unsafe Condition · Missing Pins · Missing Labels. Goes straight to Safety.")}
            tone="danger"
            testId="public-dash-report"
          />
        </section>

        {/* Fleet overview — counts only */}
        <section className="mt-5" data-testid="public-dash-overview">
          <div className="flex items-center justify-between mb-2">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold">{t("Fleet Overview")}</div>
            <div className="text-[10px] uppercase tracking-[0.18em] text-slate-400 font-mono">
              {t("Counts only · no PII")}
            </div>
          </div>
          {loading ? (
            <div className="flex items-center gap-2 text-slate-500" data-testid="public-dash-loading">
              <Loader2 className="w-5 h-5 animate-spin" /> {t("Loading overview…")}
            </div>
          ) : err ? (
            <div className="p-3 border border-red-300 bg-red-50 rounded text-red-900 text-sm" data-testid="public-dash-error">{err}</div>
          ) : (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2" data-testid="public-dash-stats">
                <Stat label={t("Active Assets")}    value={overview?.total_active_assets ?? 0}                 testId="stat-active" />
                <Stat label={t("Available")}        value={totals["Available"] ?? 0}                          testId="stat-available" />
                <Stat label={t("Inspection Hold")}  value={totals["Inspection Hold"] ?? 0} tone={(totals["Inspection Hold"] ?? 0) > 0 ? "warn" : "default"} testId="stat-hold" />
                <Stat label={t("Repair")}           value={totals["Repair"] ?? 0} tone={(totals["Repair"] ?? 0) > 0 ? "danger" : "default"} testId="stat-repair" />
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-2" data-testid="public-dash-type-stats">
                <Stat label={t("Trench Boxes")}     value={typeTotals["Trench Box"] ?? 0}      testId="stat-tb" />
                <Stat label={t("End Panels")}       value={typeTotals["End Panel"] ?? 0}       testId="stat-ep" />
                <Stat label={t("Spreader Bars")}    value={typeTotals["Spreader Bar"] ?? 0}    testId="stat-sp" />
                <Stat label={t("Other Assets")}     value={(typeTotals["Hydraulic Shore"] ?? 0) + (typeTotals["Slide Rail System"] ?? 0) + (typeTotals["Trench Jack"] ?? 0) + (typeTotals["Ladder"] ?? 0) + (typeTotals["Accessory"] ?? 0)} testId="stat-other" />
              </div>
            </>
          )}
        </section>

        {/* Competent person & training reminder */}
        <section className="mt-5 p-3 border border-slate-200 bg-white rounded" data-testid="public-dash-competent">
          <div className="flex items-start gap-2">
            <HardHat className="w-4 h-4 text-cyan-700 mt-0.5 shrink-0" />
            <div className="text-xs text-slate-700 leading-relaxed">
              <strong className="text-slate-900 uppercase tracking-[0.06em]">{t("Competent Person Required.")}</strong>{" "}
              {t("Every trench 5 ft or deeper needs a designated competent person on-site — trained to identify hazards, authorized to correct them, and present before crews enter. No competent person, no entry.")}
            </div>
          </div>
        </section>

        <footer className="mt-8 text-center text-[10px] uppercase tracking-[0.2em] text-slate-400 font-mono">
          {t("MASCI Operations Platform")} · {t("Field-safe view")}
        </footer>
      </main>
    </div>
  );
}
