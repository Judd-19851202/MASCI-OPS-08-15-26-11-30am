import { useEffect } from "react";

/**
 * GlobalKeepalive
 * ---------------
 * Pings GET /api/health every 4 minutes from any open MASCI Hub tab, so the
 * production backend container never enters the long cold-sleep state that
 * causes the Cloudflare 520 on the user's first request after idle time.
 *
 * Why 4 minutes: Emergent native deploys idle workers around the 5-minute
 * mark. A 4-min ping + jitter beats the timer with margin.
 *
 * Mounted once in App.js. Renders nothing.
 */
const PING_MS = 4 * 60 * 1000;
const JITTER_MS = 30 * 1000;

export default function GlobalKeepalive() {
  useEffect(() => {
    const url = `${process.env.REACT_APP_BACKEND_URL}/api/health`;
    const ping = () => {
      // Fire-and-forget. Failures are silent — the actual user-facing API
      // calls have their own error handling (formatApiError).
      fetch(url, { method: "GET", cache: "no-store", credentials: "omit" }).catch(
        () => {}
      );
    };
    // First ping after page load (5 s after mount, jittered) to wake any
    // already-cold worker before the user clicks anything.
    const initial = setTimeout(ping, 5000 + Math.random() * 5000);
    // Recurring every PING_MS with ±30 s jitter so a fleet of tabs doesn't
    // hammer the worker simultaneously.
    const interval = setInterval(
      ping,
      PING_MS + (Math.random() * 2 - 1) * JITTER_MS
    );
    // Also ping on tab visibility change (laptop unsleep, phone foreground).
    const onVisible = () => {
      if (document.visibilityState === "visible") ping();
    };
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      clearTimeout(initial);
      clearInterval(interval);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, []);
  return null;
}
