import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ClipboardCheck,
  Users,
  AlertTriangle,
  AlertOctagon,
  ClipboardList,
  Wrench,
  ArrowRight,
  Loader2,
  LogOut,
  Home,
} from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import AutoEmailRoutingPanel from "@/components/AutoEmailRoutingPanel";
import EquipmentStatusBoard from "@/components/EquipmentStatusBoard";
import ComplianceExportPanel from "@/components/ComplianceExportPanel";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { clearAdminToken } from "@/lib/adminAuth";
import { toast } from "sonner";

const AdminTile = ({ to, icon: Icon, title, count, sub, accent = "red", testId }) => {
  const accentCls =
    accent === "red"
      ? "border-red-700 bg-red-700"
      : accent === "amber"
      ? "border-amber-600 bg-amber-600"
      : accent === "redDeep"
      ? "border-red-900 bg-red-900"
      : "border-slate-800 bg-slate-800";
  return (
    <Link
      to={to}
      className="group relative bg-white border-2 border-slate-300 rounded-md p-6 sm:p-7 hover:border-red-700 hover:-translate-y-0.5 transition-all duration-150 flex flex-col"
      data-testid={testId}
    >
      <div
        className={`inline-flex items-center justify-center w-12 h-12 rounded-md ${accentCls} text-white mb-4`}
      >
        <Icon className="w-6 h-6" />
      </div>
      <h3 className="font-display text-xl font-black tracking-tight text-slate-900">
        {title}
      </h3>
      <div className="mt-4 pt-3 border-t-2 border-slate-100 flex items-end justify-between">
        <div>
          <div className="font-display text-3xl font-black text-slate-900 leading-none">
            {count == null ? "—" : count}
          </div>
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-1">
            {sub}
          </div>
        </div>
        <div className="font-mono text-xs uppercase tracking-[0.2em] text-red-700 font-bold flex items-center gap-1 group-hover:gap-2 transition-all">
          Open <ArrowRight className="w-3.5 h-3.5" />
        </div>
      </div>
    </Link>
  );
};

export default function AdminHub() {
  const navigate = useNavigate();
  const [counts, setCounts] = useState({
    inspections: null,
    meetings: null,
    jhas: null,
    incidents: null,
    daily: null,
    equipment: null,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const [insp, mtgs, jhas, incs, daily, eq] = await Promise.all([
          api.get("/inspections").catch(() => ({ data: [] })),
          api.get("/meetings").catch(() => ({ data: [] })),
          api.get("/jhas").catch(() => ({ data: [] })),
          api.get("/incidents").catch(() => ({ data: [] })),
          api.get("/daily-reports").catch(() => ({ data: [] })),
          api.get("/equipment-inspections").catch(() => ({ data: [] })),
        ]);
        if (!alive) return;
        setCounts({
          inspections: insp.data?.length || 0,
          meetings: mtgs.data?.length || 0,
          jhas: jhas.data?.length || 0,
          incidents: incs.data?.length || 0,
          daily: daily.data?.length || 0,
          equipment: eq.data?.length || 0,
        });
      } catch {
        /* noop */
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  const signOut = () => {
    clearAdminToken();
    toast.success("Signed out");
    navigate("/", { replace: true });
  };

  return (
    <div className="min-h-screen blueprint-bg">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Link
              to="/"
              className="inline-flex items-center text-white hover:text-red-300 text-xs font-bold uppercase tracking-wide"
              data-testid="admin-hub-public"
            >
              <Home className="w-4 h-4 mr-1" /> Crew Hub
            </Link>
          </div>
          <MasciLogo variant="lockup" size="lg" className="hidden sm:block" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" />
          <div className="flex items-center gap-2">
            <CompanyInfoDialog />
            <Button
              onClick={signOut}
              variant="outline"
              className="h-9 border-2 border-slate-600 bg-slate-800 text-white hover:border-red-500 hover:text-red-400 text-xs font-bold uppercase tracking-wide"
              data-testid="admin-signout-btn"
            >
              <LogOut className="w-3.5 h-3.5 mr-1" /> Sign out
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-8 sm:py-12">
        <div className="mb-10">
          <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-700">
            MASCI Admin Console
          </span>
          <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tight text-slate-900 mt-2">
            Every record, every form.
          </h1>
          <p className="text-slate-600 text-base mt-3 max-w-2xl">
            View, print, and manage every safety record submitted by the field.
            Crews never see this page.
          </p>
        </div>

        {loading ? (
          <div className="py-16 flex items-center justify-center text-slate-500">
            <Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading…
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5 mb-12">
            <AdminTile
              to="/admin/daily"
              icon={ClipboardList}
              title="Daily Reports"
              count={counts.daily}
              sub={counts.daily === 1 ? "report on file" : "reports on file"}
              accent="red"
              testId="admin-tile-daily"
            />
            <AdminTile
              to="/admin/inspections"
              icon={ClipboardCheck}
              title="Site Inspections"
              count={counts.inspections}
              sub={counts.inspections === 1 ? "report on file" : "reports on file"}
              accent="red"
              testId="admin-tile-inspections"
            />
            <AdminTile
              to="/admin/meetings"
              icon={Users}
              title="Safety Meetings"
              count={counts.meetings}
              sub={counts.meetings === 1 ? "meeting logged" : "meetings logged"}
              accent="slate"
              testId="admin-tile-meetings"
            />
            <AdminTile
              to="/admin/jha"
              icon={AlertTriangle}
              title="Job Hazard Analysis"
              count={counts.jhas}
              sub={counts.jhas === 1 ? "analysis on file" : "analyses on file"}
              accent="amber"
              testId="admin-tile-jha"
            />
            <AdminTile
              to="/admin/incidents"
              icon={AlertOctagon}
              title="Incident Reports"
              count={counts.incidents}
              sub={counts.incidents === 1 ? "report on file" : "reports on file"}
              accent="redDeep"
              testId="admin-tile-incidents"
            />
            <AdminTile
              to="/admin/equipment"
              icon={Wrench}
              title="Equipment Pre-Op"
              count={counts.equipment}
              sub={counts.equipment === 1 ? "inspection on file" : "inspections on file"}
              accent="slate"
              testId="admin-tile-equipment"
            />
          </div>
        )}

        <AutoEmailRoutingPanel />
        <EquipmentStatusBoard />
        <ComplianceExportPanel />
      </main>

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-8 text-center font-mono text-xs uppercase tracking-[0.2em] text-slate-500">
        MASCI · Office Console
      </footer>
    </div>
  );
}
