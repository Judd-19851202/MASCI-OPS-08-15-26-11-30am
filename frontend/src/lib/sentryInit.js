// sentryInit.js — env-gated Sentry initialization for the React frontend.
//
// Mirror of /app/backend/sentry_init.py:
//   * Init only when REACT_APP_SENTRY_DSN is set (no DSN → no-op, no errors).
//   * Release tagged with REACT_APP_RELEASE (we set this from the backend's
//     /api/version `release` value at app boot — see App.js).
//   * Environment from REACT_APP_SENTRY_ENV, defaulting to "production".
//   * Auth tokens, cookies, password fields scrubbed from breadcrumbs and
//     event payloads.
//   * Release-health enabled (autoSessionTracking).
//
// Public surface:
//     initSentryIfConfigured({ release } = {})  → boolean
//     captureException(err, ctx)                → safe wrapper, no-op if uninit

let _initialized = false;
let _sentry = null;

// Patterns we never want to send to Sentry — paranoia + speed.
const PII_KEY_RX = /(password|secret|token|api[_-]?key|bearer|private[_-]?key|session|cookie|auth)/i;

function _scrubValue(v) {
  if (v && typeof v === "object" && !Array.isArray(v)) {
    const out = {};
    for (const k of Object.keys(v)) {
      out[k] = PII_KEY_RX.test(k) ? "***SCRUBBED***" : _scrubValue(v[k]);
    }
    return out;
  }
  if (Array.isArray(v)) return v.map(_scrubValue);
  return v;
}

function _beforeSend(event /* , hint */) {
  try {
    if (event.request) {
      if (event.request.headers) {
        for (const h of Object.keys(event.request.headers)) {
          if (PII_KEY_RX.test(h)) event.request.headers[h] = "***SCRUBBED***";
        }
      }
      if (event.request.cookies) event.request.cookies = "***SCRUBBED***";
      if (event.request.data && typeof event.request.data === "object") {
        event.request.data = _scrubValue(event.request.data);
      }
      if (event.request.query_string && typeof event.request.query_string === "object") {
        event.request.query_string = _scrubValue(event.request.query_string);
      }
    }
    if (event.extra && typeof event.extra === "object") event.extra = _scrubValue(event.extra);
    if (event.contexts && typeof event.contexts === "object") {
      event.contexts = _scrubValue(event.contexts);
    }
    // Strip HMAC-shaped 40+ char hex blobs from log messages.
    if (event.message && typeof event.message === "string") {
      event.message = event.message.replace(/[a-f0-9]{40,}/g, "***SCRUBBED***");
    }
  } catch {
    /* never let the scrubber crash the event */
  }
  return event;
}

function _beforeBreadcrumb(breadcrumb /* , hint */) {
  try {
    if (breadcrumb && breadcrumb.data && typeof breadcrumb.data === "object") {
      breadcrumb.data = _scrubValue(breadcrumb.data);
    }
  } catch {
    /* swallow */
  }
  return breadcrumb;
}

export async function initSentryIfConfigured({ release } = {}) {
  if (_initialized) return true;
  const dsn = process.env.REACT_APP_SENTRY_DSN;
  if (!dsn) return false; // No DSN → no-op.

  let Sentry;
  try {
    Sentry = await import(/* webpackChunkName: "sentry" */ "@sentry/react");
  } catch {
    // sentry-sdk not installed yet → silent. The package is added at build
    // time; if it's missing, we simply don't initialise.
    return false;
  }

  const env =
    process.env.REACT_APP_SENTRY_ENV ||
    process.env.REACT_APP_ENV ||
    "production";

  const tracesRate = parseFloat(process.env.REACT_APP_SENTRY_TRACES_RATE || "0");
  const replayRate = parseFloat(process.env.REACT_APP_SENTRY_REPLAY_RATE || "0");

  try {
    Sentry.init({
      dsn,
      environment: env,
      release: release || process.env.REACT_APP_RELEASE || "unknown",
      autoSessionTracking: true,
      tracesSampleRate: isNaN(tracesRate) ? 0 : tracesRate,
      replaysSessionSampleRate: isNaN(replayRate) ? 0 : replayRate,
      replaysOnErrorSampleRate: isNaN(replayRate) ? 0 : Math.max(replayRate, 0.1),
      beforeSend: _beforeSend,
      beforeBreadcrumb: _beforeBreadcrumb,
      // Sensitive elements masked by default in any future Replay capture.
      sendDefaultPii: false,
    });
    Sentry.setTag("platform", "masci-hub");
    Sentry.setTag("component", "frontend");
    _sentry = Sentry;
    _initialized = true;
    if (process.env.NODE_ENV !== "production") {
      // eslint-disable-next-line no-console
      console.info("[sentry] initialised", { env, release });
    }
    return true;
  } catch (err) {
    // Never let Sentry init blow up the app.
    // eslint-disable-next-line no-console
    console.warn("[sentry] init failed (non-fatal):", err);
    return false;
  }
}

export function captureException(err, ctx) {
  if (!_initialized || !_sentry) return;
  try {
    _sentry.captureException(err, ctx ? { extra: ctx } : undefined);
  } catch {
    /* never throw from instrumentation */
  }
}

export function isInitialized() {
  return _initialized;
}
