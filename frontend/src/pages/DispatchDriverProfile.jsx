// DCP-1 · Driver Command Profile · Dispatch view.
// Dispatch only sees identity / operations / equipment per role redactor.
import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import DriverCommandProfile from "@/components/DriverCommandProfile";
import { usePageTitle } from "@/lib/usePageTitle";

export default function DispatchDriverProfile() {
  const { driverKey } = useParams();
  const nav = useNavigate();
  usePageTitle("Driver Command Profile · Dispatch · MASCI");
  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-5xl mx-auto px-4 py-6" data-testid="dispatch-driver-profile-page">
        <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
          <div className="flex items-center gap-3">
            <MasciLogo size="sm" />
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-indigo-700 font-bold">DISPATCH · DRIVER</div>
              <h1 className="font-display text-2xl font-black tracking-tight text-slate-900">Driver Command Profile</h1>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={() => nav(-1)} data-testid="dispatch-driver-profile-back">
            <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Back
          </Button>
        </div>
        <DriverCommandProfile driverKey={driverKey} />
      </div>
    </div>
  );
}
