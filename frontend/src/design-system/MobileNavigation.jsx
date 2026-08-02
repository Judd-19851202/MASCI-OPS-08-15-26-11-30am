import React from "react";
import { Link } from "react-router-dom";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import GlobalSearch from "@/components/GlobalSearch";
import NotificationBell from "@/components/NotificationBell";
import { PlatformIcon } from "./icons";
import { useT } from "@/lib/i18n";

export function MobileNavigation({
  portalName,
  portalRole,
  homeHref = "/",
  backHref = null,
  showHome = true,
  showBack = false,
  showSearch = true,
  showNotifications = true,
  sideNav = null,
  theme = "default",
  experienceLevel = null,
  experienceTone = "default",
  className = "",
  "data-testid": testId = "ds-mobile-navigation",
}) {
  const { t } = useT();
  if (!showHome && !showBack && !showSearch && !showNotifications && !sideNav) return null;

  const isAdminTheme = theme === "admin";
  const isWp17 = experienceLevel === "wp17c";
  const navButtonClasses = isAdminTheme
    ? "wp16-focus-ring inline-flex min-h-[48px] w-full items-center justify-center gap-2 rounded-[var(--radius-control)] border border-slate-700 bg-slate-900/18 px-3 text-xs font-semibold uppercase tracking-[0.12em] text-slate-100 shadow-sm transition-[background-color,border-color,color] duration-[140ms] hover:bg-slate-800/42"
    : "wp16-focus-ring inline-flex min-h-[48px] w-full items-center justify-center gap-2 rounded-[var(--radius-control)] border border-[color:var(--border-bold)] bg-white px-3 text-xs font-semibold uppercase tracking-[0.12em] text-[color:var(--ink-strong)] shadow-sm transition-[background-color,border-color,color] duration-[140ms] hover:bg-[color:var(--paper-card-muted)]";

  return (
    <div className={`xl:hidden fixed inset-x-0 bottom-0 z-40 wp16-bottom-dock ${isWp17 ? `wp17-mobile-dock wp17-mobile-dock--${experienceTone}` : ""} ${className}`} data-testid={testId}>
      <div className="grid grid-cols-4 gap-2 px-3 py-2.5" style={{ paddingBottom: "calc(0.625rem + env(safe-area-inset-bottom, 0px))" }}>
        <div className="flex justify-center">
          {showHome ? (
            <Link to={homeHref} className={navButtonClasses} data-testid={`${testId}-home`}>
              <PlatformIcon name="home" className="h-4 w-4" />
              {t("Home")}
            </Link>
          ) : showBack && backHref ? (
            <Link to={backHref} className={navButtonClasses} data-testid={`${testId}-back`}>
              <PlatformIcon name="arrow-left" className="h-4 w-4" />
              {t("Back")}
            </Link>
          ) : null}
        </div>
        <div className="flex justify-center">
          {showSearch ? <GlobalSearch accent={isAdminTheme ? "dark" : "light"} className="h-12 w-full justify-center" /> : <div />}
        </div>
        <div className="flex justify-center">
          {showNotifications ? (
            <div className={`flex h-12 w-full items-center justify-center rounded-[var(--radius-control)] border shadow-sm ${isAdminTheme ? "border-slate-700 bg-slate-900/18" : "border-[color:var(--border-bold)] bg-white"}`}>
              <NotificationBell accent={isAdminTheme ? "white" : "slate"} variant={isWp17 ? "wp17c" : "default"} />
            </div>
          ) : <div />}
        </div>
        <div className="flex justify-center">
          {sideNav ? (
            <Sheet>
              <SheetTrigger asChild>
                <button type="button" className={navButtonClasses} data-testid={`${testId}-menu`}>
                  <PlatformIcon name="menu" className="h-4 w-4" />
                  {t("Modules")}
                </button>
              </SheetTrigger>
              <SheetContent
                side="bottom"
                className={`flex h-[86dvh] max-h-[calc(100dvh-0.5rem)] min-h-0 flex-col overflow-hidden rounded-t-[1.5rem] p-0 ${isAdminTheme ? "border-slate-800 bg-slate-950 text-slate-100" : ""} ${isWp17 ? "wp17-mobile-sheet" : ""}`}
                data-testid={`${testId}-menu-sheet-frame`}
              >
                <SheetHeader
                  className={`shrink-0 border-b px-5 pb-4 pt-[calc(1rem+env(safe-area-inset-top,0px))] ${isAdminTheme ? "border-slate-800" : "border-[color:var(--border-hairline)]"}`}
                >
                  <SheetTitle className={`text-left font-display text-2xl font-black tracking-tight ${isAdminTheme ? "text-slate-100" : "text-[color:var(--ink-strong)]"}`}>
                    {portalName} {t("navigation")}
                  </SheetTitle>
                  <SheetDescription className={`text-left text-sm ${isAdminTheme ? "text-slate-300" : "text-[color:var(--ink-soft)]"}`}>
                    {portalRole} {t("modules and shared destinations.")}
                  </SheetDescription>
                </SheetHeader>
                <div
                  className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-4 py-4"
                  data-testid={`${testId}-menu-sheet`}
                  style={{
                    WebkitOverflowScrolling: "touch",
                    overscrollBehavior: "contain",
                    touchAction: "pan-y",
                    paddingBottom: "calc(1rem + env(safe-area-inset-bottom, 0px))",
                  }}
                >
                  {sideNav}
                </div>
              </SheetContent>
            </Sheet>
          ) : null}
        </div>
      </div>
    </div>
  );
}

export default MobileNavigation;