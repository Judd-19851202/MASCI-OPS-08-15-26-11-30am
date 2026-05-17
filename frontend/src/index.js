import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";
import { registerThumbCache } from "@/lib/thumbCache";
import { initSentryIfConfigured } from "@/lib/sentryInit";

// Initialise Sentry as early as possible so the very first runtime error
// is captured. Env-gated — if REACT_APP_SENTRY_DSN is unset, this is a
// silent no-op.
initSentryIfConfigured();

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
  window.addEventListener("load", () => {
    registerThumbCache();
  });
}
