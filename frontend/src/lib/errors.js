// errors.js — iter340 · Shared operational-error sanitizer.
//
// One source of truth for converting axios catch-block errors into
// calm, operator-grade messages. NEVER leak raw FastAPI defaults
// ("Not Found", "Method Not Allowed", "Internal Server Error",
// "Unprocessable Entity") to operators — those look like the
// platform is broken even when the underlying cause is a transient
// deploy-skew window, an expired session, or a worker hiccup.
//
// Replaces the inline copy that lived in HrDailyReports.jsx (iter339).
//
// Usage:
//   import { operationalError } from "@/lib/errors";
//   ...
//   try { ... }
//   catch (e) {
//     toast.error(operationalError(e, t("Action unavailable. Try again in a moment."),
//                                   t("Your session expired. Please sign in again.")));
//   }

const RAW_FASTAPI_DEFAULTS = new Set([
  "Not Found",
  "Method Not Allowed",
  "Internal Server Error",
  "Unprocessable Entity",
  "Service Unavailable",
  "Bad Gateway",
  "Gateway Timeout",
]);

export function operationalError(e, fallback, expiredMsg) {
  const status = e?.response?.status;
  const detail = e?.response?.data?.detail;

  // 401 → session boundary. The active portal's token came back as
  // invalid/missing/expired; "session expired" is the right message.
  // TRACK 15.13H — 403 is NOT a session boundary. 403 means the user
  // is authenticated but the request resource is gated by a higher
  // role (e.g. HR hitting an admin-only audit endpoint, or a Shop
  // mechanic hitting an Asset-Admin-only Asset Care endpoint). We
  // now route 403 through the calm `fallback` copy so the operator
  // sees "temporarily unavailable" rather than a misleading
  // "session expired" — and so the FE does NOT bounce them out of
  // a perfectly valid session.
  if (status === 401 && expiredMsg) return expiredMsg;

  // 404 from a route that should exist = deploy-skew or stale build.
  if (status === 404) return fallback;

  // 403 → access denied; calm fallback. Keep the per-call message
  // so users understand the immediate context.
  if (status === 403) {
    if (detail && typeof detail === "string" && !RAW_FASTAPI_DEFAULTS.has(detail.trim())) {
      return detail.trim();
    }
    return fallback;
  }

  // 5xx (502/503/504/520) → platform unavailable; calm fallback.
  // TRACK 15.13H — explicitly map server-side errors to the
  // operator-grade fallback rather than letting them fall through
  // to an "expired session" prompt below.
  if (typeof status === "number" && status >= 500 && status <= 599) {
    return fallback;
  }

  // Network / CORS / timeout — no `response` at all.
  if (!e?.response) return fallback;

  // No detail string → fallback.
  if (!detail || typeof detail !== "string") return fallback;

  const stripped = detail.trim();
  // Suppress raw FastAPI / proxy defaults.
  if (RAW_FASTAPI_DEFAULTS.has(stripped)) return fallback;

  // Keep operator-authored 4xx messages (field validation, business
  // rule violations, etc.) — those carry useful information.
  return stripped;
}

export default operationalError;
