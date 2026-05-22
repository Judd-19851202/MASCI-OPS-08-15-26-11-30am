// captureMode.js — iter347 (Capture Mode)
//
// Tiny utility that lets MASCI append `?capture=1` to any platform URL
// and instantly get a clean-chrome surface for cinematic screen capture:
//   • BannerStrip → returns null (Memorial Day, holiday, advisory, etc.)
//   • BackendStatusBanner → returns null (no "Server reconnecting…" toast)
//   • PersistenceHealthBanner → returns null (no admin-only health alerts)
//
// Sticky for the duration of the tab: once enabled via `?capture=1`,
// stays on until the tab is closed or `?capture=0` is appended.
//
// Footprint when not in capture mode: ZERO. Hook returns false instantly.
const STORAGE_KEY = "masci.captureMode";

export function isCaptureMode() {
  if (typeof window === "undefined") return false;
  // URL param wins — read every call so a fresh nav can toggle.
  try {
    const sp = new URLSearchParams(window.location.search);
    const v = sp.get("capture");
    if (v === "1" || v === "true") {
      window.sessionStorage.setItem(STORAGE_KEY, "1");
      return true;
    }
    if (v === "0" || v === "false") {
      window.sessionStorage.removeItem(STORAGE_KEY);
      return false;
    }
  } catch (_e) {
    /* SSR / sandboxed iframe */
  }
  // Falls back to sticky session flag so route changes inside the same
  // tab keep capture mode on without re-appending the query string.
  try {
    return window.sessionStorage.getItem(STORAGE_KEY) === "1";
  } catch (_e) {
    return false;
  }
}

/**
 * React hook variant — re-renders the consumer whenever the location
 * changes so capture mode picks up `?capture=1` on the very first paint.
 */
import { useEffect, useState } from "react";

export function useCaptureMode() {
  const [on, setOn] = useState(() => isCaptureMode());
  useEffect(() => {
    // Poll on every microtask after mount to catch route changes that
    // don't fire popstate (react-router's pushState).
    const onPop = () => setOn(isCaptureMode());
    window.addEventListener("popstate", onPop);
    // Also recheck once on mount in case the URL param landed AFTER the
    // initial render (rare but possible with deep links).
    onPop();
    return () => window.removeEventListener("popstate", onPop);
  }, []);
  return on;
}
