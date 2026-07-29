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

  return (
    <div className={`lg:hidden fixed inset-x-0 bottom-0 z-40 wp16-bottom-dock ${className}`} data-testid={testId}>
      <div className="grid grid-cols-4 gap-2 px-3 py-2">
        <div className="flex justify-center">
          {showHome ? (
            <Link to={homeHref} className="wp16-focus-ring inline-flex h-12 w-full items-center justify-center gap-2 rounded-sm border border-zinc-300 bg-white text-xs font-semibold text-zinc-950" data-testid={`${testId}-home`}>
              <PlatformIcon name="home" className="h-4 w-4" />
              Home
            </Link>
          ) : showBack && backHref ? (
            <Link to={backHref} className="wp16-focus-ring inline-flex h-12 w-full items-center justify-center gap-2 rounded-sm border border-zinc-300 bg-white text-xs font-semibold text-zinc-950" data-testid={`${testId}-back`}>
              <PlatformIcon name="arrow-left" className="h-4 w-4" />
              Back
            </Link>
          ) : null}
        </div>
        <div className="flex justify-center">{showSearch ? <GlobalSearch accent="light" className="h-12 w-full justify-center" /> : <div />}</div>
        <div className="flex justify-center">{showNotifications ? <div className="flex h-12 w-full items-center justify-center rounded-sm border border-zinc-300 bg-white"><NotificationBell accent="slate" /></div> : <div />}</div>
        <div className="flex justify-center">
          {sideNav ? (
            <Sheet>
              <SheetTrigger asChild>
                <button type="button" className="wp16-focus-ring inline-flex h-12 w-full items-center justify-center gap-2 rounded-sm border border-zinc-300 bg-white text-xs font-semibold text-zinc-950" data-testid={`${testId}-menu`}>
                  <PlatformIcon name="menu" className="h-4 w-4" />
                  Modules
                </button>
              </SheetTrigger>
              <SheetContent side="bottom" className="h-[86vh] rounded-t-2xl border-zinc-300 bg-white p-0">
                <SheetHeader className="border-b border-zinc-200 px-5 py-4">
                  <SheetTitle className="font-display text-left text-2xl font-black tracking-tight text-zinc-950">{portalName} navigation</SheetTitle>
                  <SheetDescription className="text-left text-sm text-zinc-600">
                    {portalRole} modules and canonical destinations.
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