// Mobile-first QR landing page — PUBLIC (no auth).
//
// Reads from /api/trench-safety/public/assets/{asset_id} (Phase 2,
// field-safe projection). Shows only the operational data a crew
// member needs to confirm the box is safe to use. Does NOT expose
// admin controls, full inventory, or internal audit data.
//
// Route: /trench-safety/assets/:assetId
import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import axios from "axios";
import {
  Loader2, AlertTriangle, FileWarning, ShieldAlert,
  BookOpen, ScanLine, ArrowLeft,
} from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const STATUS_STYLE = {
  "Available":       { bg: "bg-emerald-100", text: "text-emerald-900", ring: "ring-emerald-300" },
  "Assigned":        { bg: "bg-blue-100",    text: "text-blue-900",    ring: "ring-blue-300" },
  "In Transport":    { bg: "bg-cyan-100",    text: "text-cyan-900",    ring: "ring-cyan-300" },
  "Inspection Hold": { bg: "bg-amber-100",   text: "text-amber-900",   ring: "ring-amber-400" },
  "Repair":          { bg: "bg-red-100",     text: "text-red-900",     ring: "ring-red-300" },
  "Retired":         { bg: "bg-slate-200",   text: "text-slate-700",   ring: "ring-slate-300" },
};

function Row({ label, value, mono, danger, testId }) {
  return (
    <div className="flex items-baseline justify-between gap-3 py-2 border-b border-slate-100 last:border-0" data-testid={testId}>
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500">{label}</div>
      <div className={`text-base text-right ${mono ? "font-mono" : ""} ${danger ? "text-amber-700 font-bold" : (value ? "text-slate-900 font-bold" : "text-slate-400")}`}>
        {(value === null || value === undefined || value === "") ? "—" : value}
      </div>
    </div>
  );
}

export default function TrenchSafetyQrLanding() {
  const { t } = useT();
  const { assetId } = useParams();
  const [doc, setDoc] = useState(null);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setErr("");
      try {
        const r = await axios.get(`${API}/trench-safety/public/assets/${encodeURIComponent(assetId)}`);
        if (!cancelled) setDoc(r.data);
      } catch (e) {
        if (!cancelled) setErr(e?.response?.data?.detail || e?.message || "Asset not found");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [assetId]);

  const status = doc?.operational_status || "Available";
  const onHold = status === "Inspection Hold" || status === "Repair";
  const sStyle = STATUS_STYLE[status] || STATUS_STYLE["Available"];

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-cyan-700">
        <div className="max-w-md mx-auto px-4 py-3 flex items-center justify-between gap-3">
          <Link to="/" className="inline-flex items-center text-white hover:text-cyan-300 text-xs font-bold uppercase tracking-wide" data-testid="qr-home-link">
            <ArrowLeft className="w-3.5 h-3.5 mr-1" /> {t("Home")}
          </Link>
          <MasciLogo variant="mark" size="md" homeLink="/" />
          <LangToggle />
        </div>
      </header>

      <main className="max-w-md mx-auto px-4 py-5">
        <div className="text-center mb-3">
          <ScanLine className="w-7 h-7 mx-auto text-cyan-700" />
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-cyan-700 font-bold mt-1">
            {t("MASCI Trench Safety")} · {t("Field View")}
          </div>
        </div>

        {loading ? (
          <div className="flex flex-col items-center gap-2 mt-10 text-slate-500" data-testid="qr-loading">
            <Loader2 className="w-7 h-7 animate-spin" />
            <span>{t("Loading asset…")}</span>
          </div>
        ) : err ? (
          <div className="mt-6 p-4 border border-red-300 bg-red-50 rounded text-red-900 text-sm" data-testid="qr-error">
            <div className="font-bold">{t("Asset not found")}</div>
            <div className="text-xs mt-1">{t("This QR is not linked to a known MASCI trench safety asset. Contact Safety.")}</div>
          </div>
        ) : (
          <>
            {/* Big asset id + status pill */}
            <div className="bg-white border-2 border-slate-200 rounded-lg p-5 text-center" data-testid="qr-hero">
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500">
                {t(doc.asset_type || "Trench Box")}
              </div>
              <div className="font-display text-5xl font-black tracking-tight text-slate-900 mt-1 leading-none" data-testid="qr-asset-id">
                {doc.asset_id}
              </div>
              <div className="text-base text-slate-600 mt-2">{doc.size || ""}{doc.color ? ` · ${doc.color}` : ""}</div>
              <div className="mt-4">
                <span className={`inline-block px-4 py-2 rounded-full ring-2 font-bold uppercase tracking-[0.12em] text-sm ${sStyle.bg} ${sStyle.text} ${sStyle.ring}`} data-testid="qr-status">
                  {t(status)}
                </span>
              </div>
            </div>

            {/* Hold warning */}
            {onHold && (
              <div className="mt-4 p-4 border-2 border-amber-400 bg-amber-50 rounded text-amber-900" data-testid="qr-hold-warning">
                <AlertTriangle className="w-5 h-5 inline -mt-1 mr-1.5" />
                <strong className="uppercase tracking-[0.08em]">{t("Do not use")}.</strong>{" "}
                {status === "Inspection Hold"
                  ? t("This asset is on Inspection Hold. A competent person must clear it before use.")
                  : t("This asset is under Repair. It is not available for the field.")}
              </div>
            )}

            {/* Needs review / missing serial */}
            {(doc.missing_serial_number || doc.needs_review) && (
              <div className="mt-4 p-4 border border-amber-300 bg-amber-50 rounded text-amber-900 text-sm" data-testid="qr-needs-review">
                {doc.missing_serial_number && (
                  <div className="inline-flex items-start gap-1.5"><FileWarning className="w-4 h-4 mt-0.5" />{t("Serial number not on file — verify the physical plate before use.")}</div>
                )}
                {doc.needs_review && !doc.missing_serial_number && (
                  <div className="inline-flex items-start gap-1.5"><AlertTriangle className="w-4 h-4 mt-0.5" />{t("This asset is flagged for Safety review.")}</div>
                )}
              </div>
            )}

            {/* Identification card */}
            <div className="mt-4 bg-white border border-slate-200 rounded-md p-3" data-testid="qr-id-card">
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold mb-1">{t("Asset Details")}</div>
              <Row label={t("Manufacturer")} value={doc.manufacturer} testId="qr-f-mfr" />
              <Row label={t("Model")}        value={doc.model} testId="qr-f-model" />
              <Row label={t("Size")}         value={doc.size} testId="qr-f-size" />
              <Row label={t("Color")}        value={doc.color} testId="qr-f-color" />
              <Row label={t("Condition")}    value={t(doc.condition || "Good")} testId="qr-f-cond" />
            </div>

            {/* Operational card */}
            <div className="mt-3 bg-white border border-slate-200 rounded-md p-3" data-testid="qr-op-card">
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold mb-1">{t("Current Use")}</div>
              <Row label={t("Status")}            value={t(status)} testId="qr-f-status" />
              <Row label={t("Current Location")}  value={doc.current_location} testId="qr-f-loc" />
              <Row label={t("Current Project")}   value={doc.current_project_name} testId="qr-f-proj" />
              <Row label={t("Last Inspection")}   value={doc.last_inspection_at ? doc.last_inspection_at.slice(0, 10) : null} danger={!doc.last_inspection_at} testId="qr-f-last-insp" />
              <Row label={t("Tabulated Data")}    value={doc.tabulated_data_missing ? t("missing") : t("on file")} danger={doc.tabulated_data_missing} testId="qr-f-tabdata" />
            </div>

            {/* Tabulated data link */}
            <Link
              to="/safety/trench-safety/tabulated-data"
              className="mt-4 block bg-cyan-700 hover:bg-cyan-800 text-white text-center rounded-md py-3 font-bold uppercase tracking-[0.12em] text-sm"
              data-testid="qr-tabdata-link"
            >
              <BookOpen className="w-4 h-4 inline -mt-0.5 mr-1.5" />
              {t("Open Tabulated Data")}
            </Link>

            {/* Coaching */}
            <div className="mt-5 p-3 border border-slate-200 bg-white rounded text-xs text-slate-600 leading-relaxed" data-testid="qr-coaching">
              <ShieldAlert className="w-3.5 h-3.5 inline -mt-0.5 mr-1 text-cyan-700" />
              <strong className="text-slate-700">{t("Coaching:")}</strong>{" "}
              {t("Scanning confirms the asset record — it does not move the asset. Location updates when the asset is assigned, transported, or returned. Report damage before the box goes into the trench.")}
            </div>
          </>
        )}

        <footer className="mt-8 text-center text-[10px] uppercase tracking-[0.2em] text-slate-400 font-mono">
          {t("MASCI Operations Platform")} · {t("Field-safe view")}
        </footer>
      </main>
    </div>
  );
}
