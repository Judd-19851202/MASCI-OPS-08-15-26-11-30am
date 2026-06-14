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
import { Home as HomeIcon, ArrowLeft, LogOut } from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { ForgedOpsAttribution } from "@/components/ForgedOpsAttribution";
import GlobalSearch from "@/components/GlobalSearch";
import NotificationBell from "@/components/NotificationBell";
import PortalSwitcher from "@/components/PortalSwitcher";

function formatLastActivity(value) {
  if (value == null) return null;
  if (typeof value === "string") {
    // Already a label like "Refreshed 2:14 PM"
    return value;
  }
  if (value instanceof Date || typeof value === "number") {
    const d = value instanceof Date ? value : new Date(value);
    if (!Number.isNaN(d.getTime())) {
      return `Updated ${d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}`;
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
  portalSwitcherCurrent = null,
  hideProviderLine = false,
  onSignOut = null,
  children,
  className = "",
}) {
  const renderedLastActivity = formatLastActivity(lastActivity);
  const handleSignOut = () => {
    if (typeof onSignOut === "function") {
      onSignOut();
      return;
    }
    try { localStorage.removeItem("masci_token"); } catch { /* noop */ }
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
        className="sticky top-0 z-30 bg-slate-900 border-b-4 border-red-700 shadow-md"
      >
        <div className="max-w-[1600px] mx-auto px-4 sm:px-6 py-2.5 flex items-center gap-3">
          {/* MASCI mark — anchors brand identity in every portal */}
          <MasciLogo variant="mark" size="md" className="hidden sm:block" homeLink={homeHref} />
          <MasciLogo variant="mark" size="sm" className="sm:hidden" homeLink={homeHref} />

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

          {/* Right-side nav cluster */}
          <div className="ml-auto flex items-center gap-2">
            {showBack && backHref && (
              <Link
                to={backHref}
                className="hidden sm:inline-flex items-center gap-1 px-2.5 h-9 rounded border border-slate-700 text-slate-200 hover:bg-slate-800 text-xs font-bold uppercase tracking-wide"
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
                className="inline-flex items-center gap-1 px-2.5 h-9 rounded border border-slate-700 text-slate-200 hover:bg-slate-800 text-xs font-bold uppercase tracking-wide"
                aria-label="Home"
                title="Home"
                data-testid="ds-portal-shell-home"
              >
                <HomeIcon className="w-3.5 h-3.5" /> <span className="hidden sm:inline">Home</span>
              </Link>
            )}
          </div>
        </div>
      </header>

      <section style={{ padding: "var(--pad-section)" }} className="flex-1">
        <div className="max-w-[1600px] mx-auto px-4 sm:px-6">
          <div className="flex items-start justify-between gap-4" style={{ marginBottom: 16 }}>
            <div>
              {/* Mobile-only portal kicker (already in header on desktop) */}
              <div
                className="md:hidden font-mono uppercase tracking-[0.18em] font-bold text-[10px] text-slate-500 mb-1"
                data-testid="ds-portal-shell-portal-name-mobile"
              >
                {portalName} · {portalRole}
              </div>
              {pageTitle && (
                <h1
                  style={{
                    fontSize: 28, fontWeight: 700, margin: 0,
                    color: "var(--ink-strong)", fontFamily: "var(--font-display)",
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
            <div className="flex flex-col items-end gap-2">
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
      </section>

      {!hideProviderLine && (
        <footer
          data-testid="ds-portal-shell-footer"
          className="border-t border-slate-200 bg-slate-50 py-3 mt-6"
        >
          <div className="max-w-[1600px] mx-auto px-4 sm:px-6 flex items-center justify-between">
            <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-slate-500">
              MASCI Operations Platform
            </div>
            <ForgedOpsAttribution variant="login" />
          </div>
        </footer>
      )}
    </div>
  );
}

export default PortalShell;
