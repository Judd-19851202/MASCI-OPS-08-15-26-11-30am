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
import React from "react";

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
  return null;
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
