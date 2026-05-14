// HR Portal — main hub. 4 tiles: Field Leadership Records ·
// Employee Accountability · Time Verification · Training Records.
import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { Users, Search, Clock, GraduationCap, LogOut, ShieldCheck, Calculator, CalendarOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { LangToggle } from "@/components/LangToggle";
import PortalSwitcher from "@/components/PortalSwitcher";
import { useT } from "@/lib/i18n";
import { clearHrToken, getHrUser, getHrToken } from "@/lib/hrAuth";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const TILES = [
  { to: "/hr/field-leadership", icon: Users, label: "Field Leadership Records",
    desc: "Write-ups · coaching · attendance · recognition · evaluations · terminations · equipment checkout",
    accent: "border-blue-500 bg-blue-50", btn: "bg-blue-700 hover:bg-blue-800" },
  { to: "/hr/time-off", icon: CalendarOff, label: "Time Off Requests",
    desc: "Vacation · Sick · Medical · Family Emergency · Bereavement · approve, deny, or request more info · send public form to office staff",
    accent: "border-cyan-500 bg-cyan-50", btn: "bg-cyan-700 hover:bg-cyan-800",
    badgeKey: "pending" },
  { to: "/hr/employee-accountability", icon: Search, label: "Employee Accountability",
    desc: "Search an employee · all records · outstanding equipment · disciplinary history · clearance for offboarding",
    accent: "border-amber-500 bg-amber-50", btn: "bg-amber-700 hover:bg-amber-800" },
  { to: "/hr/time-verification", icon: Clock, label: "Time Verification",
    desc: "Daily Report labor hours · lunch tracking · payroll cross-check (Exact-ready)",
    accent: "border-emerald-500 bg-emerald-50", btn: "bg-emerald-700 hover:bg-emerald-800" },
  { to: "/hr/payroll-variance", icon: Calculator, label: "Payroll Variance",
    desc: "Paste Exact payroll CSV · auto-match to MASCI hours · approve / dispute each variance · weekly email summary",
    accent: "border-red-500 bg-red-50", btn: "bg-red-700 hover:bg-red-800" },
  { to: "/hr/training-records", icon: GraduationCap, label: "Training Records",
    desc: "Completed tracks · certifications · training compliance roster",
    accent: "border-purple-500 bg-purple-50", btn: "bg-purple-700 hover:bg-purple-800" },
  { to: "/hr/safety-records", icon: ShieldCheck, label: "Safety Records",
    desc: "Read-only · safety document library (OSHA, SDS, EAPs) and per-employee training & certifications maintained by Safety",
    accent: "border-cyan-700 bg-cyan-50", btn: "bg-cyan-700 hover:bg-cyan-800" },
];

export default function HrHub() {
  const { t } = useT();
  const nav = useNavigate();
  const user = getHrUser();
  const [stats, setStats] = React.useState({});

  React.useEffect(() => {
    (async () => {
      try {
        const tok = getHrToken();
        if (!tok) return;
        const r = await fetch(`${API}/field-leadership/time-off/stats`, {
          headers: { "X-HR-Token": tok },
        });
        if (r.ok) setStats(await r.json());
      } catch (e) { /* silent */ }
    })();
  }, []);

  const signOut = () => {
    clearHrToken();
    nav("/hr/login");
  };

  return (
    <div className="min-h-screen blueprint-bg pb-16">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-purple-700">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <MasciLogo variant="mark" size="xl" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
          <div className="flex items-center gap-2">
            <PortalSwitcher current="hr" />
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
          {TILES.map((tile) => {
            const badge = tile.badgeKey ? stats[tile.badgeKey] : 0;
            return (
              <Link
                key={tile.to}
                to={tile.to}
                className={`block rounded-lg border-2 ${tile.accent} p-5 hover:shadow-md hover:-translate-y-0.5 transition-all duration-150 relative`}
                data-testid={`hr-tile-${tile.to.split('/').pop()}`}
              >
                {badge > 0 && (
                  <span
                    className="absolute top-3 right-3 inline-flex items-center justify-center min-w-[28px] h-7 px-2 rounded-full bg-red-600 text-white text-xs font-black border-2 border-white shadow"
                    data-testid={`hr-tile-badge-${tile.to.split('/').pop()}`}
                  >
                    {badge}
                  </span>
                )}
                <div className="flex items-start gap-3">
                  <tile.icon className="w-6 h-6 mt-1 text-slate-700 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <h3 className="font-display text-lg font-black">{t(tile.label)}</h3>
                    <p className="text-sm text-slate-700 mt-1">{t(tile.desc)}</p>
                    <span className={`mt-3 inline-flex items-center h-9 px-3 rounded-md ${tile.btn} text-white font-bold uppercase tracking-wide text-xs`}>
                      {t("OPEN →")}
                    </span>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      </main>
    </div>
  );
}
