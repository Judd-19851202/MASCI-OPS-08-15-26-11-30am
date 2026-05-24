/**
 * AdminDlsShiftQR.jsx · iter406 · Phase 14 · QR Shift Start Generator.
 *
 * Route: /admin/dls/shift-qr  (admin token gated)
 *
 * Doctrine
 * --------
 * Physical operational deployment. NOT an admin management system.
 *   - One short form (4 optional inputs)
 *   - One big QR code pointing to the public `/shift` URL
 *   - One print button → browser PDF
 *   - Truck cab sticker workflow: generate, print, peel, stick.
 *
 * Restraint
 * ---------
 *   - 0 new collections, 0 new endpoints.
 *   - QR is rendered fully client-side with `qrcode.react` (already a dep).
 *   - URL is composed from `window.location.origin` so preview / prod
 *     produce the right link without env coupling.
 *   - No tracking, no per-card audit log, no "QR management" surface —
 *     this is a printer, not a system.
 */
import React, { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Printer, QrCode, ExternalLink } from "lucide-react";
import { QRCodeSVG } from "qrcode.react";
import AdminShell from "@/components/AdminShell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LifecycleGuide } from "@/components/LifecycleGuide";
import { usePageTitle } from "@/lib/usePageTitle";
import { useT } from "@/lib/i18n";

export default function AdminDlsShiftQR() {
  usePageTitle("Shift Start QR · Dispatch · MASCI");
  const { t } = useT();

  // Optional labels printed on the card. These don't change the QR
  // target — they just help operations know which sticker goes where.
  const [truckLabel, setTruckLabel] = useState("");
  const [carrierLabel, setCarrierLabel] = useState("MASCI");
  const [tenant, setTenant] = useState("");

  // QR target — always the public shift entry. Tenant param is purely
  // a dev/multi-tenant convenience; the default flow uses no param.
  const shiftUrl = useMemo(() => {
    const origin = (typeof window !== "undefined" && window.location.origin) || "";
    if (tenant && tenant.trim()) {
      return `${origin}/shift?tenant=${encodeURIComponent(tenant.trim())}`;
    }
    return `${origin}/shift`;
  }, [tenant]);

  return (
    <AdminShell title="Shift Start QR">
      <div className="max-w-5xl mx-auto" data-testid="admin-dls-shift-qr">
        {/* Header card — calm, slate, matches platform tone */}
        <div className="bg-white border border-slate-200 border-l-4 border-l-orange-500 rounded-md p-5 mb-5 no-print">
          <div className="flex items-start gap-3">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-slate-900 text-white shrink-0">
              <QrCode className="w-6 h-6" />
            </div>
            <div className="flex-1">
              <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-orange-700 font-bold">
                {t("Dispatch Lifecycle System")} · {t("Physical Deployment")}
              </span>
              <h1 className="font-display text-2xl font-black tracking-tight mt-0.5">
                {t("Shift Start QR Generator")}
              </h1>
              <p className="text-sm text-slate-600 mt-1 max-w-2xl">
                {t("Print a QR sticker for the truck cab. Drivers scan, land on the public shift entry, pick their identity and start the shift. No password, no app install.")}
              </p>
            </div>
            <Link
              to="/dispatch-portal/board"
              className="text-xs font-bold uppercase tracking-wide text-slate-700 hover:text-orange-700 inline-flex items-center gap-1"
              data-testid="shiftqr-back-to-board"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              {t("Operational Board")}
            </Link>
          </div>
        </div>

        {/* iter406 · Coaching · LifecycleGuide — keeps the utility platform-native */}
        <div className="no-print mb-5">
          <LifecycleGuide
            id="dls-shift-qr-guide"
            icon={QrCode}
            title={t("How operations uses this")}
            summary={t("One QR per truck cab · scan · start shift · operate lifecycle")}
            accent="orange"
            sections={[
              {
                label: t("Print"),
                body: t("Fill the optional truck and carrier labels so operations can tell stickers apart. Tap Print, then choose 'Save as PDF' or send to your printer."),
              },
              {
                label: t("Place"),
                body: t("Stick the printed card on the inside of the driver's door, the visor, or the dash. Anywhere the driver can reach with their phone camera before they roll."),
              },
              {
                label: t("Scan"),
                body: t("The driver opens their phone camera, points at the QR, taps the link. They land on the public shift entry and pick their identity from the platform's existing records — no enrollment, no app install."),
              },
              {
                label: t("Restraint"),
                body: t("The QR is not tracked. There is no per-card audit log. This screen is a printer, not a system. If a sticker is damaged, print a new one — the QR target is the same public URL for every truck."),
              },
            ]}
          />
        </div>

        {/* Form + Preview side-by-side on desktop; stacked on mobile */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Inputs */}
          <div className="bg-white border border-slate-200 rounded-md p-5 no-print" data-testid="shiftqr-form">
            <h2 className="font-display text-lg font-black text-slate-900 mb-3">
              {t("Card details")}
            </h2>
            <div className="space-y-4">
              <div>
                <Label htmlFor="shiftqr-truck" className="text-xs uppercase tracking-widest text-slate-700 font-bold">
                  {t("Truck label")} <span className="text-slate-400 normal-case font-normal">({t("optional")})</span>
                </Label>
                <Input
                  id="shiftqr-truck"
                  data-testid="shiftqr-truck-input"
                  value={truckLabel}
                  onChange={(e) => setTruckLabel(e.target.value)}
                  placeholder={t("e.g. T-21")}
                  className="mt-1.5 min-h-[44px]"
                  maxLength={32}
                />
                <p className="text-xs text-slate-500 mt-1">
                  {t("Printed at the top of the card so operations knows which truck this sticker belongs to.")}
                </p>
              </div>

              <div>
                <Label htmlFor="shiftqr-carrier" className="text-xs uppercase tracking-widest text-slate-700 font-bold">
                  {t("Carrier")} <span className="text-slate-400 normal-case font-normal">({t("optional")})</span>
                </Label>
                <Input
                  id="shiftqr-carrier"
                  data-testid="shiftqr-carrier-input"
                  value={carrierLabel}
                  onChange={(e) => setCarrierLabel(e.target.value)}
                  placeholder="MASCI"
                  className="mt-1.5 min-h-[44px]"
                  maxLength={48}
                />
                <p className="text-xs text-slate-500 mt-1">
                  {t("Useful when printing sticker packs for subhauler fleets.")}
                </p>
              </div>

              <div>
                <Label htmlFor="shiftqr-tenant" className="text-xs uppercase tracking-widest text-slate-700 font-bold">
                  {t("Tenant")} <span className="text-slate-400 normal-case font-normal">({t("dev only")})</span>
                </Label>
                <Input
                  id="shiftqr-tenant"
                  data-testid="shiftqr-tenant-input"
                  value={tenant}
                  onChange={(e) => setTenant(e.target.value)}
                  placeholder={t("Leave blank for production")}
                  className="mt-1.5 min-h-[44px]"
                  maxLength={48}
                />
                <p className="text-xs text-slate-500 mt-1">
                  {t("Only set this when generating stickers for a non-default tenant (dev or pilot).")}
                </p>
              </div>

              <div className="pt-2 flex flex-wrap gap-3">
                <Button
                  onClick={() => window.print()}
                  data-testid="shiftqr-print-btn"
                  className="bg-slate-900 hover:bg-slate-800 text-white min-h-[48px] px-5"
                >
                  <Printer className="w-4 h-4 mr-2" />
                  {t("Print card")}
                </Button>
                <a
                  href={shiftUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center min-h-[48px] px-4 text-sm font-bold text-slate-700 hover:text-orange-700"
                  data-testid="shiftqr-open-link"
                >
                  <ExternalLink className="w-4 h-4 mr-1.5" />
                  {t("Open shift URL")}
                </a>
              </div>
              <p className="text-[11px] text-slate-500 break-all" data-testid="shiftqr-url-readout">
                {shiftUrl}
              </p>
            </div>
          </div>

          {/* Printable card preview */}
          <div className="flex items-start justify-center">
            <ShiftQrCard
              shiftUrl={shiftUrl}
              truckLabel={truckLabel}
              carrierLabel={carrierLabel}
              t={t}
            />
          </div>
        </div>
      </div>

      {/* Print-friendly CSS — hides everything except the card on print. */}
      <style>{`
        @media print {
          .no-print { display: none !important; }
          .shiftqr-card {
            page-break-inside: avoid;
            box-shadow: none !important;
            border: 1px solid #0f172a !important;
            margin: 0 auto;
          }
          body { background: white !important; }
        }
      `}</style>
    </AdminShell>
  );
}

// ─────────────────────────────────────────────────────────────────────
// Printable card · 4.25 × 5.5 in style (half-letter portrait)
// ─────────────────────────────────────────────────────────────────────
function ShiftQrCard({ shiftUrl, truckLabel, carrierLabel, t }) {
  return (
    <div
      data-testid="shiftqr-card"
      className="shiftqr-card bg-white border-2 border-slate-900 rounded-md p-6 w-[340px] shadow-md"
    >
      {/* Header band */}
      <div className="border-b-2 border-slate-900 pb-3 mb-4">
        <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-orange-700 font-black">
          {carrierLabel || "MASCI"} · {t("DRIVER SHIFT START")}
        </div>
        {truckLabel ? (
          <div
            className="font-display text-3xl font-black text-slate-900 leading-none mt-1.5"
            data-testid="shiftqr-card-truck"
          >
            {truckLabel}
          </div>
        ) : (
          <div className="font-display text-2xl font-black text-slate-900 leading-none mt-1.5">
            {t("Truck cab")}
          </div>
        )}
      </div>

      {/* QR */}
      <div className="flex justify-center" data-testid="shiftqr-card-qr-wrap">
        <div className="bg-white p-2 border border-slate-200 rounded">
          <QRCodeSVG
            value={shiftUrl}
            size={220}
            level="M"
            includeMargin={false}
            data-testid="shiftqr-card-qr"
          />
        </div>
      </div>

      {/* Instructions — bilingual on the printed card */}
      <div className="mt-4 text-center space-y-1">
        <div className="font-bold text-sm text-slate-900">
          {t("Scan to start your shift")}
        </div>
        <div className="text-xs text-slate-700">
          {t("Open camera · point at QR · tap link")}
        </div>
        <div className="text-[11px] text-slate-500 italic">
          Escanea para iniciar tu turno · abre la cámara y toca el enlace
        </div>
      </div>

      {/* Footer */}
      <div className="mt-4 pt-3 border-t border-slate-300 text-center">
        <div className="font-mono text-[9px] uppercase tracking-[0.25em] text-slate-500">
          {t("No password · No app · Just tap")}
        </div>
      </div>
    </div>
  );
}
