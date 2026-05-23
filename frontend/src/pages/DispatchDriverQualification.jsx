// iter353b · Dispatch Portal · Approved Drivers / CDL Readiness page.
// Route: /dispatch-portal/driver-qualification
// Read-only view backed by GET /api/dispatch/driver-qualification.
import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, Truck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import DriverQualificationReadOnlyView from "@/components/DriverQualificationReadOnlyView";
import { getDispatchToken } from "@/lib/dispatchAuth";
import { useT } from "@/lib/i18n";

export default function DispatchDriverQualification() {
  const { t } = useT();
  const nav = useNavigate();
  const authHeaders = () => ({ "X-Dispatch-Token": getDispatchToken() || "" });

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-slate-900 border-b-4 border-orange-500 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={() => nav(-1)} className="text-white hover:bg-white/10" data-testid="dispatch-dq-back">
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("Back")}
          </Button>
          <Link to="/dispatch-portal" className="flex items-center gap-2 ml-2">
            <MasciLogo size={26} />
          </Link>
          <div className="ml-2">
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-orange-400 font-bold flex items-center gap-1">
              <Truck className="w-3 h-3" /> {t("Dispatch · Approved Drivers / CDL Readiness")}
            </div>
            <div className="text-white text-sm font-display font-black leading-tight">{t("Driver Qualification")}</div>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-5">
        <DriverQualificationReadOnlyView
          endpoint="/dispatch/driver-qualification"
          authHeaders={authHeaders}
          accent="orange"
          testidPrefix="dq-disp"
        />
      </main>
    </div>
  );
}
