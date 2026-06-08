// HrMotiveDrivers.jsx — MCC-1 HR Access Extension
// Mounts the existing MappingCleanupTab inside the HR portal in HR scope.
// Reuses the component fully — HR mode hides conflict resolution and
// makes the asset queue view-only.  Backend enforces the same matrix.
import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, Home, Truck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { usePageTitle } from "@/lib/usePageTitle";
import MappingCleanupTab from "@/components/admin/MappingCleanupTab";

export default function HrMotiveDrivers() {
  const nav = useNavigate();
  usePageTitle("Motive Driver Cleanup · HR · MASCI");
  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex items-center justify-between gap-3 mb-5 flex-wrap">
          <div className="flex items-center gap-3">
            <MasciLogo size="sm" />
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-emerald-700 font-bold">
                HR Portal · Motive
              </div>
              <h1 className="font-display text-2xl font-black tracking-tight text-slate-900">
                Driver Cleanup
              </h1>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => nav("/hr")}
              data-testid="hr-motive-drivers-back"
            >
              <ArrowLeft className="w-3.5 h-3.5 mr-1" /> HR Hub
            </Button>
            <Link to="/hr" className="hidden sm:inline-flex items-center text-xs font-mono uppercase tracking-wider text-slate-500 hover:text-slate-800">
              <Home className="w-3.5 h-3.5 mr-1" /> Home
            </Link>
          </div>
        </div>

        <MappingCleanupTab mode="hr" />
      </div>
    </div>
  );
}
