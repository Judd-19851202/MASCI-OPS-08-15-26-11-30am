// Mobile-first QR landing page — PUBLIC (no auth).
//
// Reads from /api/trench-safety/public/assets/{asset_id} (Phase 2,
// field-safe projection). Shows only the operational data a crew
// member needs to confirm the box is safe to use.
//
// Sprint: Public Trench Safety UX Correction — adds prominent Serial
// Number near the top, prominent "missing — action required" banner
// when serial is absent, and contextual back-to-trench-safety nav.
//
// Route: /trench-safety/assets/:assetId
import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import {
  Loader2, AlertTriangle, FileWarning, ShieldAlert,
  BookOpen, ScanLine,
} from "lucide-react";
import { OperationalPageFrame } from "@/components/public/OperationalPageFrame";
import { OperationalStatusBadge } from "@/components/public/OperationalStatusBadge";
import { useT } from "@/lib/i18n";
import PublicReportModal from "@/pages/trench_safety/PublicReportModal";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const STATUS_STYLE = {
  Available: { bg: "bg-emerald-100", text: "text-emerald-900", ring: "ring-emerald-300" },
  Assigned: { bg: "bg-blue-100", text: "text-blue-900", ring: "ring-blue-300" },
  "In Transport": { bg: "bg-cyan-100", text: "text-cyan-900", ring: "ring-cyan-300" },
  "Inspection Hold": { bg: "bg-amber-100", text: "text-amber-900", ring: "ring-amber-400" },
  "Maintenance Hold": { bg: "bg-orange-100", text: "text-orange-900", ring: "ring-orange-400" },
  "Certification Hold": { bg: "bg-purple-100", text: "text-purple-900", ring: "ring-purple-400" },
  "Safety Hold": { bg: "bg-red-100", text: "text-red-900", ring: "ring-red-500" },
  Retired: { bg: "bg-slate-200", text: "text-slate-700", ring: "ring-slate-300" },
};

const HOLD_STATUSES = new Set([
  "Inspection Hold", "Maintenance Hold", "Certification Hold", "Safety Hold",
]);

const HOLD_MESSAGE = {
  "Inspection Hold": "This asset is on Inspection Hold. A competent person must clear it before use.",
  "Maintenance Hold": "This asset is under Maintenance. It is not available for the field.",
  "Certification Hold": "This asset's required certification is missing or expired. DO NOT USE.",
  "Safety Hold": "SAFETY HOLD — critical condition reported. DO NOT USE. Contact Safety immediately.",
};

function Row({ label, value, mono, danger, testId }) {
  return (
    <div className="flex items-baseline justify-between gap-3 py-2 border-b border-slate-100 last:border-0" data-testid={testId}>
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500">{label}</div>
      <div className={`text-base text-right ${mono ? "font-mono" : ""} ${danger ? "text-amber-700 font-bold" : value ? "text-slate-900 font-bold" : "text-slate-400"}`}>
        {value === null || value === undefined || value === "" ? "—" : value}
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
  const [reportOpen, setReportOpen] = useState(false);

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
    return () => {
      cancelled = true;
    };
  }, [assetId]);

  const status = doc?.operational_status || "Available";
  const onHold = HOLD_STATUSES.has(status);
  const sStyle = STATUS_STYLE[status] || STATUS_STYLE.Available;
  const serialMissing = doc
    ? Boolean(doc.missing_serial_number) || !(doc.serial_number && String(doc.serial_number).trim())
    : false;
  const serialDisplay = serialMissing ? t("Missing — Action Required") : doc?.serial_number;
  const statusTone = onHold ? "red" : status === "Available" ? "emerald" : "cyan";

  const heroMeta = loading ? (
    <OperationalStatusBadge tone="cyan" testId="qr-meta-loading">{t("Loading asset")}</OperationalStatusBadge>
  ) : err ? (
    <OperationalStatusBadge tone="red" testId="qr-meta-error">{t("Asset not found")}</OperationalStatusBadge>
  ) : (
    <>
      <OperationalStatusBadge tone={statusTone} testId="qr-meta-status">{t(status)}</OperationalStatusBadge>
      <OperationalStatusBadge tone="cyan" testId="qr-meta-type">{t(doc.asset_type || "Trench Box")}</OperationalStatusBadge>
      {doc.current_location ? (
        <OperationalStatusBadge tone="amber" testId="qr-meta-location">{doc.current_location}</OperationalStatusBadge>
      ) : null}
    </>
  );

  return (
    <>
      <OperationalPageFrame
        testId="qr-landing-page"
        backTo="/trench-safety"
        backLabel={t("Back to Trench Safety")}
        accent="cyan"
        familyLabel={t("MASCI Trench Safety")}
        familyMeta={t("Public trench workflow")}
        mainWidthClass="max-w-4xl"
        heroIcon={ScanLine}
        kicker={t("MASCI Trench Safety · Field View")}
        title={loading ? t("Trench Asset Lookup") : err ? t("Asset not found") : doc?.asset_id || t("Trench Asset Lookup")}
        description={loading
          ? t("Loading the field-safe asset record so crews can confirm status, serial, and tabulated data before entry.")
          : err
            ? t("This QR is not linked to a known MASCI trench-safety asset. Contact Safety before using the equipment.")
            : t("Confirm serial, status, last inspection, and tabulated-data availability before this asset goes into service.")}
        heroMeta={heroMeta}
        heroAside={!loading && !err ? (
          <div className={`rounded-[1.5rem] border-2 px-4 py-4 ${serialMissing ? "border-red-400 bg-red-50" : "border-slate-200 bg-white/92"}`} data-testid="qr-serial-block">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500">{t("Serial Number")}</div>
            <div className={`font-mono text-2xl font-black tracking-tight mt-1 ${serialMissing ? "text-red-700" : "text-slate-900"}`} data-testid="qr-serial-value">
              {serialDisplay || "—"}
            </div>
            {serialMissing ? (
              <div className="mt-2 text-[11px] text-red-800 font-bold uppercase tracking-[0.08em] inline-flex items-center gap-1" data-testid="qr-serial-missing-alert">
                <AlertTriangle className="w-3.5 h-3.5" />
                {t("Verify the physical serial plate before use · Report to Safety")}
              </div>
            ) : null}
          </div>
        ) : null}
        footerText={t("MASCI Operations Platform · QR trench workflow")}
      >
        <div className="max-w-3xl mx-auto space-y-4">
          {loading ? (
            <div className="wp17-panel flex flex-col items-center gap-2 py-12 text-slate-500" data-testid="qr-loading">
              <Loader2 className="w-7 h-7 animate-spin" />
              <span>{t("Loading asset…")}</span>
            </div>
          ) : err ? (
            <div className="rounded-[1.5rem] border border-red-300 bg-red-50 p-5 text-red-900 text-sm" data-testid="qr-error">
              <div className="font-bold">{t("Asset not found")}</div>
              <div className="text-xs mt-1">{t("This QR is not linked to a known MASCI trench safety asset. Contact Safety.")}</div>
            </div>
          ) : (
            <>
              <div className="wp17-public-card border-2 border-slate-200 p-5 text-center" data-testid="qr-hero">
                <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500">{t(doc.asset_type || "Trench Box")}</div>
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

              {onHold ? (
                <div className="rounded-[1.5rem] border-2 border-amber-400 bg-amber-50 p-4 text-amber-900" data-testid="qr-hold-warning">
                  <AlertTriangle className="w-5 h-5 inline -mt-1 mr-1.5" />
                  <strong className="uppercase tracking-[0.08em]">{t("Do not use")}.</strong>{" "}
                  {t(HOLD_MESSAGE[status] || "This asset is on hold. DO NOT USE.")}
                </div>
              ) : null}

              {doc.needs_review && !serialMissing ? (
                <div className="rounded-[1.5rem] border border-amber-300 bg-amber-50 p-4 text-amber-900 text-sm" data-testid="qr-needs-review">
                  <div className="inline-flex items-start gap-1.5">
                    <AlertTriangle className="w-4 h-4 mt-0.5" />
                    {t("This asset is flagged for Safety review.")}
                  </div>
                </div>
              ) : null}

              <div className="wp17-panel p-4" data-testid="qr-id-card">
                <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold mb-1">{t("Asset Details")}</div>
                <Row label={t("Asset ID")} value={doc.asset_id} mono testId="qr-f-asset-id" />
                <Row label={t("Asset Type")} value={t(doc.asset_type || "Trench Box")} testId="qr-f-type" />
                <Row label={t("Manufacturer")} value={doc.manufacturer} testId="qr-f-mfr" />
                <Row label={t("Model")} value={doc.model} testId="qr-f-model" />
                <Row label={t("Size")} value={doc.size} testId="qr-f-size" />
                <Row label={t("Color")} value={doc.color} testId="qr-f-color" />
                <Row label={t("Serial Number")} value={serialMissing ? t("Missing — Action Required") : doc.serial_number} mono={!serialMissing} danger={serialMissing} testId="qr-f-serial" />
                <Row label={t("Condition")} value={t(doc.condition || "Good")} testId="qr-f-cond" />
              </div>

              {doc.asset_type === "Road Plate" ? (
                <div className="wp17-panel p-4" data-testid="qr-roadplate-card">
                  <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold mb-1">{t("Road Plate · Specs")}</div>
                  <Row label={t("Length (in)")} value={doc.length_in} mono testId="qr-rp-length" />
                  <Row label={t("Width (in)")} value={doc.width_in} mono testId="qr-rp-width" />
                  <Row label={t("Thickness (in)")} value={doc.thickness_in} mono testId="qr-rp-thickness" />
                  <Row label={t("Material")} value={doc.material} testId="qr-rp-material" />
                  <Row label={t("Rated Capacity (lb)")} value={doc.rated_capacity_lb} mono testId="qr-rp-capacity" />
                  <Row label={t("Anti-Skid Status")} value={doc.anti_skid_status ? t(doc.anti_skid_status) : null} testId="qr-rp-antiskid" />
                  <Row label={t("Markings")} value={doc.markings} testId="qr-rp-markings" />
                </div>
              ) : null}

              <div className="wp17-panel p-4" data-testid="qr-op-card">
                <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold mb-1">{t("Current Use")}</div>
                <Row label={t("Status")} value={t(status)} testId="qr-f-status" />
                <Row label={t("Current Location")} value={doc.current_location} testId="qr-f-loc" />
                <Row label={t("Current Project")} value={doc.current_project_name} testId="qr-f-proj" />
                <Row label={t("Last Inspection")} value={doc.last_inspection_at ? doc.last_inspection_at.slice(0, 10) : null} danger={!doc.last_inspection_at} testId="qr-f-last-insp" />
                <Row label={t("Tabulated Data")} value={doc.tabulated_data_missing ? t("missing") : t("on file")} danger={doc.tabulated_data_missing} testId="qr-f-tabdata" />
              </div>

              <a href="/trench-safety/tabulated-data" className="mt-1 block rounded-2xl bg-cyan-700 hover:bg-cyan-800 text-white text-center py-3 font-bold uppercase tracking-[0.12em] text-sm" data-testid="qr-tabdata-link">
                <BookOpen className="w-4 h-4 inline -mt-0.5 mr-1.5" />
                {t("Open Tabulated Data")}
              </a>

              <a href="/trench-safety/references" className="block rounded-2xl bg-white border-2 border-slate-300 hover:border-cyan-600 text-slate-800 text-center py-3 font-bold uppercase tracking-[0.12em] text-sm" data-testid="qr-references-link">
                <FileWarning className="w-4 h-4 inline -mt-0.5 mr-1.5" />
                {t("Open Safety References")}
              </a>

              <button type="button" onClick={() => setReportOpen(true)} data-testid="qr-report-btn" className="w-full rounded-2xl bg-white border-2 border-amber-400 hover:bg-amber-50 text-amber-900 text-center py-3 font-bold uppercase tracking-[0.12em] text-sm inline-flex items-center justify-center gap-2">
                <AlertTriangle className="w-4 h-4" />
                {t("Report a Problem")}
              </button>

              <div className="wp17-panel p-4 text-xs text-slate-600 leading-relaxed" data-testid="qr-coaching">
                <ShieldAlert className="w-3.5 h-3.5 inline -mt-0.5 mr-1 text-cyan-700" />
                <strong className="text-slate-700">{t("Coaching:")}</strong>{" "}
                {t("Scanning confirms the asset record — it does not move the asset. Location updates when the asset is assigned, transported, or returned. Report damage before the box goes into the trench.")}
              </div>
            </>
          )}
        </div>
      </OperationalPageFrame>

      <PublicReportModal
        open={reportOpen}
        onClose={() => setReportOpen(false)}
        defaultAssetId={doc?.asset_id || assetId || ""}
        lockAssetId={true}
      />
    </>
  );
}