// HR Portal — main hub. 4 tiles: Field Leadership Records ·
// Employee Accountability · Time Verification · Training Records.
import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { Users, Search, Clock, GraduationCap, LogOut, ShieldCheck } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { clearHrToken, getHrUser } from "@/lib/hrAuth";

const TILES = [
  { to: "/hr/field-leadership", icon: Users, label: "Field Leadership Records",
    desc: "Write-ups · coaching · attendance · recognition · evaluations · terminations · equipment checkout",
    accent: "border-blue-500 bg-blue-50", btn: "bg-blue-700 hover:bg-blue-800" },
  { to: "/hr/employee-accountability", icon: Search, label: "Employee Accountability",
    desc: "Search an employee · all records · outstanding equipment · disciplinary history · clearance for offboarding",
    accent: "border-amber-500 bg-amber-50", btn: "bg-amber-700 hover:bg-amber-800" },
  { to: "/hr/time-verification", icon: Clock, label: "Time Verification",
    desc: "Daily Report labor hours · lunch tracking · payroll cross-check (Exact-ready)",
    accent: "border-emerald-500 bg-emerald-50", btn: "bg-emerald-700 hover:bg-emerald-800" },
  { to: "/hr/training-records", icon: GraduationCap, label: "Training Records",
    desc: "Completed tracks · certifications · training compliance roster",
    accent: "border-purple-500 bg-purple-50", btn: "bg-purple-700 hover:bg-purple-800" },
];

export default function HrHub() {
  const { t } = useT();
  const nav = useNavigate();
  const user = getHrUser();

  const signOut = () => {
    clearHrToken();
    nav("/hr/login");
  };

  return (
    <div className="min-h-screen blueprint-bg pb-16">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-purple-700">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <MasciLogo variant="lockup" size="xl" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
          <div className="flex items-center gap-2">
            <LangToggle />
            <CompanyInfoDialog />
            <Button variant="outline" size="sm" onClick={signOut} className="text-xs" data-testid="hr-sign-out">
              <LogOut className="w-3.5 h-3.5 mr-1" /> {t("Sign out")}
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-8">
        <div className="font-mono text-xs uppercase tracking-[0.2em] text-purple-700">
          <ShieldCheck className="w-3.5 h-3.5 inline mr-1" /> {t("HR Portal")} · {user?.name || ""}
        </div>
        <h1 className="font-display text-3xl sm:text-4xl font-black mt-1">{t("Employee Records & Accountability")}</h1>
        <p className="text-slate-600 mt-2 max-w-2xl">
          {t("Read-only HR access · field leadership records · accountability · payroll-time verification · training compliance.")}
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-8">
          {TILES.map((tile) => (
            <Card key={tile.to} className={`border-2 ${tile.accent} p-5 hover:shadow-md transition-shadow`} data-testid={`hr-tile-${tile.to.split('/').pop()}`}>
              <div className="flex items-start gap-3">
                <tile.icon className="w-6 h-6 mt-1 text-slate-700 shrink-0" />
                <div className="flex-1 min-w-0">
                  <h3 className="font-display text-lg font-black">{t(tile.label)}</h3>
                  <p className="text-sm text-slate-700 mt-1">{t(tile.desc)}</p>
                  <Link to={tile.to} className={`mt-3 inline-flex items-center h-9 px-3 rounded-md ${tile.btn} text-white font-bold uppercase tracking-wide text-xs`}>
                    {t("OPEN →")}
                  </Link>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </main>
    </div>
  );
}
