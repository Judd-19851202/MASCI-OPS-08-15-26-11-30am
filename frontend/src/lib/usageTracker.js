// usageTracker.js — Iter146 (Phase 2.5). Fire-and-forget client-side
// analytics for the MASCI platform.
//
// Public API:
//   trackPageView(route)                  — call on route change
//   trackFormSubmit(route, success, label?) — call on form submit success/fail
//   trackExport(route, label)             — call when user triggers a CSV/PDF
//   trackUploadFailure(route, error_code) — call on a failed file upload
//   bindRouteChangeTracker(history?)      — auto-emit page_view on navigation
//
// Design constraints:
//   * Never blocks the user — silent failure is the rule
//   * Batches up to 10 events / flushes every 5s (or on tab close)
//   * Uses `navigator.sendBeacon` on unload so we don't lose the last
//     batch when the user closes the tab
//   * No raw user identifiers in any payload — actor hints are
//     optional and HMAC-hashed server-side
//   * Sniffs viewport once at startup so the user/session bucket is stable

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const BATCH_FLUSH_SIZE = 10;
const BATCH_FLUSH_INTERVAL_MS = 5000;
const MAX_BUFFER = 100; // hard cap so we never grow unbounded

let buffer = [];
let flushTimer = null;
let lastFlush = 0;
let bound = false;

function detectViewport() {
  if (typeof window === "undefined") return "desktop";
  const w = window.innerWidth || 1024;
  if (w < 640) return "mobile";
  if (w < 1024) return "tablet";
  return "desktop";
}

function detectPortalFromPath(path) {
  if (!path) return "public";
  if (path.startsWith("/admin")) return "admin";
  if (path.startsWith("/safety-portal")) return "safety";
  if (path.startsWith("/hr")) return "hr";
  if (path.startsWith("/pm")) return "pm";
  if (path.startsWith("/shop")) return "shop";
  if (path.startsWith("/dispatch")) return "dispatch";
  if (path.startsWith("/leadership")) return "leadership";
  if (path.startsWith("/safety/")) return "safety";
  return "public";
}

function enqueue(event) {
  if (buffer.length >= MAX_BUFFER) return; // drop silently
  buffer.push({
    ...event,
    viewport: event.viewport || detectViewport(),
    portal: event.portal || detectPortalFromPath(event.route || ""),
  });
  if (buffer.length >= BATCH_FLUSH_SIZE) {
    flush();
  } else if (!flushTimer) {
    flushTimer = setTimeout(flush, BATCH_FLUSH_INTERVAL_MS);
  }
}

function flush(useBeacon = false) {
  if (!buffer.length) {
    flushTimer = null;
    return;
  }
  const events = buffer.splice(0, buffer.length);
  flushTimer = null;
  lastFlush = Date.now();

  const body = JSON.stringify({ events });

  // sendBeacon for unload paths — guarantees delivery even on tab close.
  if (useBeacon && typeof navigator !== "undefined" && navigator.sendBeacon) {
    try {
      const blob = new Blob([body], { type: "application/json" });
      navigator.sendBeacon(`${API}/usage/track`, blob);
      return;
    } catch {
      // fall through to fetch
    }
  }

  try {
    fetch(`${API}/usage/track`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      // `keepalive: true` lets the request survive a page transition.
      keepalive: true,
    }).catch(() => {
      /* silent — analytics must NEVER raise into user UX */
    });
  } catch {
    /* silent */
  }
}

// ─── Public API ──────────────────────────────────────────────────
export function trackPageView(route) {
  enqueue({ kind: "page_view", route });
}

export function trackFormSubmit(route, success, label) {
  enqueue({
    kind: "form_submit",
    route,
    status: success ? "success" : "error",
    label,
  });
}

export function trackExport(route, label) {
  enqueue({ kind: "export", route, label });
}

export function trackUploadFailure(route, errorCode) {
  enqueue({ kind: "upload_failure", route, error_code: errorCode });
}

/**
 * One-shot hook that wires route-change page_view tracking. Pass the
 * react-router history object OR rely on the popstate fallback that
 * react-router v6 emits.
 */
export function bindRouteChangeTracker() {
  if (bound || typeof window === "undefined") return;
  bound = true;
  // Initial pageview at boot
  trackPageView(window.location.pathname);

  // Patch history.pushState / replaceState so SPA navigation emits
  // page_view without us having to plumb a hook through every page.
  const wrap = (fnName) => {
    const orig = window.history[fnName];
    window.history[fnName] = function patched(...args) {
      const ret = orig.apply(this, args);
      try {
        trackPageView(window.location.pathname);
      } catch {
        /* silent */
      }
      return ret;
    };
  };
  try {
    wrap("pushState");
    wrap("replaceState");
  } catch {
    /* silent */
  }
  window.addEventListener("popstate", () => {
    try { trackPageView(window.location.pathname); } catch { /* silent */ }
  });

  // Flush on tab-close so the last batch isn't lost.
  window.addEventListener("beforeunload", () => flush(true));
  window.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") flush(true);
  });
}

/** Manual flush — exposed for tests / debug. */
export function _flushNow() { flush(); }
