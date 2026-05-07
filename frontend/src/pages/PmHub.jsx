import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ClipboardCheck,
  Users,
  AlertOctagon,
  ClipboardList,
  Wrench,
  Box,
  FileText,
  ArrowRight,
  Loader2,
  LogOut,
  Home,
  Briefcase,
  ShieldCheck,
  Image as ImageIcon,
} from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { ForgedOpsAttribution } from "@/components/ForgedOpsAttribution";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import AutoEmailRoutingPanel from "@/components/AutoEmailRoutingPanel";
import EquipmentStatusBoard from "@/components/EquipmentStatusBoard";
import ComplianceExportPanel from "@/components/ComplianceExportPanel";
import SystemHealthBadge from "@/components/SystemHealthBadge";
import AdminJobMasterPanel from "@/components/AdminJobMasterPanel";
// AdminPMPanel intentionally NOT imported here — PM roster is admin-only as of 2026-05-05.
import EquipmentMasterPanel from "@/components/EquipmentMasterPanel";
import EquipmentPartsPanel from "@/components/EquipmentPartsPanel";
import EmployeeMasterPanel from "@/components/EmployeeMasterPanel";
import SupplierMasterPanel from "@/components/SupplierMasterPanel";
import TrainingStatsStripe from "@/components/TrainingStatsStripe";
import SitePostersPanel from "@/components/SitePostersPanel";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { clearPmToken } from "@/lib/pmAuth";
import { clearAdminToken } from "@/lib/adminAuth";
import { clearShopToken } from "@/lib/shopAuth";
import { toast } from "sonner";

const PmTile = ({ to, icon: Icon, title, count, sub, accent = "amber", testId }) => {
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
      className="group relative bg-white border-2 border-slate-300 rounded-md p-6 sm:p-7 hover:border-amber-600 hover:-translate-y-0.5 transition-all duration-150 flex flex-col"
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
        <div className="font-mono text-xs uppercase tracking-[0.2em] text-amber-700 font-bold flex items-center gap-1 group-hover:gap-2 transition-all">
          Open <ArrowRight className="w-3.5 h-3.5" />
        </div>
      </div>
    </Link>
  );
};

export default function PmHub() {
  const navigate = useNavigate();
  const [counts, setCounts] = useState({
    inspections: null,
    meetings: null,
    jhaPlans: null,
    trenchBoxes: null,
    incidents: null,
    daily: null,
    equipment: null,
    qaqc: null,
  });
  const [loading, setLoading] = useState(true);

  // Always start at the top of the page after login, regardless of any
  // scroll position React Router may have preserved from the login screen.
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const [insp, mtgs, jhaPlans, trench, incs, daily, eq, qaqc] = await Promise.all([
          api.get("/inspections").catch(() => ({ data: [] })),
          api.get("/meetings").catch(() => ({ data: [] })),
          api.get("/job-hazard-plans").catch(() => ({ data: [] })),
          api.get("/trench-boxes").catch(() => ({ data: [] })),
          api.get("/incidents").catch(() => ({ data: [] })),
          api.get("/daily-reports").catch(() => ({ data: [] })),
          api.get("/equipment-inspections").catch(() => ({ data: [] })),
          api.get("/qaqc-inspections").catch(() => ({ data: [] })),
        ]);
        if (!alive) return;
        setCounts({
          inspections: insp.data?.length || 0,
          meetings: mtgs.data?.length || 0,
          jhaPlans: jhaPlans.data?.length || 0,
          trenchBoxes: trench.data?.length || 0,
          incidents: incs.data?.length || 0,
          daily: daily.data?.length || 0,
          equipment: eq.data?.length || 0,
          qaqc: qaqc.data?.length || 0,
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
    // Wipe every tier on sign-out so a shared device can't leak an
    // identity to the next user.
    clearPmToken();
    clearAdminToken();
    clearShopToken();
    toast.success("Signed out");
    navigate("/", { replace: true });
  };

  return (
    <div className="min-h-screen blueprint-bg">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-amber-500">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Link
              to="/"
              className="inline-flex items-center text-white hover:text-amber-300 text-xs font-bold uppercase tracking-wide"
              data-testid="pm-hub-public"
            >
              <Home className="w-4 h-4 mr-1" /> MASCI Hub
            </Link>
          </div>
          <MasciLogo variant="lockup" size="lg" className="hidden sm:block" homeLink="/pm" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/pm" />
          <div className="flex items-center gap-2">
            <SystemHealthBadge />
            <CompanyInfoDialog />
            <Button
              onClick={signOut}
              variant="outline"
              className="h-9 border-2 border-slate-600 bg-slate-800 text-white hover:border-amber-500 hover:text-amber-300 text-xs font-bold uppercase tracking-wide"
              data-testid="pm-signout-btn"
            >
              <LogOut className="w-3.5 h-3.5 mr-1" /> Sign out
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-8 sm:py-12">
        {/* Banner — make it visually obvious this is the PM portal */}
        <div
          className="bg-amber-50 border-2 border-amber-400 rounded-md p-4 sm:p-5 mb-8 flex items-start gap-3"
          data-testid="pm-portal-banner"
        >
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-amber-500 text-white shrink-0">
            <Briefcase className="w-5 h-5" />
          </div>
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-amber-800 font-black">
              Project Management Portal
            </div>
            <h1 className="font-display text-2xl sm:text-3xl font-black text-slate-900 leading-tight mt-0.5">
              Records &amp; Forms — every job in one place.
            </h1>
            <p className="text-slate-700 text-sm mt-1.5">
              Same workspace as Admin for the day-to-day office work.
              System-recovery tools live in the Admin Console only.
            </p>
          </div>
        </div>

        {/* 1 · Records & Forms — start screen */}
        {loading ? (
          <div className="py-16 flex items-center justify-center text-slate-500">
            <Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading…
          </div>
        ) : (
          <>
            <TrainingStatsStripe />
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5 mb-10">
            <PmTile
              to="/pm/daily"
              icon={ClipboardList}
              title="Daily Reports"
              count={counts.daily}
              sub={counts.daily === 1 ? "report on file" : "reports on file"}
              accent="red"
              testId="pm-tile-daily"
            />
            <PmTile
              to="/pm/inspections"
              icon={ClipboardCheck}
              title="Site Inspections"
              count={counts.inspections}
              sub={counts.inspections === 1 ? "report on file" : "reports on file"}
              accent="red"
              testId="pm-tile-inspections"
            />
            <PmTile
              to="/pm/meetings"
              icon={Users}
              title="Safety Meetings"
              count={counts.meetings}
              sub={counts.meetings === 1 ? "meeting logged" : "meetings logged"}
              accent="slate"
              testId="pm-tile-meetings"
            />
            <PmTile
              to="/pm/jha-plans"
              icon={FileText}
              title="Job Hazard Plans"
              count={counts.jhaPlans}
              sub={counts.jhaPlans === 1 ? "plan uploaded" : "plans uploaded"}
              accent="amber"
              testId="pm-tile-jha-plans"
            />
            <PmTile
              to="/pm/trench-boxes"
              icon={Box}
              title="Trench Box Data"
              count={counts.trenchBoxes}
              sub={counts.trenchBoxes === 1 ? "box on file" : "boxes on file"}
              accent="slate"
              testId="pm-tile-trench-boxes"
            />
            <PmTile
              to="/pm/incidents"
              icon={AlertOctagon}
              title="Incident Reports"
              count={counts.incidents}
              sub={counts.incidents === 1 ? "report on file" : "reports on file"}
              accent="redDeep"
              testId="pm-tile-incidents"
            />
            <PmTile
              to="/pm/equipment"
              icon={Wrench}
              title="Equipment Pre-Op"
              count={counts.equipment}
              sub={counts.equipment === 1 ? "inspection on file" : "inspections on file"}
              accent="slate"
              testId="pm-tile-equipment"
            />
            <PmTile
              to="/pm/qaqc"
              icon={ShieldCheck}
              title="QA / QC Inspections"
              count={counts.qaqc}
              sub="Records on your jobs"
              accent="amber"
              testId="pm-tile-qaqc"
            />
            <PmTile
              to="/pm/photos"
              icon={ImageIcon}
              title="Job Photos"
              count={null}
              sub="All photos by job & week"
              accent="rose"
              testId="pm-tile-photos"
            />
            </div>
          </>
        )}

        {/* 2 · Compliance Export — PM portal NEVER sees backup tools, even
            if an admin token is also present in localStorage. */}
        <ComplianceExportPanel hideBackupTools />

        {/* 3 · Active Jobs */}
        <AdminJobMasterPanel />

        {/* 4 · Email Routing — Project Manager roster is admin-only as of
            2026-05-05. PMs no longer see/edit each other's accounts; the
            auto-routing summary stays so a PM can sanity-check who an
            email goes to. */}
        <AutoEmailRoutingPanel />

        {/* 5 · Site Posters */}
        <SitePostersPanel />

        {/* 6 · Equipment Status Board */}
        <EquipmentStatusBoard />

        {/* 7 · Master Lists — equipment fleet, parts, employees, suppliers */}
        <EquipmentMasterPanel />
        <EquipmentPartsPanel />
        <EmployeeMasterPanel />
        <SupplierMasterPanel />
      </main>

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-8 flex flex-col items-center gap-5 border-t border-slate-200">
        <div className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500">
          MASCI · Project Management Portal
        </div>
        <ForgedOpsAttribution variant="admin" />
      </footer>
    </div>
  );
}
