import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";
import { registerThumbCache } from "@/lib/thumbCache";
import { initSentryIfConfigured } from "@/lib/sentryInit";
import { installPortalFetchAuth } from "@/lib/fetchPortalAuth";
import { installPortalAxiosAuth } from "@/lib/axiosPortalAuth";
import { installPortalXhrAuth } from "@/lib/xhrPortalAuth";
import { getDirectoryToken, getDirectoryUser } from "@/lib/directoryAuth";

// TRACK 15.39A · Suppress the benign "ResizeObserver loop completed with
// undelivered notifications" warning that Radix primitives (Select, Sheet,
// Dialog) emit during open/close animations. Without this, the CRA dev
// error overlay treats the warning as a fatal error and blocks all clicks
// — production builds don't have an overlay, so this guard is dev-only-
// visible but harmless in prod.
if (typeof window !== "undefined") {
  installPortalFetchAuth();
  installPortalAxiosAuth();
  installPortalXhrAuth();
  getDirectoryToken();
  const swallowResizeObserverLoop = (event) => {
    const msg = (event && (event.message || event.reason?.message)) || "";
    if (
      typeof msg === "string" &&
      msg.toLowerCase().includes("resizeobserver loop")
    ) {
      event.stopImmediatePropagation();
      event.preventDefault?.();
    }
  };
  window.addEventListener("error", swallowResizeObserverLoop);
  window.addEventListener("unhandledrejection", swallowResizeObserverLoop);
}

// Initialise Sentry as early as possible so the very first runtime error
// is captured. Env-gated — if REACT_APP_SENTRY_DSN is unset, this is a
// silent no-op. We fire-and-forget a /api/version fetch so the release
// tag matches the backend's source_hash; if it fails (offline, slow,
// API down) Sentry still initialises with release="unknown".
(async () => {
  let release;
  try {
    const apiBase = process.env.REACT_APP_BACKEND_URL || "";
    const r = await fetch(`${apiBase}/api/version`, { cache: "no-store" });
    if (r.ok) {
      const j = await r.json();
      release = j?.release;
    }
  } catch {
    /* swallow — Sentry will init with release="unknown" */
  }
  initSentryIfConfigured({ release });
})();

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

// Register the photo-thumbnail service worker (production HTTPS only).
// Failures are silent — the app still works with no SW, just no
// offline photo cache.
if (typeof window !== "undefined") {
  window.addEventListener("load", async () => {
    await registerThumbCache();
    // Re-establish the thumbnail cache principal for an already-signed-in
    // session (page reload / browser reopen). Fail-closed if none.
    try {
      const u = getDirectoryUser();
      setThumbCachePrincipal(u?.id || null);
    } catch { /* ignore */ }
  });
}
