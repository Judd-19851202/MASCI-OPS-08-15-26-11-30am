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
import { OperationalPageFrame } from "@/components/public/OperationalPageFrame";
import { OperationalStatusBadge } from "@/components/public/OperationalStatusBadge";
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
    <div className="wp17-public-card p-4 text-center" data-testid={testId}>
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
      <Link to={to} className={`block wp17-public-card p-4 transition hover:shadow-md ${toneClasses}`} data-testid={testId}>
        {inner}
      </Link>
    );
  }
  return (
    <button
      type="button"
      onClick={onClick}
      className={`text-left wp17-public-card p-4 transition hover:shadow-md ${toneClasses}`}
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

  const heroMeta = (
    <>
      <OperationalStatusBadge tone="cyan" testId="public-dash-meta-lookup">{t("Live asset lookup")}</OperationalStatusBadge>
      <OperationalStatusBadge tone="amber" testId="public-dash-meta-qr">{t("QR launch")}</OperationalStatusBadge>
      {!loading && !err ? (
        <OperationalStatusBadge tone="emerald" testId="public-dash-meta-active">
          {t("Active assets")} · {overview?.total_active_assets ?? 0}
        </OperationalStatusBadge>
      ) : null}
    </>
  );

  return (
    <OperationalPageFrame
      testId="public-dash-page"
      backTo="/safety"
      backLabel={t("Back to Safety")}
      accent="cyan"
      familyLabel={t("MASCI Trench Safety")}
      familyMeta={t("Public trench workflow")}
      mainWidthClass="max-w-5xl"
      heroIcon={ScanLine}
      kicker={t("MASCI Trench Safety · Field Command")}
      title={t("Trench Safety")}
      description={t("Open the same field-safe trench intelligence crews use on site: look up an asset, confirm its status, jump to tabulated data, or escalate a problem immediately.")}
      heroMeta={heroMeta}
      heroAside={(
        <div className="wp17-panel p-4" data-testid="public-dash-lookup-card">
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold mb-2">
            {t("Asset Lookup")}
          </div>
          <p className="text-sm text-slate-600 mb-3">
            {t("Type the asset tag from any MASCI trench box, panel, or spreader to confirm status, inspection freshness, and tabulated data before use.")}
          </p>
          <PublicAssetLookup compact />
        </div>
      )}
      footerText={t("MASCI Operations Platform · Field-safe trench workflow")}
    >
      <div className="space-y-5">

        {/* Stop-work + coaching strip */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3" data-testid="public-dash-coaching-row">
          <div className="rounded-[1.5rem] border-2 border-red-300 bg-red-50 p-4 flex items-start gap-3 shadow-[0_18px_40px_rgba(15,23,42,0.06)]" data-testid="public-dash-stopwork">
            <OctagonAlert className="w-4 h-4 text-red-700 mt-0.5 shrink-0" />
            <p className="text-xs text-red-900 leading-snug">
              <strong className="uppercase tracking-[0.08em]">{t("Stop-Work Authority.")}</strong>{" "}
              {t("If anything looks wrong, stop the job. You will never be punished for keeping a crew alive.")}
            </p>
          </div>
          <div className="rounded-[1.5rem] border border-amber-300 bg-amber-50 p-4 flex items-start gap-3 shadow-[0_18px_40px_rgba(15,23,42,0.06)]" data-testid="public-dash-coaching">
            <ShieldAlert className="w-4 h-4 text-amber-700 mt-0.5 shrink-0" />
            <p className="text-xs text-amber-900 leading-snug">
              <strong>{t("Match the box to its tabulated data.")}</strong>{" "}
              {t("If the serial plate or data sheet is missing, stop and contact Safety.")}
            </p>
          </div>
        </div>

        {/* QR scan guidance */}
        <section className="wp17-panel p-4 text-xs text-cyan-900 bg-cyan-50/50 border-cyan-200" data-testid="public-dash-qr-help">
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

        {/* Action tiles — Tabulated Data · References · Report · Excavation Ops */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3" data-testid="public-dash-actions">
          <ActionTile
            to="/trench-safety/excavation/new"
            icon={AlertTriangle}
            title={t("Excavation Operations")}
            body={t("Submit a field excavation record. Coaching first. EN / ES.")}
            testId="public-dash-excavation"
          />
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
        <section className="wp17-panel p-4" data-testid="public-dash-overview">
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
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 mt-2" data-testid="public-dash-type-stats">
                <Stat label={t("Trench Boxes")}     value={typeTotals["Trench Box"] ?? 0}      testId="stat-tb" />
                <Stat label={t("End Panels")}       value={typeTotals["End Panel"] ?? 0}       testId="stat-ep" />
                <Stat label={t("Spreader Bars")}    value={typeTotals["Spreader Bar"] ?? 0}    testId="stat-sp" />
                <Stat label={t("Road Plates")}      value={typeTotals["Road Plate"] ?? 0}      testId="stat-rp" />
                <Stat label={t("Other Assets")}     value={(typeTotals["Hydraulic Shore"] ?? 0) + (typeTotals["Slide Rail System"] ?? 0) + (typeTotals["Trench Jack"] ?? 0) + (typeTotals["Ladder"] ?? 0) + (typeTotals["Accessory"] ?? 0)} testId="stat-other" />
              </div>
            </>
          )}
        </section>

        {/* Competent person & training reminder */}
        <section className="wp17-panel p-4" data-testid="public-dash-competent">
          <div className="flex items-start gap-2">
            <HardHat className="w-4 h-4 text-cyan-700 mt-0.5 shrink-0" />
            <div className="text-xs text-slate-700 leading-relaxed">
              <strong className="text-slate-900 uppercase tracking-[0.06em]">{t("Competent Person Required.")}</strong>{" "}
              {t("Every trench 5 ft or deeper needs a designated competent person on-site — trained to identify hazards, authorized to correct them, and present before crews enter. No competent person, no entry.")}
            </div>
          </div>
        </section>
      </div>
    </OperationalPageFrame>
  );
}
