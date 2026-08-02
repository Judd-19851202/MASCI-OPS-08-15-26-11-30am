import React from "react";
import { ChevronDown } from "lucide-react";
import { ForgedOpsAttribution } from "@/components/ForgedOpsAttribution";
import GlobalSearch from "@/components/GlobalSearch";
import NotificationBell from "@/components/NotificationBell";
import PortalSwitcher from "@/components/PortalSwitcher";
import { CanonicalHeader } from "@/components/CanonicalHeader";
import { HeaderIdentityProvider } from "@/components/header/HeaderIdentityContext";
import { SemanticIcon } from "@/components/icons/AppIcon";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { MobileNavigation } from "@/design-system/MobileNavigation";
import { useBranding } from "@/lib/BrandingProvider";
import { clearAllSessions } from "@/lib/sessionReset";
import { formatPlatformTimeOnly } from "@/lib/platformTime";
import { useT } from "@/lib/i18n";

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
  const { t } = useT();
  const isLightSurface = theme === "light";
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          type="button"
          className={`wp16-focus-ring inline-flex h-[var(--control-height-sm)] items-center gap-2 rounded-[var(--radius-control)] border px-3 text-xs font-semibold shadow-sm transition-[background-color,border-color,color] duration-[140ms] ${isLightSurface ? "border-slate-200 bg-white text-slate-900 hover:border-slate-300 hover:bg-slate-50" : "border-white/18 bg-white/10 text-white hover:bg-white/18"}`}
          data-testid={`${testIdPrefix}-trigger`}
        >
          <SemanticIcon name="hr" size="xs" className="opacity-70" />
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
            <div className="mt-1 text-sm font-semibold text-slate-100">{signedInName || t("Signed in")}</div>
            <div className="mt-2 inline-flex items-center gap-1.5 text-[11px] uppercase tracking-[0.14em] text-slate-300">
              <SemanticIcon name="workflow" size="xs" className="opacity-70" />
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
            <SemanticIcon name="signOut" size="xs" />
            {t("Sign out")}
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
  showPageHeader = true,
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
  const { t } = useT();
  const branding = useBranding();
  const platformDisplay = branding.platform_display_name || "Operations Platform";
  const platformShort = branding.platform_short_name || portalName;
  const renderedLastActivity = formatLastActivity(lastActivity);
  const clock = useLocalClock();
  const localTimeLabel = formatPlatformTimeOnly(clock);
  const signedInName = React.useMemo(() => resolveSignedInName(), []);
  const [headerIdentityOverride, setHeaderIdentityOverride] = React.useState(null);
  const theme = resolveShellTheme(shellTheme);
  const isAdminTheme = theme === "admin";
  const searchAccent = "light";
  const notificationAccent = "slate";
  const portalSwitcherVariant = "light";
  const isWp17 = experienceLevel === "wp17c";
  const localizedPortalRole = typeof portalRole === "string" ? t(portalRole) : portalRole;
  const localizedPageTitle = typeof pageTitle === "string" ? t(pageTitle) : pageTitle;
  const localizedSubtitle = typeof subtitle === "string" ? t(subtitle) : subtitle;
  const resolvedExperienceTone = resolveExperienceTone(experienceTone, localizedPortalRole, theme);
  const shouldShowHomeShortcut = false;
  const shouldShowBackShortcut = showBack && backHref;
  const rootClasses = [
    "wp16-shell min-h-screen flex flex-col",
    isAdminTheme ? "wp16-shell--admin" : "",
    isWp17 ? `wp17-shell wp17-shell--${resolvedExperienceTone}` : "",
    className,
  ].filter(Boolean).join(" ");
  const resolvedContextLabel = headerIdentityOverride?.pageLabel || localizedPageTitle || localizedPortalRole;
  const headerIdentityValue = React.useMemo(
    () => ({
      headerOwnsWorkflowIdentity: Boolean(resolvedContextLabel),
      pageTitle: resolvedContextLabel,
      portalLabel: localizedPortalRole,
      setHeaderIdentity: setHeaderIdentityOverride,
      clearHeaderIdentity: () => setHeaderIdentityOverride(null),
    }),
    [localizedPortalRole, resolvedContextLabel]
  );

  const handleSignOut = async () => {
    if (signOutCapability && signOutCapability.available !== true) return;
    if (typeof onSignOut === "function") {
      onSignOut();
      return;
    }
    await clearAllSessions();
    window.location.assign("/sign-in");
  };

  const utilityRail = (showSearch || showNotifications || showPortalSwitcher || showSignOut) ? (
    <div className="wp17-panel px-4 py-3 sm:px-5" data-testid="ds-portal-shell-utility-rail-card">
      <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
        {showSearch ? (
          <div className="min-w-0 xl:flex-1" data-testid="ds-portal-shell-search-rail">
            <GlobalSearch accent={searchAccent} className="w-full justify-between xl:w-auto" />
          </div>
        ) : null}

        <div className="flex flex-wrap items-center gap-2 xl:justify-end" data-testid="ds-portal-shell-utility-controls">
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
          {showSignOut ? (
            <ProfileMenu
              signedInName={signedInName}
              portalRole={localizedPortalRole}
              localTimeLabel={localTimeLabel}
              onSignOut={handleSignOut}
              disabled={!!signOutCapability && signOutCapability.available !== true}
              title={signOutCapability?.disabled_reason || t("Sign out")}
              theme="light"
            />
          ) : null}
        </div>
      </div>
    </div>
  ) : null;

  const hasWorkflowContext = Boolean(showPageHeader && (localizedSubtitle || primaryActions || renderedLastActivity));

  return (
    <div
      data-testid="ds-portal-shell"
      className={rootClasses}
    >
      <CanonicalHeader
        variant="platform"
        contextLabel={resolvedContextLabel}
        accent="blue"
        backTo={shouldShowBackShortcut ? backHref : null}
        backLabel={t("Back")}
        homeTo="/"
        showHomeLink={shouldShowHomeShortcut}
        showLangToggle
        utilitySlot={utilityRail}
        containerClassName="max-w-[var(--content-max-width)]"
        testIdPrefix="ds-portal-shell"
      />

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
              {hasWorkflowContext ? (
                <div className="wp16-shell-page-header wp16-shell-workflow-context" data-testid="ds-portal-shell-page-header">
                  <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                    <div className="min-w-0 flex-1">
                      {localizedSubtitle ? <p className="mt-2 max-w-[76ch] text-sm text-[color:var(--ink-soft)] sm:text-base">{localizedSubtitle}</p> : null}
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
              ) : null}

              {alertSlot ? <div className="mb-4">{alertSlot}</div> : null}
              <HeaderIdentityProvider value={headerIdentityValue}>
                <main data-testid="ds-portal-shell-content" className={isWp17 ? "wp17-shell-content" : undefined}>{children}</main>
              </HeaderIdentityProvider>
            </div>
          </div>
        </div>
      </section>

      <MobileNavigation
        portalName={portalName}
        portalRole={localizedPortalRole}
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