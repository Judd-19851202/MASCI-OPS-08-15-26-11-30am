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
  Building2,
  TrendingUp,
  ShieldCheck,
  Image as ImageIcon,
  UserCheck,
} from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { ForgedOpsAttribution } from "@/components/ForgedOpsAttribution";
import { BackendVersionBadge } from "@/components/BackendVersionBadge";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import AutoEmailRoutingPanel from "@/components/AutoEmailRoutingPanel";
import EquipmentStatusBoard from "@/components/EquipmentStatusBoard";
import ComplianceExportPanel from "@/components/ComplianceExportPanel";
import PersistenceHealthBanner from "@/components/PersistenceHealthBanner";
import BackupHeroPanel from "@/components/BackupHeroPanel";
import StoredBackupsPanel from "@/components/StoredBackupsPanel";
import RestoreBackupPanel from "@/components/RestoreBackupPanel";
import CrewRecoveryPanel from "@/components/CrewRecoveryPanel";
import SystemHealthBadge from "@/components/SystemHealthBadge";
import TrainingStatsStripe from "@/components/TrainingStatsStripe";
import BilingualAdoptionCard from "@/components/BilingualAdoptionCard";
import CalculatorUsageCard from "@/components/CalculatorUsageCard";
import AdminJobMasterPanel from "@/components/AdminJobMasterPanel";
import AdminPMPanel from "@/components/AdminPMPanel";
import AdminShopUsersPanel from "@/components/AdminShopUsersPanel";
import EquipmentMasterPanel from "@/components/EquipmentMasterPanel";
import EquipmentPartsPanel from "@/components/EquipmentPartsPanel";
import EmployeeMasterPanel from "@/components/EmployeeMasterPanel";
import SupplierMasterPanel from "@/components/SupplierMasterPanel";
import SitePostersPanel from "@/components/SitePostersPanel";
import AdminTrainingResourcesPanel from "@/components/AdminTrainingResourcesPanel";
import AdminSafetyFormsPanel from "@/components/AdminSafetyFormsPanel";
import DateAuditPanel from "@/components/DateAuditPanel";
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
    qaqc: null,
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
        <div className="max-w-6xl mx-auto px-3 sm:px-8 py-4 flex items-center justify-between gap-2 sm:gap-3 flex-wrap">
          <div className="flex items-center gap-3">
            <Link
              to="/"
              className="inline-flex items-center text-white hover:text-red-300 text-xs font-bold uppercase tracking-wide"
              data-testid="admin-hub-public"
            >
              <Home className="w-4 h-4 mr-1" /> <span className="hidden xs:inline">MASCI</span> Hub
            </Link>
          </div>
          <MasciLogo variant="lockup" size="lg" className="hidden sm:block" homeLink="/admin" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/admin" />
          <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap justify-end">
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
              className="inline-flex items-center h-9 px-2 sm:px-3 rounded-md bg-slate-800 text-white border-2 border-slate-600 hover:border-amber-500 hover:text-amber-300 text-xs font-bold uppercase tracking-wide"
              data-testid="admin-guide-link"
              title="Admin guide"
            >
              <span className="sm:hidden">📖</span>
              <span className="hidden sm:inline">📖 Guide</span>
            </Link>
            <CompanyInfoDialog
              trigger={
                <Button
                  variant="outline"
                  className="h-9 px-2 sm:px-3 border-2 border-slate-600 bg-slate-800 text-white hover:border-amber-500 hover:text-amber-300 text-xs font-bold uppercase tracking-wide"
                  data-testid="admin-company-info-btn"
                  title="Company Info"
                >
                  <Building2 className="w-3.5 h-3.5 sm:mr-1" />
                  <span className="hidden sm:inline">Info</span>
                </Button>
              }
            />
            <Button
              onClick={signOut}
              variant="outline"
              className="h-9 px-2 sm:px-3 border-2 border-slate-600 bg-slate-800 text-white hover:border-red-500 hover:text-red-400 text-xs font-bold uppercase tracking-wide"
              data-testid="admin-signout-btn"
              title="Sign out"
            >
              <LogOut className="w-3.5 h-3.5 sm:mr-1" />
              <span className="hidden sm:inline">Sign out</span>
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
            <AdminTile
              to="/admin/qaqc"
              icon={ShieldCheck}
              title="QA / QC Inspections"
              count={counts.qaqc}
              sub={counts.qaqc === 1 ? "record on file" : "records on file"}
              accent="amber"
              testId="admin-tile-qaqc"
            />
            <AdminTile
              to="/admin/photos"
              icon={ImageIcon}
              title="Job Photos"
              count={null}
              sub="All photos by job & week"
              accent="rose"
              testId="admin-tile-photos"
            />
            <AdminTile
              to="/leadership/records"
              icon={UserCheck}
              title="Field Leadership"
              count={null}
              sub="Write-ups · Coaching · Recognition"
              accent="indigo"
              testId="admin-tile-leadership"
            />
            </div>
          </>
        )}

        {/* 2 · Compliance Export — backup/restore tools relocated to bottom System Recovery section */}
        <ComplianceExportPanel hideBackupTools />

        {/* 3 · Active Jobs */}
        <AdminJobMasterPanel />

        {/* 4 · Email Routing (PM roster + auto-routing rules) */}
        <AdminPMPanel />
        <AdminShopUsersPanel />
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

        {/* 7b · Field Leadership — Equipment Catalog + Manufacturers */}
        <div className="border-2 border-slate-300 rounded-md p-5 bg-white">
          <div className="flex items-start justify-between gap-3">
            <div>
              <span className="font-mono text-xs uppercase tracking-[0.2em] text-red-700 font-bold">
                Field Leadership
              </span>
              <h3 className="font-display text-xl sm:text-2xl font-black mt-1">
                Equipment Catalog & Manufacturers
              </h3>
              <p className="text-sm text-slate-600 mt-1 max-w-xl">
                Manage the searchable equipment list and manufacturer dropdown used by the
                Equipment Checkout & Accountability form. Edit replacement values, disable
                old items, and export the full checkout history.
              </p>
            </div>
            <Link
              to="/admin/leadership-equipment"
              className="inline-flex items-center h-10 px-4 rounded-md bg-blue-700 hover:bg-blue-800 text-white font-bold uppercase tracking-wide text-xs"
              data-testid="admin-leadership-equipment-link"
            >
              Open
            </Link>
          </div>
        </div>

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

          {/* Material Calculator usage — per-calculator run counts + CSV export */}
          <CalculatorUsageCard />

          {/* Internal training packets + QR posters (Shop / PM / Admin) — relocated from public Training Hub */}
          <AdminTrainingResourcesPanel />

          {/* Safety Forms (Equipment Issuance + Use & Care Training) */}
          <AdminSafetyFormsPanel />

          {/* One-shot timezone-bug sweep (added 2026-05-05) */}
          <DateAuditPanel />

          {/* ============================================================
              BACKUP & RESTORE — every backup/recovery tool lives below
              this header, in order of escalating risk:
                1. Backup Hero    (safe — make + email + download .zip)
                2. Stored Backups (server-side library; delete is gated)
                3. Restore        (merge=safe; replace=wipes, gated)
                4. System Recovery (force re-seed; wipes, gated)
              Every destructive button (delete, replace, force re-seed)
              prompts an "Are you sure?" + admin-password re-entry before
              running. Live counts up top via PersistenceHealthBanner.
              ============================================================ */}
          <div className="mt-10 mb-4 pb-3 border-b-2 border-slate-300">
            <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-900">
              Backup &amp; Restore Tools
            </span>
            <h3 className="font-display text-xl sm:text-2xl font-black tracking-tight text-slate-900 mt-1">
              Everything backup-related, in one place
            </h3>
            <p className="text-slate-600 text-sm mt-2 max-w-3xl">
              Anything that <strong>deletes or wipes data</strong> is locked behind an
              "Are you sure?" prompt and requires re-typing the admin password. The
              live database is never touched without your explicit re-confirmation.
            </p>
          </div>

          {/* 1 · BACKUP HERO — make + email + download .zip (always safe) */}
          <div className="mb-2">
            <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500 font-bold">
              1 · One-click backup &amp; restore
            </div>
            <p className="text-xs text-slate-600 mt-1 mb-2 max-w-3xl">
              The two big buttons most admins ever need. <strong>Backup Everything</strong>{" "}
              builds a single .zip of every safety record, photo, signature, and PDF —
              downloads it AND emails a copy. <strong>Restore From File</strong> uploads
              that .zip back in safe merge mode (existing rows updated, new rows added,
              nothing wiped).
            </p>
          </div>
          <BackupHeroPanel />

          {/* 2 · STORED BACKUPS — on-server backup library */}
          <div className="mt-8 mb-2">
            <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500 font-bold">
              2 · Stored backups on this server
            </div>
            <p className="text-xs text-slate-600 mt-1 mb-2 max-w-3xl">
              The list of every scheduled backup .zip currently saved on disk. Run a
              backup now, download an old one for off-site storage, or delete one you
              no longer need. <strong>Delete</strong> requires admin-password
              re-entry. Backups are made automatically twice daily (02:00 UTC + 18:00
              UTC) and pruned after retention.
            </p>
          </div>
          <StoredBackupsPanel />

          {/* 3 · RESTORE FROM BACKUP — merge (safe) or replace (wipes) */}
          <div className="mt-8 mb-2">
            <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500 font-bold">
              3 · Restore from backup file
            </div>
            <p className="text-xs text-slate-600 mt-1 mb-2 max-w-3xl">
              Advanced restore with two modes. <strong>Merge</strong> upserts every
              row in the .zip — safe, repeatable, nothing is wiped. <strong>Replace</strong>{" "}
              wipes every collection found in the .zip first, then reinserts — used
              only to roll the system back to a known-good snapshot. Replace requires
              typing <em>REPLACE</em> AND the admin password.
            </p>
          </div>
          <RestoreBackupPanel />

          {/* 4 · SYSTEM RECOVERY — force-reseed equipment / employees / suppliers */}
          <div className="mt-8 mb-2">
            <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500 font-bold">
              4 · Emergency system recovery
            </div>
            <p className="text-xs text-slate-600 mt-1 mb-2 max-w-3xl">
              Live count of every database collection — flags equipment / employees /
              suppliers in red if any are empty after a redeploy. The{" "}
              <strong>Force re-seed</strong> button wipes those four lists and reloads
              them from the JSON seed files; safety records, projects, and user
              accounts are never touched. Force re-seed requires admin-password
              re-entry.
            </p>
          </div>
          <CrewRecoveryPanel />
        </div>
      </main>

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-8 flex flex-col items-center gap-5 border-t border-slate-200">
        <div className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500">
          MASCI · Office Console
        </div>
        <BackendVersionBadge />
        <ForgedOpsAttribution variant="admin" />
      </footer>
    </div>
  );
}
