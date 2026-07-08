// TRACK 25.01 · LegacyMovedBanner — Phase B rollout affordance.
//
// Renders a persistent, non-blocking banner at the top of legacy admin
// pages that have been consolidated into the Operations Control Center.
// The original page STILL RENDERS below the banner — this is a
// zero-drift move (no routes deleted, no functionality lost).
//
// Operators see:
//   - What page they're on today
//   - Where the canonical home now lives
//   - Why the move helps them
//   - A one-click deep-link into the new home
//
// The banner is dismissible for the current session (per-tab). Any
// future visit re-shows the banner until Phase E sunsets the legacy
// route entirely.
import React, { useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { lookupLegacyRoute } from "@/app/routing/legacyRedirects";

const SESSION_KEY_PREFIX = "masci.aos.banner.dismissed:";

function isDismissedForRoute(pathname) {
  try {
    return (
      typeof window !== "undefined" &&
      window.sessionStorage &&
      window.sessionStorage.getItem(SESSION_KEY_PREFIX + pathname) === "1"
    );
  } catch (_e) {
    return false;
  }
}

function markDismissed(pathname) {
  try {
    if (typeof window !== "undefined" && window.sessionStorage) {
      window.sessionStorage.setItem(SESSION_KEY_PREFIX + pathname, "1");
    }
  } catch (_e) {
    /* no-op */
  }
}

export function LegacyMovedBanner({ pathname }) {
  const location = useLocation();
  const navigate = useNavigate();
  const activePath = pathname || location.pathname;
  const entry = useMemo(() => lookupLegacyRoute(activePath), [activePath]);
  const [dismissed, setDismissed] = useState(() =>
    isDismissedForRoute(activePath),
  );

  if (!entry) return null;
  if (dismissed) return null;

  const openCanonical = () => {
    navigate(entry.canonical);
  };

  const dismiss = () => {
    markDismissed(activePath);
    setDismissed(true);
  };

  return (
    <div
      role="status"
      className="w-full border-b border-amber-300 bg-amber-50"
      data-testid="legacy-moved-banner"
      data-legacy-path={activePath}
      data-canonical-path={entry.canonical}
    >
      <div className="mx-auto max-w-7xl px-4 py-3 sm:py-2 flex flex-col sm:flex-row sm:items-center gap-2">
        <div className="min-w-0 flex-1">
          <div className="text-xs font-semibold uppercase tracking-widest text-amber-800">
            This page has moved
          </div>
          <div className="mt-0.5 text-sm text-amber-900">
            <span className="font-semibold">
              {entry.canonicalTitle || "Operations Control Center"}
            </span>{" "}
            is the new home.{" "}
            <span className="text-amber-800">{entry.reason}</span>
          </div>
          <div className="mt-1 text-[11px] text-amber-800/80">
            This URL will keep working during the transition — no
            bookmarks broken.
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={openCanonical}
            className="rounded-md border border-amber-600 bg-amber-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-amber-700"
            data-testid="legacy-moved-banner-open-canonical"
          >
            Open in Operations Control Center
          </button>
          <button
            type="button"
            onClick={dismiss}
            className="rounded-md border border-amber-300 bg-white px-2 py-1.5 text-xs font-medium text-amber-900 hover:bg-amber-100"
            data-testid="legacy-moved-banner-dismiss"
            aria-label="Dismiss for this session"
          >
            Dismiss
          </button>
        </div>
      </div>
    </div>
  );
}

// Wrapper that prepends the banner in front of the legacy page's own
// content. Used by AppRoutes.jsx so we don't have to edit every legacy
// page.
export function WithLegacyBanner({ children, pathname }) {
  return (
    <div data-testid="legacy-moved-shell">
      <LegacyMovedBanner pathname={pathname} />
      {children}
    </div>
  );
}

export default LegacyMovedBanner;
