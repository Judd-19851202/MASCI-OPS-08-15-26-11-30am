// DispatchOperationsMapPage.jsx — Track 15.82 · Dispatch portal map shell.
//
// Wraps the certified `OperationsMapPage` with a calm, Dispatch-themed
// breadcrumb so the page feels like part of Dispatch Portal, NOT the
// Admin Console. We do NOT duplicate map logic — we render the exact
// same canvas, filters, timeline, and asset card sheet.
//
// Why a wrapper instead of mutating OperationsMapPage:
//   • /operations-map (Admin) renders the bare page without breadcrumb —
//     unchanged. Admin RBAC stays intact.
//   • /dispatch-portal/map renders the same page WITH the breadcrumb,
//     scoped to Dispatch. Closes the "context drift" complaint Track
//     15.81 surfaced.
import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Radar } from "lucide-react";
import OperationsMapPage from "@/pages/OperationsMapPage";
import { useT } from "@/lib/i18n";
// TRACK 18.00 · Phase F · Transportation Operations unified branding.
import TransportationOpsTopBar from "@/components/transportation/TransportationOpsTopBar";

export default function DispatchOperationsMapPage() {
  const { t } = useT();
  return (
    <div data-testid="dispatch-operations-map-page" className="flex flex-col min-h-screen">
      <TransportationOpsTopBar />
      {/* Dispatch breadcrumb — sticky, calm, field-readable. */}
      <div
        data-testid="dispatch-map-breadcrumb"
        className="sticky top-0 z-30 flex items-center gap-3 px-4 py-2.5 border-b-2 border-orange-300 bg-orange-50"
      >
        <Link
          to="/dispatch-portal"
          data-testid="dispatch-map-back-to-hub"
          className="inline-flex items-center min-h-[40px] px-3 rounded-md border-2 border-orange-300 hover:border-orange-500 text-orange-800 font-bold tracking-wide text-sm transition-colors"
        >
          <ArrowLeft className="w-4 h-4 mr-1.5" />
          {t("Back to Dispatch Hub")}
        </Link>
        <div className="hidden sm:flex items-center gap-2 text-orange-800">
          <Radar className="w-4 h-4" />
          <span className="font-mono text-[11px] uppercase tracking-[0.22em] font-bold">
            {t("Dispatch · Live Fleet Map")}
          </span>
        </div>
      </div>
      {/* The certified Operations Map canvas — unchanged. */}
      <OperationsMapPage />
    </div>
  );
}
