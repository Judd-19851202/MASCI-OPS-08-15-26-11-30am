// MASCI Operations Platform · <PortalShell>
//
// Unified authenticated portal chrome.
// Backward-compatible API: old call sites (portalName + portalRole + pageTitle + subtitle)
// keep working unchanged. New props (showHome, showBack, providerLine, hideProviderLine)
// fill in the SV-04/SV-05/SV-06 gaps catalogued in UXS-1 by lighting up MASCI mark +
// "Powered by ForgedOps" footer + Home button across every consumer.
//
// Local-time rendering: `lastActivity` accepts a string OR a Date/ISO that we format
// with `toLocaleTimeString()` so dashboard timestamps display in the user's device tz.

import React from "react";
import { Link } from "react-router-dom";
import { Home as HomeIcon, ArrowLeft, LogOut, Clock, User as UserIcon, MoreHorizontal } from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { ForgedOpsAttribution } from "@/components/ForgedOpsAttribution";
import GlobalSearch from "@/components/GlobalSearch";
import NotificationBell from "@/components/NotificationBell";
import PortalSwitcher from "@/components/PortalSwitcher";
import { LangToggle } from "@/components/LangToggle";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { useBranding } from "@/lib/BrandingProvider";
import { clearAllSessions } from "@/lib/sessionReset";
// TRACK 27.03 · Final Completion · canonical local-time formatter.
import { formatPlatformTimeOnly } from "@/lib/platformTime";

function useLocalClock() {
  const [now, setNow] = React.useState(() => new Date());
  React.useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 30 * 1000);
    return () => clearInterval(id);
  }, []);
  return now;
}

function resolveSignedInName() {
  if (typeof window === "undefined") return null;
  // Probe known portal identity caches without coupling to any one auth lib.
  const keys = [
    "masci.directory.user",
    "masci.admin.user",
    "masci.pm.user",
    "masci.hr.user",
    "masci.shop.user",
    "masci.safety.user",
    "masci.dispatch.user",
    "masci.fl.user",
  ];
  for (const k of keys) {
    try {
      const raw = localStorage.getItem(k) || sessionStorage.getItem(k);
      if (!raw) continue;
      const parsed = JSON.parse(raw);
      const candidate = parsed?.name || parsed?.full_name || parsed?.email || parsed?.user?.name || parsed?.user?.email;
      if (candidate) return candidate;
    } catch { /* noop */ }
  }
  return null;
}

function formatLastActivity(value) {
  if (value == null) return null;
  if (typeof value === "string") {
    // Already a label like "Refreshed 2:14 PM"
    return value;
  }
  if (value instanceof Date || typeof value === "number") {
    const d = value instanceof Date ? value : new Date(value);
    if (!Number.isNaN(d.getTime())) {
      return `Updated ${formatPlatformTimeOnly(d)}`;
    }
  }
  // React node — render as-is
  return value;
}

export function PortalShell({
  portalName = "MASCI",
  portalRole,
  pageTitle,
  subtitle,
  primaryActions = null,
  lastActivity = null,
  alertSlot = null,
  homeHref = "/",
  backHref = null,
  showHome = true,
  showBack = false,
  showSearch = true,
  showNotifications = true,
  showPortalSwitcher = true,
  showSignOut = true,
  signOutCapability = null,
  portalSwitcherCurrent = null,
  hideProviderLine = false,
  onSignOut = null,
  sideNav = null,
  children,
  className = "",
}) {
  const branding = useBranding();
  const platformShort = branding.platform_short_name || portalName;
  const platformDisplay = branding.platform_display_name || "Operations Platform";
  const renderedLastActivity = formatLastActivity(lastActivity);
  const clock = useLocalClock();
  const localTimeLabel = formatPlatformTimeOnly(clock);
  const signedInName = React.useMemo(() => resolveSignedInName(), []);
  const handleSignOut = async () => {
    if (signOutCapability && signOutCapability.available !== true) return;
    if (typeof onSignOut === "function") {
      onSignOut();
      return;
    }
    await clearAllSessions();
    window.location.assign("/sign-in");
  };

  return (
    <div
      data-testid="ds-portal-shell"
      className={className}
      style={{ background: "var(--paper-base)", color: "var(--ink-regular)", minHeight: "100vh", display: "flex", flexDirection: "column" }}
    >
      {/* MASCI top chrome — unified across all authenticated portals */}
      <header
        data-testid="ds-portal-shell-header"
        className="sticky top-0 z-30 border-b-4 border-red-700 shadow-md overflow-hidden elite-shell-header"
      >
        <div className="max-w-[1600px] mx-auto px-3 sm:px-6 py-2.5 flex items-center gap-2 sm:gap-3 min-w-0">
          {/* MASCI mark — anchors brand identity in every portal */}
          <MasciLogo variant="mark" size="md" className="hidden sm:block shrink-0" homeLink={homeHref} />
          <MasciLogo variant="mark" size="sm" className="sm:hidden shrink-0" homeLink={homeHref} />

          <div className="hidden md:block min-w-0 flex-1">
            <div
              className="font-mono uppercase tracking-[0.18em] font-bold text-[10px] text-red-300"
              data-testid="ds-portal-shell-portal-name"
            >
              {portalName} · {portalRole}
            </div>
            {pageTitle && (
              <div className="text-white font-bold truncate text-sm" data-testid="ds-portal-shell-page-name">
                {pageTitle}
              </div>
            )}
          </div>

          {/* Right-side nav cluster — unified MASCI chrome.
              TRACK 28.08 · Phase 0 · D4-PORTALSHELL-MOBILE-OVERFLOW:
              on <md viewports, secondary controls (SEARCH, PortalSwitcher,
              clock, LangToggle, user name) collapse into a "•••" overflow
              popover so the row can never push past a 390px viewport. */}
          <div className="ml-auto flex items-center gap-1.5 sm:gap-2 min-w-0 shrink">
            {showSearch && (
              <div className="hidden lg:block shrink-0" data-testid="ds-portal-shell-search">
                <GlobalSearch accent="dark" />
              </div>
            )}
            {showNotifications && (
              <div className="shrink-0" data-testid="ds-portal-shell-notifications">
                <NotificationBell accent="white" />
              </div>
            )}
            {showPortalSwitcher && (
              <div className="hidden md:block shrink-0" data-testid="ds-portal-shell-portal-switcher">
                <PortalSwitcher current={portalSwitcherCurrent} />
              </div>
            )}
            <div
              className="hidden sm:inline-flex items-center gap-1 px-2.5 h-9 rounded border border-slate-700 text-slate-200 text-xs font-mono tracking-widest tabular-nums shrink-0"
              data-testid="ds-portal-shell-local-time"
              title="Local device time"
            >
              <Clock className="w-3 h-3 opacity-70" />
              {localTimeLabel}
            </div>
            <div className="hidden md:block shrink-0" data-testid="ds-portal-shell-lang-toggle">
              <LangToggle variant="dark" className="h-9" />
            </div>
            {signedInName && (
              <div
                className="hidden xl:inline-flex items-center gap-1.5 px-2.5 h-9 rounded border border-slate-700 text-slate-200 text-xs font-bold tracking-wide max-w-[160px] shrink-0"
                data-testid="ds-portal-shell-user"
                title={signedInName}
              >
                <UserIcon className="w-3.5 h-3.5 opacity-70" />
                <span className="truncate">{signedInName}</span>
              </div>
            )}

            {/* Mobile overflow popover — surfaces the secondary controls
                that are hidden on <md (SEARCH, PortalSwitcher, clock,
                LangToggle, signed-in name). Visible only on <md so it
                doesn't clutter tablet/desktop chrome. */}
            <Popover>
              <PopoverTrigger asChild>
                <button
                  type="button"
                  className="md:hidden inline-flex items-center justify-center w-9 h-9 rounded border border-slate-700 text-slate-200 hover:bg-slate-800 shrink-0"
                  aria-label="More options"
                  title="More"
                  data-testid="ds-portal-shell-mobile-more"
                >
                  <MoreHorizontal className="w-4 h-4" />
                </button>
              </PopoverTrigger>
              <PopoverContent
                align="end"
                sideOffset={8}
                className="w-64 p-3 bg-slate-900/78 border-slate-700 text-slate-100 elite-glass-modal"
                data-testid="ds-portal-shell-mobile-more-menu"
              >
                <div className="flex flex-col gap-3">
                  <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-red-300">
                    {portalName} · {portalRole}
                  </div>
                  {signedInName && (
                    <div className="inline-flex items-center gap-1.5 text-xs text-slate-200 font-bold">
                      <UserIcon className="w-3.5 h-3.5 opacity-70" />
                      <span className="truncate">{signedInName}</span>
                    </div>
                  )}
                  <div className="inline-flex items-center gap-1 text-xs font-mono tracking-widest tabular-nums text-slate-300">
                    <Clock className="w-3 h-3 opacity-70" />
                    {localTimeLabel}
                  </div>
                  {showSearch && (
                    <div data-testid="ds-portal-shell-mobile-search">
                      <GlobalSearch accent="dark" />
                    </div>
                  )}
                  <div className="flex items-center justify-between gap-2">
                    {showPortalSwitcher && (
                      <div data-testid="ds-portal-shell-mobile-portal-switcher">
                        <PortalSwitcher current={portalSwitcherCurrent} />
                      </div>
                    )}
                    <div data-testid="ds-portal-shell-mobile-lang-toggle">
                      <LangToggle variant="dark" className="h-9" />
                    </div>
                  </div>
                </div>
              </PopoverContent>
            </Popover>

            {showBack && backHref && (
              <Link
                to={backHref}
                className="hidden sm:inline-flex items-center gap-1 px-2.5 h-9 rounded border border-slate-700 text-slate-200 hover:bg-slate-800 text-xs font-bold uppercase tracking-wide shrink-0"
                aria-label="Go back"
                title="Back"
                data-testid="ds-portal-shell-back"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> Back
              </Link>
            )}
            {showHome && (
              <Link
                to={homeHref}
                className="inline-flex items-center gap-1 px-2.5 h-9 rounded border border-slate-700 text-slate-200 hover:bg-slate-800 text-xs font-bold uppercase tracking-wide shrink-0"
                aria-label="Home"
                title="Home"
                data-testid="ds-portal-shell-home"
              >
                <HomeIcon className="w-3.5 h-3.5" /> <span className="hidden sm:inline">Home</span>
              </Link>
            )}
            {showSignOut && (
              <button
                type="button"
                onClick={handleSignOut}
                disabled={!!signOutCapability && signOutCapability.available !== true}
                className="inline-flex items-center gap-1 px-2.5 h-9 rounded border border-slate-700 text-slate-200 hover:bg-slate-800 text-xs font-bold uppercase tracking-wide shrink-0"
                aria-label="Sign out"
                title={signOutCapability?.disabled_reason || "Sign out"}
                data-testid="ds-portal-shell-signout"
              >
                <LogOut className="w-3.5 h-3.5" /> <span className="hidden lg:inline">Sign out</span>
              </button>
            )}
          </div>
        </div>
      </header>

      <section style={{ padding: "var(--pad-section)" }} className="flex-1 blueprint-bg min-w-0">
        <div className="max-w-[1600px] mx-auto px-4 sm:px-6 min-w-0">
          <div className={sideNav ? "lg:grid lg:grid-cols-[260px_1fr] lg:gap-6 min-w-0" : "min-w-0"}>
            {sideNav && (
              <aside
                className="hidden lg:block sticky top-[4.25rem] h-[calc(100vh-4.25rem)] overflow-y-auto text-slate-100 -ml-4 sm:-ml-6 pl-4 sm:pl-6 pr-2 py-4 border-r border-slate-800 elite-glass-sidebar"
                data-testid="ds-portal-shell-sidenav"
              >
                {sideNav}
              </aside>
            )}
            <div className="min-w-0">
          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3 md:gap-4" style={{ marginBottom: 16 }}>
            <div className="min-w-0 flex-1">
              {/* Mobile-only portal kicker (already in header on desktop) */}
              <div
                className="md:hidden font-mono uppercase tracking-[0.18em] font-bold text-[10px] text-slate-500 mb-1"
                data-testid="ds-portal-shell-portal-name-mobile"
              >
                {portalName} · {portalRole}
              </div>
              {pageTitle && (
                <h1
                  // TRACK 22.4c mobile responsiveness — the shell H1
                  // must never extrude past its flex parent. Long
                  // question-style titles ("What requires the
                  // dispatcher's attention right now?") can render at
                  // >500px in the display font before whitespace
                  // wrapping settles, briefly pushing the layout past
                  // a 390px viewport. `overflowWrap:anywhere` +
                  // `minWidth:0` on the flex child force early wrap.
                  style={{
                    fontSize: 28, fontWeight: 700, margin: 0,
                    color: "var(--ink-strong)", fontFamily: "var(--font-display)",
                    overflowWrap: "anywhere",
                    wordBreak: "break-word",
                    hyphens: "auto",
                    lineHeight: 1.15,
                  }}
                >
                  {pageTitle}
                </h1>
              )}
              {subtitle && (
                <p style={{ color: "var(--ink-soft)", margin: "4px 0 0", fontSize: 14 }}>
                  {subtitle}
                </p>
              )}
            </div>
            {/* TRACK 28.08 · Phase 0 · D4 — on <md, the primary actions cluster
                stacks below the title (flex-col wrapper above) so the H1 can
                claim the full row width and never collapses to 0. It also
                `flex-wrap` internally so multi-button clusters like the Admin
                OS (Search/Refresh/Export snapshot) don't extrude past a 390px
                viewport. `min-w-0` lets any child shrink cleanly. */}
            <div className="flex flex-row md:flex-col md:items-end flex-wrap items-center gap-2 min-w-0">
              {primaryActions}
              {renderedLastActivity && (
                <aside style={{ color: "var(--ink-soft)", fontSize: 12 }} data-testid="ds-portal-shell-last-activity">
                  {renderedLastActivity}
                </aside>
              )}
            </div>
          </div>

          {alertSlot && <div style={{ marginBottom: 16 }}>{alertSlot}</div>}

          <main data-testid="ds-portal-shell-content">{children}</main>
            </div>
          </div>
        </div>
      </section>

      {!hideProviderLine && (
        <footer
          data-testid="ds-portal-shell-footer"
          className="border-t border-slate-200 bg-slate-50 py-3 mt-6"
        >
          <div className="max-w-[1600px] mx-auto px-4 sm:px-6 flex items-center justify-between">
            <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-slate-500">
              {platformDisplay}
            </div>
            <ForgedOpsAttribution variant="login" />
          </div>
        </footer>
      )}
    </div>
  );
}

export default PortalShell;
