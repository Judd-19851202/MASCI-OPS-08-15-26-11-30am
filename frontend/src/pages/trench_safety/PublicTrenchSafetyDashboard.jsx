// Public Trench Safety Dashboard — field-facing, read-only.
// Closes GAP-1 from the architecture lock certification.
//
// Allowed (per directive):
//   • Trench Safety Overview (counts only)
//   • Asset Lookup Entry
//   • QR Scan Entry (= same as lookup; QR codes resolve to this surface)
//   • Tabulated Data Access (link)
//   • Safety References (link → existing primer)
//   • Report Issue (modal)
//
// NOT allowed (per directive):
//   • Administration / management / edit
//   • Scan counters / statistics / usage metrics / gamification / engagement
//
// Routes: /trench-safety  (public, no auth)
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import {
  ShieldAlert, Boxes, BookOpen, AlertTriangle, ScanLine, Loader2,
  ArrowLeft, FileWarning,
} from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import PublicAssetLookup from "@/pages/trench_safety/PublicAssetLookup";
import PublicReportModal from "@/pages/trench_safety/PublicReportModal";

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

export default function PublicTrenchSafetyDashboard() {
  const { t } = useT();
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [reportOpen, setReportOpen] = useState(false);

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

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-cyan-700">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
          <Link to="/" className="inline-flex items-center text-white hover:text-cyan-300 text-xs font-bold uppercase tracking-wide" data-testid="public-dash-home">
            <ArrowLeft className="w-3.5 h-3.5 mr-1" /> {t("Home")}
          </Link>
          <MasciLogo variant="mark" size="md" homeLink="/" />
          <LangToggle />
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 sm:px-6 py-5">
        {/* Title */}
        <div className="text-center mb-4">
          <ScanLine className="w-7 h-7 mx-auto text-cyan-700" />
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-cyan-700 font-bold mt-1">
            {t("MASCI Trench Safety")} · {t("Field View")}
          </div>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-1" data-testid="public-dash-title">
            {t("Trench Safety")}
          </h1>
          <p className="text-slate-600 text-sm max-w-2xl mx-auto mt-2">
            {t("Field reference for every MASCI trench safety asset. Look up a box, open its tabulated data, or report a problem.")}
          </p>
        </div>

        {/* Coaching */}
        <div className="bg-amber-50 border border-amber-300 rounded-md p-3 flex items-start gap-2" data-testid="public-dash-coaching">
          <ShieldAlert className="w-4 h-4 text-amber-700 mt-0.5 shrink-0" />
          <p className="text-sm text-amber-900">
            <strong>{t("Coaching:")}</strong>{" "}
            {t("Match the box to the correct tabulated data before use. If the serial plate or tabulated data is missing, stop and contact Safety. A box on Inspection Hold is not available for use.")}
          </p>
        </div>

        {/* Overview — fleet shape, no PII, no names */}
        <section className="mt-5" data-testid="public-dash-overview">
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold mb-2">{t("Fleet Overview")}</div>
          {loading ? (
            <div className="flex items-center gap-2 text-slate-500" data-testid="public-dash-loading">
              <Loader2 className="w-5 h-5 animate-spin" /> {t("Loading overview…")}
            </div>
          ) : err ? (
            <div className="p-3 border border-red-300 bg-red-50 rounded text-red-900 text-sm" data-testid="public-dash-error">{err}</div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2" data-testid="public-dash-stats">
              <Stat label={t("Active Assets")}    value={overview?.total_active_assets ?? 0}                 testId="stat-active" />
              <Stat label={t("Available")}        value={totals["Available"] ?? 0}                          testId="stat-available" />
              <Stat label={t("Inspection Hold")}  value={totals["Inspection Hold"] ?? 0} tone={(totals["Inspection Hold"] ?? 0) > 0 ? "warn" : "default"} testId="stat-hold" />
              <Stat label={t("Repair")}           value={totals["Repair"] ?? 0} tone={(totals["Repair"] ?? 0) > 0 ? "danger" : "default"} testId="stat-repair" />
            </div>
          )}
        </section>

        {/* Asset Lookup */}
        <section className="mt-5">
          <PublicAssetLookup />
        </section>

        {/* Action tiles */}
        <section className="mt-5 grid grid-cols-1 sm:grid-cols-3 gap-2" data-testid="public-dash-actions">
          <Link
            to="/trench-boxes"
            className="bg-white border border-slate-200 rounded-md p-4 hover:border-cyan-600 hover:shadow transition"
            data-testid="public-dash-tabdata"
          >
            <BookOpen className="w-5 h-5 text-cyan-700" />
            <div className="font-display text-base font-black text-slate-900 mt-2">{t("Tabulated Data")}</div>
            <div className="text-xs text-slate-600 mt-1">{t("Manufacturer-engineered OSHA PDFs · per-box folders + general library.")}</div>
          </Link>
          <Link
            to="/trench-boxes"
            className="bg-white border border-slate-200 rounded-md p-4 hover:border-cyan-600 hover:shadow transition"
            data-testid="public-dash-references"
          >
            <FileWarning className="w-5 h-5 text-cyan-700" />
            <div className="font-display text-base font-black text-slate-900 mt-2">{t("Safety References")}</div>
            <div className="text-xs text-slate-600 mt-1">{t("Plain-English / Spanish primer · what tabulated data is and how to read it in the field.")}</div>
          </Link>
          <button
            onClick={() => setReportOpen(true)}
            className="bg-white border border-amber-300 rounded-md p-4 hover:border-amber-500 hover:shadow transition text-left"
            data-testid="public-dash-report"
          >
            <AlertTriangle className="w-5 h-5 text-amber-700" />
            <div className="font-display text-base font-black text-slate-900 mt-2">{t("Report a Problem")}</div>
            <div className="text-xs text-slate-600 mt-1">{t("Damage · Unsafe Condition · Missing Pins · Missing Labels. Goes straight to Safety.")}</div>
          </button>
        </section>

        {/* QR helper */}
        <section className="mt-5 p-3 border border-slate-200 bg-white rounded text-xs text-slate-600" data-testid="public-dash-qr-help">
          <ScanLine className="w-3.5 h-3.5 inline mr-1 -mt-0.5 text-cyan-700" />
          <strong className="text-slate-700">{t("QR Scan:")}</strong>{" "}
          {t("Scan the QR label on any MASCI trench box to open its asset record. Scanning does not move the asset — location updates when the asset is assigned, transported, or returned.")}
        </section>

        <footer className="mt-8 text-center text-[10px] uppercase tracking-[0.2em] text-slate-400 font-mono">
          {t("MASCI Operations Platform")} · {t("Field-safe view")}
        </footer>
      </main>

      <PublicReportModal
        open={reportOpen}
        onClose={() => setReportOpen(false)}
      />
    </div>
  );
}
