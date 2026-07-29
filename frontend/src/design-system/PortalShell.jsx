import React from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft,
  Clock,
  Home as HomeIcon,
  LogOut,
  MoreHorizontal,
  User as UserIcon,
} from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { ForgedOpsAttribution } from "@/components/ForgedOpsAttribution";
import GlobalSearch from "@/components/GlobalSearch";
import NotificationBell from "@/components/NotificationBell";
import PortalSwitcher from "@/components/PortalSwitcher";
import { LangToggle } from "@/components/LangToggle";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { useBranding } from "@/lib/BrandingProvider";
import { clearAllSessions } from "@/lib/sessionReset";
import { formatPlatformTimeOnly } from "@/lib/platformTime";
import { PageHeader } from "./PageHeader";
import { MobileNavigation } from "./MobileNavigation";

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
  for (const key of keys) {
    try {
      const raw = localStorage.getItem(key) || sessionStorage.getItem(key);
      if (!raw) continue;
      const parsed = JSON.parse(raw);
      const candidate = parsed?.name || parsed?.full_name || parsed?.email || parsed?.user?.name || parsed?.user?.email;
      if (candidate) return candidate;
    } catch {
      /* ignore malformed storage */
    }
  }
  return null;
}

function formatLastActivity(value) {
  if (value == null) return null;
  if (typeof value === "string") return value;
  if (value instanceof Date || typeof value === "number") {
    const date = value instanceof Date ? value : new Date(value);
    if (!Number.isNaN(date.getTime())) {
      return `Updated ${formatPlatformTimeOnly(date)}`;
    }
  }
  return value;
}

function UtilityButton({ children, className = "", ...props }) {
  return (
    <button
      type="button"
      className={`hidden sm:inline-flex wp16-focus-ring items-center gap-1 px-2.5 h-10 rounded-sm border border-zinc-300 bg-white text-zinc-700 hover:bg-zinc-50 text-xs font-bold uppercase tracking-wide shrink-0 ${className}`}
      {...props}
    >
      {children}
    </button>
  );
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
      className={`wp16-shell wp16-mobile-safe ${className}`}
      style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}
    >
      <header data-testid="ds-portal-shell-header" className="sticky top-0 z-30 wp16-topbar">
        <div className="max-w-[1600px] mx-auto px-3 sm:px-6 py-3 flex items-center gap-3 min-w-0">
          <MasciLogo variant="mark" size="md" className="hidden sm:block shrink-0" homeLink={homeHref} />
          <MasciLogo variant="mark" size="sm" className="sm:hidden shrink-0" homeLink={homeHref} />

          <div className="min-w-0 flex-1">
            <div className="wp16-kicker" data-testid="ds-portal-shell-portal-name">
              {portalName} · {portalRole}
            </div>
            <div className="text-sm sm:text-base font-semibold text-zinc-950 truncate" data-testid="ds-portal-shell-page-name">
              {pageTitle || platformDisplay}
            </div>
          </div>

          <div className="ml-auto flex items-center gap-1.5 sm:gap-2 min-w-0 shrink-0">
            {showSearch ? (
              <div className="hidden xl:block" data-testid="ds-portal-shell-search">
                <GlobalSearch accent="light" />
              </div>
            ) : null}

            {showNotifications ? (
              <div data-testid="ds-portal-shell-notifications">
                <NotificationBell accent="slate" />
              </div>
            ) : null}

            {showPortalSwitcher ? (
              <div className="hidden lg:block" data-testid="ds-portal-shell-portal-switcher">
                <PortalSwitcher current={portalSwitcherCurrent} variant="light" />
              </div>
            ) : null}

            <div
              className="hidden lg:inline-flex items-center gap-1 px-2.5 h-10 rounded-sm border border-zinc-300 bg-white text-zinc-700 text-xs font-mono tracking-widest tabular-nums shrink-0"
              data-testid="ds-portal-shell-local-time"
              title="Local device time"
            >
              <Clock className="w-3 h-3 opacity-70" />
              {localTimeLabel}
            </div>

            <div className="hidden lg:block" data-testid="ds-portal-shell-lang-toggle">
              <LangToggle variant="light" className="h-10" />
            </div>

            {signedInName ? (
              <div
                className="hidden 2xl:inline-flex items-center gap-1.5 px-2.5 h-10 rounded-sm border border-zinc-300 bg-white text-zinc-700 text-xs font-bold tracking-wide max-w-[180px] shrink-0"
                data-testid="ds-portal-shell-user"
                title={signedInName}
              >
                <UserIcon className="w-3.5 h-3.5 opacity-70" />
                <span className="truncate">{signedInName}</span>
              </div>
            ) : null}

            <Popover>
              <PopoverTrigger asChild>
                <button
                  type="button"
                  className="lg:hidden wp16-focus-ring inline-flex items-center justify-center w-10 h-10 rounded-sm border border-zinc-300 bg-white text-zinc-700 hover:bg-zinc-50"
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
                className="w-72 p-3 border-zinc-300 bg-white text-zinc-900 shadow-xl"
                data-testid="ds-portal-shell-mobile-more-menu"
              >
                <div className="flex flex-col gap-3">
                  <div className="wp16-kicker">{portalName} · {portalRole}</div>
                  {signedInName ? (
                    <div className="inline-flex items-center gap-1.5 text-xs text-zinc-700 font-bold">
                      <UserIcon className="w-3.5 h-3.5 opacity-70" />
                      <span className="truncate">{signedInName}</span>
                    </div>
                  ) : null}
                  <div className="inline-flex items-center gap-1 text-xs font-mono tracking-widest tabular-nums text-zinc-600">
                    <Clock className="w-3 h-3 opacity-70" />
                    {localTimeLabel}
                  </div>
                  {showSearch ? (
                    <div data-testid="ds-portal-shell-mobile-search">
                      <GlobalSearch accent="light" className="w-full justify-between" />
                    </div>
                  ) : null}
                  <div className="flex items-center justify-between gap-2">
                    {showPortalSwitcher ? (
                      <div data-testid="ds-portal-shell-mobile-portal-switcher">
                        <PortalSwitcher current={portalSwitcherCurrent} variant="light" />
                      </div>
                    ) : null}
                    <div data-testid="ds-portal-shell-mobile-lang-toggle">
                      <LangToggle variant="light" className="h-10" />
                    </div>
                  </div>
                </div>
              </PopoverContent>
            </Popover>

            {showBack && backHref ? (
              <Link
                to={backHref}
                className="hidden sm:inline-flex wp16-focus-ring items-center gap-1 px-2.5 h-10 rounded-sm border border-zinc-300 bg-white text-zinc-700 hover:bg-zinc-50 text-xs font-bold uppercase tracking-wide shrink-0"
                aria-label="Go back"
                title="Back"
                data-testid="ds-portal-shell-back"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> Back
              </Link>
            ) : null}

            {showHome ? (
              <Link
                to={homeHref}
                className="hidden sm:inline-flex wp16-focus-ring items-center gap-1 px-2.5 h-10 rounded-sm border border-zinc-300 bg-white text-zinc-700 hover:bg-zinc-50 text-xs font-bold uppercase tracking-wide shrink-0"
                aria-label="Home"
                title="Home"
                data-testid="ds-portal-shell-home"
              >
                <HomeIcon className="w-3.5 h-3.5" /> <span className="hidden lg:inline">Home</span>
              </Link>
            ) : null}

            {showSignOut ? (
              <UtilityButton
                onClick={handleSignOut}
                disabled={!!signOutCapability && signOutCapability.available !== true}
                aria-label="Sign out"
                title={signOutCapability?.disabled_reason || "Sign out"}
                data-testid="ds-portal-shell-signout"
              >
                <LogOut className="w-3.5 h-3.5" /> <span className="hidden lg:inline">Sign out</span>
              </UtilityButton>
            ) : null}
          </div>
        </div>
      </header>

      <section className="flex-1 px-3 sm:px-6 py-4 sm:py-6 min-w-0">
        <div className="max-w-[1600px] mx-auto min-w-0">
          <div className={sideNav ? "wp16-grid-columns--shell min-w-0" : "min-w-0"}>
            {sideNav ? (
              <aside
                className="hidden lg:block sticky top-[5.5rem] self-start max-h-[calc(100vh-7rem)] overflow-y-auto"
                data-testid="ds-portal-shell-sidenav"
              >
                {sideNav}
              </aside>
            ) : null}

            <div className="min-w-0">
              {pageTitle || subtitle || primaryActions || renderedLastActivity ? (
                <PageHeader
                  kicker={`${portalName} · ${portalRole}`}
                  title={pageTitle || platformDisplay}
                  description={subtitle}
                  actions={primaryActions}
                  meta={renderedLastActivity ? <span data-testid="ds-portal-shell-last-activity">{renderedLastActivity}</span> : null}
                  className="mb-4"
                  data-testid="ds-portal-shell-page-header"
                />
              ) : null}

              {alertSlot ? <div style={{ marginBottom: 16 }}>{alertSlot}</div> : null}

              <main data-testid="ds-portal-shell-content">{children}</main>
            </div>
          </div>
        </div>
      </section>

      {!hideProviderLine ? (
        <footer data-testid="ds-portal-shell-footer" className="border-t border-zinc-300 bg-white/90 py-3 mt-6">
          <div className="max-w-[1600px] mx-auto px-4 sm:px-6 flex items-center justify-between">
            <div className="wp16-kicker">{platformDisplay}</div>
            <ForgedOpsAttribution variant="login" />
          </div>
        </footer>
      ) : null}

      <MobileNavigation
        portalName={portalName}
        portalRole={portalRole}
        homeHref={homeHref}
        backHref={backHref}
        showHome={showHome}
        showBack={showBack}
        showSearch={showSearch}
        showNotifications={showNotifications}
        sideNav={sideNav}
      />
    </div>
  );
}

export default PortalShell;