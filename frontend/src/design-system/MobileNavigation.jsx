import React from "react";
import { Link } from "react-router-dom";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import GlobalSearch from "@/components/GlobalSearch";
import NotificationBell from "@/components/NotificationBell";
import { PlatformIcon } from "./icons";

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
  className = "",
  "data-testid": testId = "ds-mobile-navigation",
}) {
  if (!showHome && !showBack && !showSearch && !showNotifications && !sideNav) return null;

  const navButtonClasses = "wp16-focus-ring inline-flex min-h-[48px] w-full items-center justify-center gap-2 rounded-[var(--radius-control)] border border-[color:var(--border-bold)] bg-white px-3 text-xs font-semibold uppercase tracking-[0.12em] text-[color:var(--ink-strong)] shadow-sm transition-[background-color,border-color,color] duration-[140ms] hover:bg-[color:var(--paper-card-muted)]";

  return (
    <div className={`lg:hidden fixed inset-x-0 bottom-0 z-40 wp16-bottom-dock ${className}`} data-testid={testId}>
      <div className="grid grid-cols-4 gap-2 px-3 py-2.5" style={{ paddingBottom: "calc(0.625rem + env(safe-area-inset-bottom, 0px))" }}>
        <div className="flex justify-center">
          {showHome ? (
            <Link to={homeHref} className={navButtonClasses} data-testid={`${testId}-home`}>
              <PlatformIcon name="home" className="h-4 w-4" />
              Home
            </Link>
          ) : showBack && backHref ? (
            <Link to={backHref} className={navButtonClasses} data-testid={`${testId}-back`}>
              <PlatformIcon name="arrow-left" className="h-4 w-4" />
              Back
            </Link>
          ) : null}
        </div>
        <div className="flex justify-center">
          {showSearch ? <GlobalSearch accent="light" className="h-12 w-full justify-center" /> : <div />}
        </div>
        <div className="flex justify-center">
          {showNotifications ? (
            <div className="flex h-12 w-full items-center justify-center rounded-[var(--radius-control)] border border-[color:var(--border-bold)] bg-white shadow-sm">
              <NotificationBell accent="slate" />
            </div>
          ) : <div />}
        </div>
        <div className="flex justify-center">
          {sideNav ? (
            <Sheet>
              <SheetTrigger asChild>
                <button type="button" className={navButtonClasses} data-testid={`${testId}-menu`}>
                  <PlatformIcon name="menu" className="h-4 w-4" />
                  Modules
                </button>
              </SheetTrigger>
              <SheetContent side="bottom" className="h-[86dvh] rounded-t-[1.5rem] p-0" data-testid={`${testId}-menu-sheet-frame`}>
                <SheetHeader className="border-b border-[color:var(--border-hairline)] px-5 py-4">
                  <SheetTitle className="text-left font-display text-2xl font-black tracking-tight text-[color:var(--ink-strong)]">
                    {portalName} navigation
                  </SheetTitle>
                  <SheetDescription className="text-left text-sm text-[color:var(--ink-soft)]">
                    {portalRole} modules and shared destinations.
                  </SheetDescription>
                </SheetHeader>
                <div className="overflow-y-auto px-4 py-4" data-testid={`${testId}-menu-sheet`}>
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