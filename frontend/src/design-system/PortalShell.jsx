import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Clock, Home as HomeIcon, LogOut, MoreHorizontal, ChevronDown, User as UserIcon } from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { ForgedOpsAttribution } from "@/components/ForgedOpsAttribution";
import GlobalSearch from "@/components/GlobalSearch";
import NotificationBell from "@/components/NotificationBell";
import PortalSwitcher from "@/components/PortalSwitcher";
import { LangToggle } from "@/components/LangToggle";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { MobileNavigation } from "@/design-system/MobileNavigation";
import { useBranding } from "@/lib/BrandingProvider";
import { clearAllSessions } from "@/lib/sessionReset";
import { formatPlatformTimeOnly } from "@/lib/platformTime";

function resolveShellTheme(explicitTheme) {
  if (explicitTheme) return explicitTheme;
  if (typeof window !== "undefined" && window.location.pathname.startsWith("/admin")) {
    return "admin";
  }
  return "default";
}

function resolveExperienceTone(explicitTone, portalRole, theme) {
  if (explicitTone && explicitTone !== "default") return explicitTone;
  const role = String(portalRole || "").toLowerCase();
  if (theme === "admin" || role.includes("admin")) return "admin";
  if (role.includes("project")) return "pm";
  if (role.includes("human") || role === "hr") return "hr";
  if (role.includes("safety")) return "safety";
  if (role.includes("transport")) return "transportation";
  if (role.includes("dispatch")) return "dispatch";
  if (role.includes("shop")) return "shop";
  if (role.includes("field")) return "field";
  return "default";
}

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
      /* noop */
    }
  }

  return null;
}

function formatLastActivity(value) {
  if (value == null) return null;
  if (typeof value === "string") return value;
  if (value instanceof Date || typeof value === "number") {
    const date = value instanceof Date ? value : new Date(value);
    if (!Number.isNaN(date.getTime())) return `Updated ${formatPlatformTimeOnly(date)}`;
  }
  return value;
}

function TopActionLink({ to, label, icon: Icon, testId, theme = "default" }) {
  const classes = "border-white/18 bg-white/10 text-white hover:bg-white/18";

  return (
    <Link
      to={to}
      className={`wp16-focus-ring inline-flex h-[var(--control-height-sm)] items-center gap-1.5 rounded-[var(--radius-control)] border px-3 text-xs font-semibold uppercase tracking-[0.12em] shadow-sm transition-[background-color,border-color,color] duration-[140ms] ${classes}`}
      data-testid={testId}
    >
      <Icon className="h-3.5 w-3.5" />
      <span>{label}</span>
    </Link>
  );
}

function ProfileMenu({
  signedInName,
  portalRole,
  localTimeLabel,
  onSignOut,
  disabled,
  title,
  theme,
  testIdPrefix = "ds-portal-shell-profile",
}) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          type="button"
          className="wp16-focus-ring inline-flex h-[var(--control-height-sm)] items-center gap-2 rounded-[var(--radius-control)] border border-white/18 bg-white/10 px-3 text-xs font-semibold text-white shadow-sm transition-[background-color,border-color,color] duration-[140ms] hover:bg-white/18"
          data-testid={`${testIdPrefix}-trigger`}
        >
          <UserIcon className="h-3.5 w-3.5 opacity-70" />
          <span className="max-w-[10rem] truncate">{signedInName || portalRole}</span>
          <ChevronDown className="h-3.5 w-3.5 opacity-60" />
        </button>
      </PopoverTrigger>
      <PopoverContent
        align="end"
        sideOffset={8}
        className="elite-glass-modal w-[min(90vw,18rem)] border-white/16 bg-slate-950/92 p-3 text-slate-100"
        data-testid={`${testIdPrefix}-menu`}
      >
        <div className="space-y-3">
          <div>
            <div className="wp17-kicker text-slate-300">{portalRole}</div>
            <div className="mt-1 text-sm font-semibold text-slate-100">{signedInName || "Signed in"}</div>
            <div className="mt-2 inline-flex items-center gap-1.5 text-[11px] uppercase tracking-[0.14em] text-slate-300">
              <Clock className="h-3 w-3 opacity-70" />
              {localTimeLabel}
            </div>
          </div>
          <button
            type="button"
            onClick={onSignOut}
            disabled={disabled}
            title={title}
            className="wp16-focus-ring inline-flex min-h-[44px] w-full items-center justify-center gap-2 rounded-[var(--radius-control)] border border-white/14 bg-white/10 px-3 text-xs font-semibold uppercase tracking-[0.12em] text-white transition-[background-color,border-color,color,opacity] duration-[140ms] hover:bg-white/18 disabled:opacity-50"
            data-testid={`${testIdPrefix}-signout`}
          >
            <LogOut className="h-3.5 w-3.5" />
            Sign out
          </button>
        </div>
      </PopoverContent>
    </Popover>
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
  shellTheme = null,
  experienceLevel = "wp17c",
  experienceTone = "default",
  onSignOut = null,
  sideNav = null,
  children,
  className = "",
}) {
  const branding = useBranding();
  const platformDisplay = branding.platform_display_name || "Operations Platform";
  const platformShort = branding.platform_short_name || portalName;
  const renderedLastActivity = formatLastActivity(lastActivity);
  const clock = useLocalClock();
  const localTimeLabel = formatPlatformTimeOnly(clock);
  const signedInName = React.useMemo(() => resolveSignedInName(), []);
  const theme = resolveShellTheme(shellTheme);
  const isAdminTheme = theme === "admin";
  const searchAccent = "dark";
  const notificationAccent = "white";
  const portalSwitcherVariant = "dark";
  const langToggleVariant = "dark";
  const isWp17 = experienceLevel === "wp17c";
  const resolvedExperienceTone = resolveExperienceTone(experienceTone, portalRole, theme);
  const shouldShowHomeShortcut = showHome && !sideNav;
  const shouldShowBackShortcut = showBack && backHref && !sideNav;
  const rootClasses = [
    "wp16-shell min-h-screen flex flex-col",
    isAdminTheme ? "wp16-shell--admin" : "",
    isWp17 ? `wp17-shell wp17-shell--${resolvedExperienceTone}` : "",
    className,
  ].filter(Boolean).join(" ");
  const topControlClasses = "border-white/18 bg-white/10 text-slate-200";
  const mobileMoreButtonClasses = "border-white/18 bg-white/10 text-white";
  const mobilePopoverClasses = "elite-glass-modal w-[min(92vw,22rem)] border-white/16 bg-slate-950/92 p-3 text-slate-100";

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
      className={rootClasses}
    >
      <header data-testid="ds-portal-shell-header" className="app-sticky-header wp16-shell-header relative">
        <div className="mx-auto flex min-h-[var(--shell-header-height)] max-w-[var(--content-max-width)] items-center gap-3 px-3 py-3 sm:px-6">
          <div className="flex min-w-0 items-center gap-3">
            <MasciLogo variant="mark" size="md" className="hidden sm:block shrink-0" homeLink={homeHref} />
            <MasciLogo variant="mark" size="sm" className="sm:hidden shrink-0" homeLink={homeHref} />
            <div className="min-w-0">
              <div className="wp16-kicker" data-testid="ds-portal-shell-portal-name">
                {platformShort} · {portalRole}
              </div>
              {pageTitle ? (
                <div className="truncate text-sm font-semibold text-white" data-testid="ds-portal-shell-page-name">
                  {pageTitle}
                </div>
              ) : null}
            </div>
          </div>

          <div className="ml-auto hidden min-w-0 items-center gap-2 xl:flex">
            {showSearch ? (
              <div data-testid="ds-portal-shell-search">
                <GlobalSearch accent={searchAccent} />
              </div>
            ) : null}
            {showNotifications ? (
              <div data-testid="ds-portal-shell-notifications">
                <NotificationBell accent={notificationAccent} variant={isWp17 ? "wp17c" : "default"} />
              </div>
            ) : null}
            {showPortalSwitcher ? (
              <div data-testid="ds-portal-shell-portal-switcher">
                <PortalSwitcher current={portalSwitcherCurrent} variant={portalSwitcherVariant} />
              </div>
            ) : null}
            <div data-testid="ds-portal-shell-lang-toggle">
              <LangToggle variant={langToggleVariant} className="h-[var(--control-height-sm)]" />
            </div>
            {shouldShowBackShortcut ? <TopActionLink to={backHref} label="Back" icon={ArrowLeft} testId="ds-portal-shell-back" theme={theme} /> : null}
            {shouldShowHomeShortcut ? <TopActionLink to={homeHref} label="Home" icon={HomeIcon} testId="ds-portal-shell-home" theme={theme} /> : null}
            {showSignOut ? (
              <ProfileMenu
                signedInName={signedInName}
                portalRole={portalRole}
                localTimeLabel={localTimeLabel}
                onSignOut={handleSignOut}
                disabled={!!signOutCapability && signOutCapability.available !== true}
                title={signOutCapability?.disabled_reason || "Sign out"}
                theme={theme}
              />
            ) : null}
          </div>

          <div className="ml-auto flex items-center gap-2 xl:hidden">
            {showNotifications ? <NotificationBell accent={notificationAccent} variant={isWp17 ? "wp17c" : "default"} /> : null}
            <Popover>
              <PopoverTrigger asChild>
                <button
                  type="button"
                  className={`wp16-focus-ring inline-flex h-[var(--control-height-sm)] w-[var(--control-height-sm)] items-center justify-center rounded-[var(--radius-control)] border shadow-sm ${mobileMoreButtonClasses}`}
                  aria-label="More options"
                  data-testid="ds-portal-shell-mobile-more"
                >
                  <MoreHorizontal className="h-4 w-4" />
                </button>
              </PopoverTrigger>
              <PopoverContent align="end" sideOffset={8} className={mobilePopoverClasses} data-testid="ds-portal-shell-mobile-more-menu">
                <div className="flex flex-col gap-3">
                  <div>
                    <div className="wp16-kicker">{platformShort} · {portalRole}</div>
                    {signedInName ? (
                      <div className="mt-1 inline-flex items-center gap-1.5 text-sm font-semibold text-slate-100">
                        <UserIcon className="h-3.5 w-3.5 opacity-70" />
                        <span className="truncate">{signedInName}</span>
                      </div>
                    ) : null}
                    <div className="mt-2 inline-flex items-center gap-1.5 text-xs font-mono uppercase tracking-[0.14em] text-slate-300">
                      <Clock className="h-3 w-3 opacity-70" />
                      {localTimeLabel}
                    </div>
                  </div>

                  {showSearch ? (
                    <div data-testid="ds-portal-shell-mobile-search">
                      <GlobalSearch accent={searchAccent} className="w-full justify-center" />
                    </div>
                  ) : null}

                  <div className="flex flex-wrap items-center gap-2">
                    {showPortalSwitcher ? <PortalSwitcher current={portalSwitcherCurrent} variant={portalSwitcherVariant} className="w-full justify-center sm:w-auto" /> : null}
                    <LangToggle variant={langToggleVariant} className="h-[var(--control-height-sm)]" testId="ds-portal-shell-mobile-lang-toggle" />
                  </div>

                  <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                    {showBack && backHref ? <TopActionLink to={backHref} label="Back" icon={ArrowLeft} testId="ds-portal-shell-mobile-back" theme={theme} /> : null}
                    {showHome ? <TopActionLink to={homeHref} label="Home" icon={HomeIcon} testId="ds-portal-shell-mobile-home" theme={theme} /> : null}
                  </div>

                  {showSignOut ? (
                    <button
                      type="button"
                      onClick={handleSignOut}
                      disabled={!!signOutCapability && signOutCapability.available !== true}
                      className="wp16-focus-ring inline-flex min-h-[44px] items-center justify-center gap-2 rounded-[var(--radius-control)] border border-white/14 bg-white/10 px-3 text-xs font-semibold uppercase tracking-[0.12em] text-white transition-[background-color,border-color,color,opacity] duration-[140ms] hover:bg-white/18 disabled:opacity-50"
                      title={signOutCapability?.disabled_reason || "Sign out"}
                      data-testid="ds-portal-shell-mobile-signout"
                    >
                      <LogOut className="h-3.5 w-3.5" />
                      Sign out
                    </button>
                  ) : null}
                </div>
              </PopoverContent>
            </Popover>
          </div>
        </div>
      </header>

      <section className="wp16-shell-main wp16-mobile-safe flex-1">
        <div className="mx-auto max-w-[var(--content-max-width)] px-4 sm:px-6">
          <div className={sideNav ? "wp16-grid-columns--shell" : "min-w-0"}>
            {sideNav ? (
              <aside
                className="wp16-shell-sidebar hidden xl:block p-3"
                style={{ position: "sticky", top: "calc(var(--shell-header-height) + 1rem)", maxHeight: "calc(100dvh - var(--shell-header-height) - 1.5rem)", overflowY: "auto" }}
                data-testid="ds-portal-shell-sidenav"
              >
                {sideNav}
              </aside>
            ) : null}

            <div className="min-w-0">
              <div className="wp16-shell-page-header" data-testid="ds-portal-shell-page-header">
                <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                  <div className="min-w-0 flex-1">
                    <div className="wp16-kicker md:hidden" data-testid="ds-portal-shell-portal-name-mobile">
                      {platformShort} · {portalRole}
                    </div>
                    {pageTitle ? (
                      <h1
                        className="wp16-section-title text-4xl sm:text-5xl lg:text-6xl"
                        style={{ overflowWrap: "anywhere", wordBreak: "break-word" }}
                      >
                        {pageTitle}
                      </h1>
                    ) : null}
                    {subtitle ? <p className="mt-2 max-w-[76ch] text-sm text-[color:var(--ink-soft)] sm:text-base">{subtitle}</p> : null}
                  </div>

                  <div className="min-w-0 xl:max-w-[28rem] xl:text-right">
                    {primaryActions ? <div className="wp16-shell-actions justify-start xl:justify-end">{primaryActions}</div> : null}
                    {renderedLastActivity ? (
                      <aside className="mt-2 text-xs uppercase tracking-[0.14em] text-[color:var(--ink-soft)]" data-testid="ds-portal-shell-last-activity">
                        {renderedLastActivity}
                      </aside>
                    ) : null}
                  </div>
                </div>
              </div>

              {alertSlot ? <div className="mb-4">{alertSlot}</div> : null}
              <main data-testid="ds-portal-shell-content" className={isWp17 ? "wp17-shell-content" : undefined}>{children}</main>
            </div>
          </div>
        </div>
      </section>

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
        theme={theme}
        experienceLevel={experienceLevel}
        experienceTone={resolvedExperienceTone}
        data-testid="ds-portal-shell-mobile-navigation"
      />

      {!hideProviderLine ? (
        <footer data-testid="ds-portal-shell-footer" className={`mt-6 border-t border-[color:var(--border-hairline)] bg-white/80 py-3 ${isWp17 ? "wp17-shell-footer" : ""}`}>
          <div className="mx-auto flex max-w-[var(--content-max-width)] items-center justify-between gap-3 px-4 sm:px-6">
            <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-[color:var(--ink-soft)]">
              {platformDisplay}
            </div>
            <ForgedOpsAttribution variant="login" />
          </div>
        </footer>
      ) : null}
    </div>
  );
}

export default PortalShell;