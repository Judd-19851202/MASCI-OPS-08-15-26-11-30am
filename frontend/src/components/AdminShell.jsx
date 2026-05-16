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

import React, { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard, Users, Building2, Wrench, Mail, BookOpen, ClipboardCheck,
  ShieldCheck, LogOut, Menu as MenuIcon, Home, Cable, Truck, Activity,
  Rocket, History, GraduationCap, ListChecks, ChartBar,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { ForgedOpsAttribution } from "@/components/ForgedOpsAttribution";
import { BackendVersionBadge } from "@/components/BackendVersionBadge";
import SystemHealthBadge from "@/components/SystemHealthBadge";
import PortalSwitcher from "@/components/PortalSwitcher";
import NotificationBell from "@/components/NotificationBell";
import GlobalSearch from "@/components/GlobalSearch";
import AdminGlobalSearch from "@/components/AdminGlobalSearch";
import {
  Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger,
} from "@/components/ui/sheet";
import { api } from "@/lib/api";
import { clearAdminToken } from "@/lib/adminAuth";
import { clearPmToken } from "@/lib/pmAuth";
import { clearShopToken } from "@/lib/shopAuth";
import { toast } from "sonner";

const SECTIONS = [
  { key: "overview",   to: "/admin",            icon: LayoutDashboard, label: "Overview",     desc: "KPIs, search, snapshot" },
  { key: "people",     to: "/admin/people",     icon: Users,           label: "People & Access", desc: "PM · Shop · HR · Multi-portal · Employee master" },
  { key: "jobs",       to: "/admin/jobs",       icon: Building2,       label: "Jobs & Field",    desc: "Job master · Posters · Banners" },
  { key: "equipment",  to: "/admin/equipment",  icon: Wrench,          label: "Equipment & Suppliers", desc: "Status board · Master · Parts · Suppliers" },
  { key: "email",      to: "/admin/email",      icon: Mail,            label: "Email & Routing", desc: "Auto-routing · Distribution lists" },
  { key: "training",   to: "/admin/training",   icon: BookOpen,        label: "Training & Forms",desc: "Training resources · Safety forms" },
  { key: "compliance", to: "/admin/compliance", icon: ClipboardCheck,  label: "Compliance & Audits", desc: "Exports · Date audit" },
  { key: "tasks",      to: "/tasks",            icon: ClipboardCheck,  label: "Tasks & Actions", desc: "Cross-portal accountability · Open · Overdue · Completed" },
  { key: "expirations", to: "/document-expirations", icon: ClipboardCheck, label: "Document Expirations", desc: "OSHA · TWIC · CDL · Registrations · Inspections" },
  { key: "po",         to: "/po-requests",       icon: ClipboardCheck,  label: "PO Requests",     desc: "Field POs · approvals · receipt tracking" },
  { key: "project-health", to: "/project-health", icon: Activity,        label: "Project Health",  desc: "Operational friction by job · per-project status" },
  { key: "dispatch",   to: "/admin/dispatch",   icon: Truck,           label: "Dispatch Portal", desc: "Transfers · Holds · Utilization" },
  { key: "events",     to: "/admin/operations-events", icon: Activity, label: "Operations Events", desc: "Append-only log · platform history" },
  { key: "integrations", to: "/admin/integrations", icon: Cable,       label: "Integrations",    desc: "Motive · MaintainX · CSV import/export" },
  { key: "system",     to: "/admin/system",     icon: ShieldCheck,     label: "System & Backups",desc: "Backups · R2 · Restore · Recovery" },
  { key: "system-health", to: "/admin/system-health", icon: Activity,  label: "System Health",   desc: "Green/yellow/red operational probe" },
  { key: "digest-config", to: "/admin/digest-config", icon: Mail,      label: "Weekly Digest",   desc: "Recipients · schedule · preview · send" },
  { key: "audit-log",  to: "/admin/audit-log",  icon: History,         label: "Audit Log",       desc: "Unified merged timeline" },
  { key: "deploy-recovery", to: "/admin/deploy-recovery", icon: Rocket, label: "Deploy Recovery", desc: "Rollback playbook · backup chain" },
  { key: "deploy-readiness", to: "/admin/deploy-readiness", icon: ListChecks, label: "Deploy Readiness", desc: "Pre-deploy QA · Mongo · indexes · R2 · integrations" },
  { key: "analytics", to: "/admin/analytics", icon: ChartBar, label: "Usage Analytics", desc: "Operational insight · routes · portals · friction" },
  { key: "ops-training", to: "/ops-training", icon: GraduationCap, label: "Operator Training", desc: "Step-by-step portal & integration guides · PDF download" },
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

  const signOut = async () => {
    try { await api.post("/admin/logout"); } catch { /* ignore */ }
    clearAdminToken();
    clearPmToken();
    clearShopToken();
    toast.success("Signed out");
    navigate("/", { replace: true });
  };

  return (
    <div className="min-h-screen blueprint-bg flex flex-col">
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
            <SheetContent side="left" className="bg-slate-900 border-r-2 border-red-700 p-0 w-72">
              <SheetHeader className="px-4 pt-4 pb-2 border-b border-slate-800">
                <SheetTitle className="text-white font-display text-lg">Admin Console</SheetTitle>
              </SheetHeader>
              <SideNav active={section} onNavigate={() => setMobileOpen(false)} />
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
                    Admin Console
                  </Link>
                  <span className="text-red-500 opacity-60">›</span>
                  <span className="text-red-200">{title}</span>
                </>
              ) : (
                <span>Admin Console</span>
              )}
            </div>
            <div
              className="font-display text-base sm:text-lg font-black text-white truncate leading-tight"
              data-testid="admin-section-title"
            >
              {title}
            </div>
          </div>

          <div className="flex items-center gap-1.5 shrink-0">
            <div className="hidden md:block w-72">
              <AdminGlobalSearch />
            </div>
            <PortalSwitcher current="admin" />
            <div className="md:hidden"><GlobalSearch accent="dark" /></div>
            <NotificationBell accent="white" />
            <SystemHealthBadge />
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
              className="text-white hover:bg-red-900 hover:text-white h-8 px-2.5 text-xs"
              data-testid="admin-sign-out"
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
            <SideNav active={section} />
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
