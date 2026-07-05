// AdminShell.jsx — Shared layout for the new section-based admin (iter83)
//
// Wraps every /admin/* page with:
//   - Red top bar (MASCI lockup, page title, PortalSwitcher, SystemHealthBadge, Sign out)
//   - Left-side persistent nav with all 8 admin sections (collapsible on mobile via Sheet)
//   - Body slot for the section's panels
//   - ForgedOps™ footer
//
// Each section page just wraps its panels in <AdminShell title="Equipment & Suppliers" section="equipment">
// and the chrome takes care of everything else.

import React, { useEffect, useMemo, useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard, Users, Building2, Wrench, Mail, BookOpen, ClipboardCheck,
  ShieldCheck, LogOut, Menu as MenuIcon, Home, Cable, Truck, Activity,
  Rocket, History, GraduationCap, ListChecks, ChartBar, Map, Film, Database,
  Clock, NotebookPen, ListTodo, Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { ForgedOpsAttribution } from "@/components/ForgedOpsAttribution";
import { BackendVersionBadge } from "@/components/BackendVersionBadge";
import SystemHealthBadge from "@/components/SystemHealthBadge";
import PortalSwitcher from "@/components/PortalSwitcher";
import NotificationBell from "@/components/NotificationBell";
import { OfflineIndicator } from "@/lib/resiliency";
import GlobalSearch from "@/components/GlobalSearch";
import AdminGlobalSearch from "@/components/AdminGlobalSearch";
import { LangToggle } from "@/components/LangToggle";
import {
  Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger,
} from "@/components/ui/sheet";
import SideNavV2, { isAdminSidebarV2Enabled } from "@/components/admin/sidebar/SideNavV2";
import { api } from "@/lib/api";
import { clearAdminToken } from "@/lib/adminAuth";
import { clearPmToken } from "@/lib/pmAuth";
import { clearShopToken } from "@/lib/shopAuth";
import { clearAllSessions } from "@/lib/sessionReset";
import { toast } from "sonner";

const SECTIONS = [
  { key: "overview",   to: "/admin",            icon: LayoutDashboard, label: "Overview",     desc: "KPIs, search, snapshot" },
  { key: "command-center", to: "/admin/command-center", icon: Activity, label: "Command Center", desc: "Executive single-glass · Jobs · Safety · Equipment · Accountability · Approvals" },
  { key: "people",     to: "/admin/people",     icon: Users,           label: "People & Access", desc: "PM · Shop · HR · Multi-portal · Employee master" },
  { key: "jobs",       to: "/admin/jobs",       icon: Building2,       label: "Jobs & Field",    desc: "Job master · Posters · Banners" },
  { key: "equipment",  to: "/admin/equipment",  icon: Wrench,          label: "Equipment & Suppliers", desc: "Status board · Master · Parts · Suppliers" },
  { key: "asset-admin", to: "/admin/asset-admin", icon: ShieldCheck,    label: "Asset Administration", desc: "Canonical taxonomy · review queue · registrations · insurance" },
  { key: "email",      to: "/admin/email",      icon: Mail,            label: "Email & Routing", desc: "Auto-routing · Distribution lists" },
  { key: "training",   to: "/admin/training",   icon: BookOpen,        label: "Training & Forms",desc: "Training resources · Safety forms" },
  { key: "compliance", to: "/admin/compliance", icon: ClipboardCheck,  label: "Compliance & Audits", desc: "Exports · Date audit" },
  { key: "tasks",      to: "/tasks",            icon: ClipboardCheck,  label: "Tasks & Actions", desc: "Cross-portal accountability · Open · Overdue · Completed" },
  { key: "expirations", to: "/document-expirations", icon: ClipboardCheck, label: "Document Expirations", desc: "OSHA · TWIC · CDL · Registrations · Inspections" },
  { key: "po",         to: "/po-requests",       icon: ClipboardCheck,  label: "PO Requests",     desc: "Field POs · approvals · receipt tracking" },
  { key: "project-health", to: "/project-health", icon: Activity,        label: "Project Health",  desc: "Operational friction by job · per-project status" },
  { key: "asset-transfers", to: "/asset-transfers", icon: Truck,         label: "Asset Transfers", desc: "Equipment movement · lifecycle · receiving" },
  { key: "dispatch",   to: "/admin/dispatch",   icon: Truck,           label: "Transportation Operations", desc: "Transfers · Holds · Utilization" },
  { key: "events",     to: "/admin/operations-events", icon: Activity, label: "Operations Events", desc: "Append-only log · platform history" },
  { key: "odr-center", to: "/odr/center", icon: NotebookPen, label: "Operational Daily Records", desc: "Field-day system of record · FLL-aware ODR rollups" },
  { key: "operational-records", to: "/operational-records", icon: NotebookPen, label: "Operational Records", desc: "Cross-portal field-day records · Phase V.1" },
  { key: "operations-actions", to: "/operations-actions", icon: ListTodo, label: "Operations Actions", desc: "Cross-portal operational tasks · owners" },
  { key: "integrations", to: "/admin/integrations", icon: Cable,       label: "Integrations",    desc: "Motive · MaintainX · CSV import/export" },
  { key: "system",     to: "/admin/system",     icon: ShieldCheck,     label: "System & Backups",desc: "Backups · R2 · Restore · Recovery" },
  { key: "ai-configuration", to: "/admin/ai-configuration", icon: Sparkles, label: "AI Configuration", desc: "Optional intelligence · tenant AI switchboard · admin-only" },
  { key: "integration-truth", to: "/admin/integration-truth", icon: ShieldCheck, label: "Integration Truth", desc: "Runtime AI keys · third-party integration state · legacy alias telemetry" },
  { key: "system-health", to: "/admin/system-health", icon: Activity,  label: "System Health",   desc: "Green/yellow/red operational probe" },
  { key: "database", to: "/admin/database", icon: Database, label: "Database",   desc: "Atlas capacity · 30-day storage trend · runway" },
  { key: "digest-config", to: "/admin/digest-config", icon: Mail,      label: "Weekly Digest",   desc: "Recipients · schedule · preview · send" },
  { key: "operational-intelligence", to: "/admin/operational-intelligence", icon: Activity, label: "Operational Intelligence", desc: "Scores · previews · history · audit for all 11 intelligence products" },
  { key: "audit-log",  to: "/admin/audit-log",  icon: History,         label: "Audit Log",       desc: "Unified merged timeline" },
  { key: "sessions",   to: "/admin/sessions",   icon: Activity,        label: "Sessions",        desc: "Last 50 portal sessions · idle/abs status · forensic only" },
  { key: "deploy-recovery", to: "/admin/deploy-recovery", icon: Rocket, label: "Deploy Recovery", desc: "Rollback playbook · backup chain" },
  { key: "deploy-readiness", to: "/admin/deploy-readiness", icon: ListChecks, label: "Deploy Readiness", desc: "Pre-deploy QA · Mongo · indexes · R2 · integrations" },
  { key: "analytics", to: "/admin/analytics", icon: ChartBar, label: "Usage Analytics", desc: "Operational insight · routes · portals · friction" },
  { key: "operational-guidance", to: "/guidance", icon: GraduationCap, label: "Operational Guidance Center", desc: "RBAC-aware portal training · operator guides · troubleshooting" },
  { key: "operational-inventory", to: "/admin/operational-inventory", icon: Map, label: "Operational Inventory", desc: "Live governance dashboard · 10-field coverage matrix · drift detection" },
  { key: "governance", to: "/admin/governance", icon: ShieldCheck, label: "Governance Health", desc: "Compliance gap detector · cross-portal contradictions · convergence score" },
  { key: "project-identity", to: "/admin/project-identity", icon: ShieldCheck, label: "Project Identity Governance", desc: "Detect drift across project numbers & names · operator-only resolution · zero auto-mutation" },
  { key: "operational-language", to: "/admin/operational-language", icon: BookOpen, label: "Operational Language", desc: "Shared glossary · single source of vocabulary truth · EN + ES" },
  { key: "promo-assets", to: "/admin/promo-assets", icon: Film, label: "Promo Assets", desc: "Cinematic platform clips · hero loops · social cuts · editor-ready library" },
];

export { SECTIONS };

function SideNav({ active, onNavigate }) {
  return (
    <nav className="space-y-1 p-3" data-testid="admin-side-nav">
      {SECTIONS.map((s) => (
        <NavLink
          key={s.key}
          to={s.to}
          end={s.key === "overview"}
          onClick={onNavigate}
          className={({ isActive }) =>
            `group flex items-start gap-2.5 rounded-md px-3 py-2.5 transition-colors ${
              isActive || s.key === active
                ? "bg-red-700 text-white shadow-sm"
                : "text-slate-200 hover:bg-slate-800 hover:text-white"
            }`
          }
          data-testid={`admin-nav-${s.key}`}
        >
          <s.icon className="w-4 h-4 mt-0.5 shrink-0" />
          <div className="min-w-0">
            <div className="text-sm font-bold leading-tight">{s.label}</div>
            <div className="text-[10px] uppercase tracking-wider opacity-70 mt-0.5 leading-tight font-mono">
              {s.desc}
            </div>
          </div>
        </NavLink>
      ))}
    </nav>
  );
}

export default function AdminShell({ title, section, children, intro }) {
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 30 * 1000);
    return () => clearInterval(id);
  }, []);
  const localTimeLabel = now.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  // Phase IV.A.1 — Feature-flagged V2 sidebar. Resolved once per mount
  // so toggling the flag requires a page reload (predictable rollout).
  // Legacy <SideNav> remains the default; V2 must be opted in.
  const useV2Sidebar = useMemo(() => isAdminSidebarV2Enabled(), []);
  const renderNav = (onNavigate) =>
    useV2Sidebar
      ? <SideNavV2 onNavigate={onNavigate} />
      : <SideNav active={section} onNavigate={onNavigate} />;

  const signOut = async () => {
    try { await api.post("/admin/logout"); } catch { /* ignore */ }
    // P0 access-control hardening (iter179): wipe EVERY auth artifact,
    // not just the admin tokens. Prevents stale cross-portal sessions
    // from inheriting across browser-sharing sign-in/out cycles.
    await clearAllSessions();
    toast.success("Signed out");
    navigate("/", { replace: true });
  };

  return (
    <div className="min-h-screen blueprint-bg flex flex-col overflow-x-clip">
      <div className="caution-stripe" />

      {/* Top bar — red gradient, sticky on scroll for context */}
      <header className="sticky top-0 z-30 bg-slate-900 border-b-4 border-red-700 shadow-lg">
        <div className="max-w-7xl mx-auto px-3 sm:px-5 py-3 flex items-center gap-2 sm:gap-4">
          {/* Mobile menu trigger */}
          <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
            <SheetTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="lg:hidden text-white hover:bg-slate-800 hover:text-white p-2"
                data-testid="admin-mobile-nav-trigger"
              >
                <MenuIcon className="w-5 h-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="bg-slate-900 border-r-2 border-red-700 p-0 w-72 flex flex-col">
              <SheetHeader className="px-4 pt-4 pb-2 border-b border-slate-800 shrink-0">
                <SheetTitle className="text-white font-display text-lg">Administration</SheetTitle>
              </SheetHeader>
              {/* iter437 Phase IV-A · mobile sidebar scroll fix
                  Root cause: SheetContent is `fixed inset-y-0 h-full`
                  with no internal scroll container. iOS Safari does
                  NOT auto-scroll overflowing children of a fixed
                  ancestor. Add an explicit flex-1 + overflow-y-auto
                  wrapper + WebKit momentum scroll. */}
              <div
                className="flex-1 min-h-0 overflow-y-auto overscroll-contain"
                style={{ WebkitOverflowScrolling: "touch" }}
                data-testid="admin-mobile-nav-scroll"
              >
                {renderNav(() => setMobileOpen(false))}
              </div>
            </SheetContent>
          </Sheet>

          <MasciLogo variant="mark" size="md" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="sm" className="sm:hidden" homeLink="/" />

          <div className="flex-1 min-w-0">
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-red-300 font-bold flex items-center gap-1.5">
              {section !== "overview" ? (
                <>
                  <Link
                    to="/admin"
                    className="hover:text-white hover:underline underline-offset-2 transition-colors"
                    data-testid="admin-breadcrumb-home"
                  >
                    Administration
                  </Link>
                  <span className="text-red-500 opacity-60">›</span>
                  <span className="text-red-200">{title}</span>
                </>
              ) : (
                <span>Administration</span>
              )}
            </div>
            <div
              className="font-display text-base sm:text-lg font-black text-white truncate leading-tight"
              data-testid="admin-section-title"
            >
              {title}
            </div>
          </div>

          {/* iter203 — Mobile header collapse: hide PortalSwitcher,
              GlobalSearch icon, SystemHealthBadge on <sm. Keep
              NotificationBell, OfflineIndicator, Sign Out visible. */}
          <div className="flex items-center gap-1 sm:gap-1.5 shrink-0">
            <div className="hidden md:block w-72">
              <AdminGlobalSearch />
            </div>
            <div className="hidden sm:flex items-center gap-1.5">
              <PortalSwitcher current="admin" />
              <div className="md:hidden"><GlobalSearch accent="dark" /></div>
            </div>
            <NotificationBell accent="white" />
            <OfflineIndicator />
            <div
              className="hidden sm:inline-flex items-center gap-1 px-2.5 h-8 rounded border border-slate-700 text-slate-200 text-[11px] font-mono tracking-widest tabular-nums"
              data-testid="admin-shell-local-time"
              title="Local device time"
            >
              <Clock className="w-3 h-3 opacity-70" />
              {localTimeLabel}
            </div>
            <div className="hidden md:block" data-testid="admin-shell-lang-toggle">
              <LangToggle variant="dark" className="h-8" />
            </div>
            <div className="hidden sm:flex"><SystemHealthBadge /></div>
            <Link
              to="/"
              className="hidden md:inline-flex items-center h-8 px-2.5 rounded-md text-white hover:bg-slate-800 text-xs font-bold uppercase tracking-wide"
              data-testid="admin-hub-link"
              title="Public Hub"
            >
              <Home className="w-3.5 h-3.5" />
            </Link>
            <Button
              variant="ghost"
              size="sm"
              onClick={signOut}
              className="text-white hover:bg-red-900 hover:text-white h-8 px-2 sm:px-2.5 text-xs"
              data-testid="admin-sign-out"
              title="Sign out"
            >
              <LogOut className="w-3.5 h-3.5 sm:mr-1" />
              <span className="hidden sm:inline">Sign out</span>
            </Button>
          </div>
        </div>
      </header>

      {/* Main layout: side nav (desktop only) + body */}
      <div className="flex-1 max-w-7xl mx-auto w-full px-3 sm:px-5 py-5 sm:py-6 flex gap-6">
        {/* Persistent side nav — desktop only */}
        <aside
          className="hidden lg:block w-64 shrink-0 self-start sticky top-[72px]"
          data-testid="admin-side-nav-desktop"
        >
          <div className="rounded-md bg-slate-900 border-2 border-slate-800 overflow-hidden">
            {renderNav()}
          </div>
          <div className="mt-3 px-3 text-[9px] font-mono uppercase tracking-[0.22em] text-slate-400 flex items-center justify-between">
            <BackendVersionBadge />
          </div>
        </aside>

        {/* Body content */}
        <main className="flex-1 min-w-0" data-testid="admin-section-body">
          {section !== "overview" && (
            <div className="mb-3 flex items-center gap-2 flex-wrap">
              <Link
                to="/admin"
                className="inline-flex items-center gap-1.5 h-8 px-3 rounded-md bg-white border-2 border-slate-300 hover:border-red-700 hover:text-red-700 text-slate-700 text-xs font-bold uppercase tracking-wide transition-colors"
                data-testid="admin-back-to-overview"
              >
                <LayoutDashboard className="w-3.5 h-3.5" />
                ← Back to Admin Overview
              </Link>
              <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-400">
                or use the menu at top-left
              </span>
            </div>
          )}
          {intro && (
            <div className="mb-5 p-4 sm:p-5 rounded-md bg-white border-2 border-slate-200 shadow-sm">
              {intro}
            </div>
          )}
          {children}
        </main>
      </div>

      <footer className="max-w-7xl mx-auto w-full px-3 sm:px-5 py-6 flex flex-col items-center gap-3">
        <ForgedOpsAttribution variant="login" />
      </footer>
    </div>
  );
}
