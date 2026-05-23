// iter353b · Field Leadership Portal · Driver Readiness page.
// iter353d · row click opens FL Accountability Mini-Widget drawer.
import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, HardHat } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { MasciLogo } from "@/components/MasciLogo";
import DriverQualificationReadOnlyView from "@/components/DriverQualificationReadOnlyView";
import FlAccountabilityWidget from "@/components/FlAccountabilityWidget";
import { getFlToken } from "@/lib/flAuth";
import { useT } from "@/lib/i18n";

export default function FieldLeadershipDriverQualification() {
  const { t } = useT();
  const nav = useNavigate();
  const [drawerEmp, setDrawerEmp] = useState(null);
  const authHeaders = () => ({ "X-FL-Token": getFlToken() || "" });

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-slate-900 border-b-4 border-red-700 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={() => nav(-1)} className="text-white hover:bg-white/10" data-testid="fl-dq-back">
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("Back")}
          </Button>
          <Link to="/field-leadership/portal" className="flex items-center gap-2 ml-2">
            <MasciLogo size={26} />
          </Link>
          <div className="ml-2">
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-red-400 font-bold flex items-center gap-1">
              <HardHat className="w-3 h-3" /> {t("Field Leadership · Driver Readiness")}
            </div>
            <div className="text-white text-sm font-display font-black leading-tight">{t("Driver Qualification")}</div>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-5">
        <DriverQualificationReadOnlyView
          endpoint="/field-leadership/portal/driver-qualification"
          authHeaders={authHeaders}
          accent="red"
          testidPrefix="dq-fl"
          onRowClick={(emp) => setDrawerEmp(emp)}
        />
      </main>

      {/* iter353d · accountability mini-widget drawer */}
      <Sheet open={!!drawerEmp} onOpenChange={(v) => !v && setDrawerEmp(null)}>
        <SheetContent side="right" className="w-full sm:max-w-md p-0" data-testid="fl-widget-drawer">
          {drawerEmp ? (
            <div className="p-4 h-full overflow-y-auto">
              <FlAccountabilityWidget employeeId={drawerEmp.id} onClose={() => setDrawerEmp(null)} />
            </div>
          ) : null}
        </SheetContent>
      </Sheet>
    </div>
  );
}
