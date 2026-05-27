// PmShell.jsx — Shared layout for the section-based PM portal (iter105)
//
// Mirrors AdminShell but with:
//   - amber-600 accent (PM portal color)
//   - PM-only sections (no system/backups/access-control)
//   - PM token sign-out instead of admin
//
// Each PM section page wraps panels in <PmShell title="Jobs" section="jobs"> and
// the chrome handles header/sidebar/footer.

import React, { useMemo, useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard, Building2, Wrench, Mail, Users, Truck, FileImage,
  ClipboardCheck, LogOut, Menu as MenuIcon, Home, Briefcase, UserCheck, KeyRound,
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
import {
  Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger,
} from "@/components/ui/sheet";
import SideNavV2, { isPmSidebarV2Enabled } from "@/components/pm/sidebar/SideNavV2";
import { api } from "@/lib/api";
import { clearPmToken } from "@/lib/pmAuth";
import { clearAllSessions } from "@/lib/sessionReset";
import { toast } from "sonner";

const SECTIONS = [
  { key: "overview",        to: "/pm",                   icon: LayoutDashboard, label: "Overview",        desc: "Forms · Jobs · Search" },
  { key: "jobs",            to: "/pm/jobs",              icon: Briefcase,       label: "Jobs",            desc: "Jobs assigned to you (read-only)" },
  { key: "field-leadership", to: "/pm/field-leadership", icon: UserCheck,       label: "Field Leadership", desc: "Crew docs · My jobs only" },
  { key: "fleet",           to: "/pm/fleet",             icon: Wrench,          label: "Equipment Fleet", desc: "Master · Parts (read-only)" },
  { key: "people",          to: "/pm/people",            icon: Users,           label: "People",          desc: "Employee master (read-only)" },
  { key: "suppliers",       to: "/pm/suppliers",         icon: Truck,           label: "Suppliers",       desc: "Supplier master (read-only)" },
  { key: "posters",         to: "/pm/posters",           icon: FileImage,       label: "Site Posters",    desc: "JHP · Trench Box · Inspection QRs" },
];

export { SECTIONS };

function SideNav({ active, onNavigate }) {
  return (
    <nav className="space-y-1 p-3" data-testid="pm-side-nav">
      {SECTIONS.map((s) => (
        <NavLink
          key={s.key}
          to={s.to}
          end={s.key === "overview"}
          onClick={onNavigate}
          className={({ isActive }) =>
            `group flex items-start gap-2.5 rounded-md px-3 py-2.5 transition-colors ${
              isActive || s.key === active
                ? "bg-amber-600 text-white shadow-sm"
                : "text-slate-200 hover:bg-slate-800 hover:text-white"
            }`
          }
          data-testid={`pm-nav-${s.key}`}
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

export default function PmShell({ title, section, children, intro }) {
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  // Phase IV-BETA.1 — Feature-flagged V2 sidebar. Resolved once per mount
  // so toggling the flag requires a page reload (predictable rollout).
  // Legacy <SideNav> remains the default; V2 must be opted in.
  const useV2Sidebar = useMemo(() => isPmSidebarV2Enabled(), []);
  const renderNav = (onNavigate) =>
    useV2Sidebar
      ? <SideNavV2 onNavigate={onNavigate} />
      : <SideNav active={section} onNavigate={onNavigate} />;

  const signOut = async () => {
    try { await api.post("/pm/logout"); } catch { /* ignore */ }
    // P0 (iter179): wipe every auth artifact, not just PM.
    await clearAllSessions();
    toast.success("Signed out");
    navigate("/pm/login", { replace: true });
  };

  return (
    <div className="min-h-screen blueprint-bg flex flex-col overflow-x-hidden">
      <div className="caution-stripe" />

      <header className="sticky top-0 z-30 bg-slate-900 border-b-4 border-amber-600 shadow-lg">
        <div className="max-w-7xl mx-auto px-3 sm:px-5 py-3 flex items-center gap-2 sm:gap-4">
          <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
            <SheetTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="lg:hidden text-white hover:bg-slate-800 hover:text-white p-2"
                data-testid="pm-mobile-nav-trigger"
              >
                <MenuIcon className="w-5 h-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="bg-slate-900 border-r-2 border-amber-600 p-0 w-72 flex flex-col">
              <SheetHeader className="px-4 pt-4 pb-2 border-b border-slate-800 shrink-0">
                <SheetTitle className="text-white font-display text-lg flex items-center gap-2">
                  <Briefcase className="w-4 h-4 text-amber-400" /> PM Portal
                </SheetTitle>
              </SheetHeader>
              {/* iter437 Phase IV-BETA.1 · PM mobile sidebar scroll fix
                  Mirrors AdminShell Phase IV-A.0. Without an explicit
                  scroll wrapper, iOS Safari does not auto-scroll
                  overflowing children of a `position: fixed` ancestor —
                  the bottom of the menu would be unreachable. */}
              <div
                className="flex-1 min-h-0 overflow-y-auto overscroll-contain"
                style={{ WebkitOverflowScrolling: "touch" }}
                data-testid="pm-mobile-nav-scroll"
              >
                {renderNav(() => setMobileOpen(false))}
              </div>
            </SheetContent>
          </Sheet>

          <MasciLogo variant="mark" size="md" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="sm" className="sm:hidden" homeLink="/" />

          <div className="flex-1 min-w-0">
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-amber-300 font-bold flex items-center gap-1.5">
              {section !== "overview" ? (
                <>
                  <Link
                    to="/pm"
                    className="hover:text-white hover:underline underline-offset-2 transition-colors"
                    data-testid="pm-breadcrumb-home"
                  >
                    PM Portal
                  </Link>
                  <span className="text-amber-500 opacity-60">›</span>
                  <span className="text-amber-200">{title}</span>
                </>
              ) : (
                <span>PM Portal</span>
              )}
            </div>
            <div
              className="font-display text-base sm:text-lg font-black text-white truncate leading-tight"
              data-testid="pm-section-title"
            >
              {title}
            </div>
          </div>

          {/* iter203 — Mobile header collapse: on <sm hide
              PortalSwitcher, GlobalSearch, SystemHealthBadge, and
              KeyRound (change-password). Keep visible: hamburger, logo,
              title, NotificationBell, OfflineIndicator, Sign Out icon.
              Non-essentials remain accessible via the mobile sheet. */}
          <div className="flex items-center gap-1 sm:gap-1.5 shrink-0">
            <div className="hidden sm:flex items-center gap-1.5">
              <PortalSwitcher current="pm" />
              <GlobalSearch accent="dark" />
            </div>
            <NotificationBell accent="white" />
            <OfflineIndicator />
            <div className="hidden sm:flex items-center gap-1.5">
              <SystemHealthBadge />
            </div>
            <Link
              to="/"
              className="hidden md:inline-flex items-center h-8 px-2.5 rounded-md text-white hover:bg-slate-800 text-xs font-bold uppercase tracking-wide"
              data-testid="pm-hub-link"
              title="Public Hub"
            >
              <Home className="w-3.5 h-3.5" />
            </Link>
            <Link
              to="/pm/change-password"
              className="hidden sm:inline-flex items-center h-8 px-2.5 rounded-md text-white hover:bg-slate-800 text-xs font-bold uppercase tracking-wide"
              data-testid="pm-change-password"
              title="Change My Password"
            >
              <KeyRound className="w-3.5 h-3.5" />
            </Link>
            <Button
              variant="ghost"
              size="sm"
              onClick={signOut}
              className="text-white hover:bg-amber-900 hover:text-white h-8 px-2 sm:px-2.5 text-xs"
              data-testid="pm-sign-out"
              title="Sign out"
            >
              <LogOut className="w-3.5 h-3.5 sm:mr-1" />
              <span className="hidden sm:inline">Sign out</span>
            </Button>
          </div>
        </div>
      </header>

      <div className="flex-1 max-w-7xl mx-auto w-full px-3 sm:px-5 py-5 sm:py-6 flex gap-6">
        <aside
          className="hidden lg:block w-64 shrink-0 self-start sticky top-[72px]"
          data-testid="pm-side-nav-desktop"
        >
          <div className="rounded-md bg-slate-900 border-2 border-slate-800 overflow-hidden">
            {renderNav()}
          </div>
          <div className="mt-3 px-3 text-[9px] font-mono uppercase tracking-[0.22em] text-slate-400 flex items-center justify-between">
            <BackendVersionBadge />
          </div>
        </aside>

        <main className="flex-1 min-w-0" data-testid="pm-section-body">
          {section !== "overview" && (
            <div className="mb-3 flex items-center gap-2 flex-wrap">
              <Link
                to="/pm"
                className="inline-flex items-center gap-1.5 h-8 px-3 rounded-md bg-white border-2 border-slate-300 hover:border-amber-600 hover:text-amber-700 text-slate-700 text-xs font-bold uppercase tracking-wide transition-colors"
                data-testid="pm-back-to-overview"
              >
                <LayoutDashboard className="w-3.5 h-3.5" />
                ← Back to PM Overview
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
