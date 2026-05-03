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
  TrendingUp,
} from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { JuddGroupAttribution } from "@/components/JuddGroupAttribution";
import { BackendVersionBadge } from "@/components/BackendVersionBadge";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import AutoEmailRoutingPanel from "@/components/AutoEmailRoutingPanel";
import EquipmentStatusBoard from "@/components/EquipmentStatusBoard";
import ComplianceExportPanel from "@/components/ComplianceExportPanel";
import PersistenceHealthBanner from "@/components/PersistenceHealthBanner";
import BackupHeroPanel from "@/components/BackupHeroPanel";
import CrewRecoveryPanel from "@/components/CrewRecoveryPanel";
import SystemHealthBadge from "@/components/SystemHealthBadge";
import TrainingStatsStripe from "@/components/TrainingStatsStripe";
import BilingualAdoptionCard from "@/components/BilingualAdoptionCard";
import AdminJobMasterPanel from "@/components/AdminJobMasterPanel";
import AdminPMPanel from "@/components/AdminPMPanel";
import EquipmentMasterPanel from "@/components/EquipmentMasterPanel";
import EquipmentPartsPanel from "@/components/EquipmentPartsPanel";
import EmployeeMasterPanel from "@/components/EmployeeMasterPanel";
import SupplierMasterPanel from "@/components/SupplierMasterPanel";
import SitePostersPanel from "@/components/SitePostersPanel";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { clearAdminToken } from "@/lib/adminAuth";
import { clearPmToken } from "@/lib/pmAuth";
import { clearShopToken } from "@/lib/shopAuth";
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
    jhaPlans: null,
    trenchBoxes: null,
    incidents: null,
    daily: null,
    equipment: null,
  });
  const [loading, setLoading] = useState(true);

  // Always start at the top of the page after login.
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const [insp, mtgs, jhaPlans, trench, incs, daily, eq] = await Promise.all([
          api.get("/inspections").catch(() => ({ data: [] })),
          api.get("/meetings").catch(() => ({ data: [] })),
          api.get("/job-hazard-plans").catch(() => ({ data: [] })),
          api.get("/trench-boxes").catch(() => ({ data: [] })),
          api.get("/incidents").catch(() => ({ data: [] })),
          api.get("/daily-reports").catch(() => ({ data: [] })),
          api.get("/equipment-inspections").catch(() => ({ data: [] })),
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
    // Wipe every tier on sign-out — shared office iPads / trailer
    // phones must not leak an admin identity to the next user.
    clearAdminToken();
    clearPmToken();
    clearShopToken();
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
              <Home className="w-4 h-4 mr-1" /> MASCI Hub
            </Link>
          </div>
          <MasciLogo variant="lockup" size="lg" className="hidden sm:block" homeLink="/admin" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/admin" />
          <div className="flex items-center gap-2">
            <SystemHealthBadge />
            <Link
              to="/pm"
              className="hidden sm:inline-flex items-center h-9 px-3 rounded-md bg-amber-500 text-slate-900 border-2 border-amber-700 hover:bg-amber-400 text-xs font-bold uppercase tracking-wide"
              data-testid="admin-hub-pm-link"
              title="Open the PM portal as the admin"
            >
              PM Portal
            </Link>
            <Link
              to="/admin/guide"
              className="inline-flex items-center h-9 px-3 rounded-md bg-slate-800 text-white border-2 border-slate-600 hover:border-amber-500 hover:text-amber-300 text-xs font-bold uppercase tracking-wide"
              data-testid="admin-guide-link"
            >
              📖 Guide
            </Link>
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
        {/* ============================================================
            DAY-TO-DAY WORKSPACE — same surface a PM gets in /pm.
            Layout (top → bottom):
              1. Records & Forms tile grid  (the "start screen")
              2. Compliance Export
              3. Active Jobs
              4. Email Routing (PM roster + auto-routing rules)
              5. Site Posters
              6. Equipment Status Board
              7. Equipment Master · Parts · Employees · Suppliers
              8. (admin only) System Recovery — bottom
            ============================================================ */}

        {/* 1 · Records & Forms — start screen */}
        <div className="mb-8">
          <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-700">
            MASCI Admin Console
          </span>
          <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tight text-slate-900 mt-2">
            Records &amp; Forms
          </h1>
          <p className="text-slate-600 text-base mt-3 max-w-2xl">
            Every safety record submitted by the field — view, print, or
            delete. Crews never see this page.
          </p>
        </div>

        {loading ? (
          <div className="py-16 flex items-center justify-center text-slate-500">
            <Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading…
          </div>
        ) : (
          <>
            <TrainingStatsStripe />
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5 mb-10">
            <AdminTile
              to="/admin/pnl"
              icon={TrendingUp}
              title="Project P&L Snapshot"
              count={counts.daily}
              sub="Live job-cost dashboard"
              accent="amber"
              testId="admin-tile-pnl"
            />
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
              to="/admin/jha-plans"
              icon={FileText}
              title="Job Hazard Plans"
              count={counts.jhaPlans}
              sub={counts.jhaPlans === 1 ? "plan uploaded" : "plans uploaded"}
              accent="amber"
              testId="admin-tile-jha-plans"
            />
            <AdminTile
              to="/admin/trench-boxes"
              icon={Box}
              title="Trench Box Data"
              count={counts.trenchBoxes}
              sub={counts.trenchBoxes === 1 ? "box on file" : "boxes on file"}
              accent="slate"
              testId="admin-tile-trench-boxes"
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
          </>
        )}

        {/* 2 · Compliance Export */}
        <ComplianceExportPanel />

        {/* 3 · Active Jobs */}
        <AdminJobMasterPanel />

        {/* 4 · Email Routing (PM roster + auto-routing rules) */}
        <AdminPMPanel />
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

        {/* ============================================================
            SYSTEM RECOVERY — admin-only destructive controls.
            Parked at the bottom of the page on purpose so the PM
            workspace items above stay one-to-one with /pm and admins
            don't trip over backup buttons during normal work.
            ============================================================ */}
        <div className="mt-12 pt-10 border-t-4 border-slate-900">
          <div className="mb-6">
            <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-900">
              Admin Only · System Recovery
            </span>
            <h2 className="font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900 mt-1">
              Backups, restore, and crew recovery
            </h2>
            <p className="text-slate-600 text-sm mt-2 max-w-2xl">
              These controls touch the database directly. They are gated to
              the admin password only and are not available in the Project
              Management portal.
            </p>
          </div>

          {/* Data-loss warning banner — red if running on local Mongo, green if Atlas */}
          <PersistenceHealthBanner />

          {/* Bilingual adoption — per-form EN vs ES filing counts */}
          <BilingualAdoptionCard />

          {/* ONE-STOP backup + restore hero — 2 giant buttons, nothing else */}
          <BackupHeroPanel />

          {/* EMERGENCY: system status grid + force-reseed if data missing after a redeploy */}
          <CrewRecoveryPanel />
        </div>
      </main>

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-8 flex flex-col items-center gap-5 border-t border-slate-200">
        <div className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500">
          MASCI · Office Console
        </div>
        <BackendVersionBadge />
        <JuddGroupAttribution variant="admin" />
      </footer>
    </div>
  );
}
