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

  // 401 / 403 → session boundary, not a server defect.
  if ((status === 401 || status === 403) && expiredMsg) return expiredMsg;

  // 404 from a route that should exist = deploy-skew or stale build.
  if (status === 404) return fallback;

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
