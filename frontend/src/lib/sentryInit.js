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

function _beforeSend(event, hint) {
  try {
    // Track 15.13A · Sentry noise suppression for transient network errors.
    // AxiosError "Network Error" / ERR_NETWORK fires whenever:
    //   * Safari suspends a background tab mid-fetch,
    //   * backend cold-start returns 520 before the worker is hot,
    //   * an in-flight request is aborted by a route change.
    // The session-status bus already classifies these as
    // NETWORK_UNREACHABLE and renders a calm in-app banner — bubbling
    // the underlying AxiosError to Sentry on top of that is pure noise
    // (the user already sees the right message). Drop these events at
    // the gateway. Real backend 5xx / 4xx still flow through because
    // those carry `err.response.status` and are classified above.
    const origErr = hint && hint.originalException;
    if (origErr && typeof origErr === "object") {
      const code = origErr.code;
      const name = origErr.name;
      const message = String(origErr.message || "");
      const noResponse = !origErr.response;
      const isAxios = origErr.isAxiosError === true || name === "AxiosError";
      const isCanceled =
        code === "ERR_CANCELED" ||
        name === "CanceledError" ||
        name === "AbortError" ||
        /canceled|aborted/i.test(message);
      const isNetwork =
        code === "ERR_NETWORK" ||
        code === "ENETUNREACH" ||
        /network error/i.test(message);
      const isTimeout =
        code === "ECONNABORTED" ||
        code === "ETIMEDOUT" ||
        /timeout/i.test(message);
      if (isAxios && noResponse && (isCanceled || isNetwork || isTimeout)) {
        return null; // suppress — already surfaced as a banner in-app
      }
    }
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

  // Environment auto-detection (Phase 2 production cutover hardening).
  //
  // Order of precedence:
  //   1. Explicit REACT_APP_SENTRY_ENV env var if set (operator override).
  //   2. Legacy REACT_APP_ENV env var if set.
  //   3. window.location.hostname — runtime hostname is the most
  //      reliable production signal. If the hostname contains
  //      "preview" (Emergent preview pods) or matches "localhost",
  //      tag as "preview". Otherwise → "production".
  //   4. Default to "production".
  //
  // This means a single build works for both surfaces: preview pods
  // auto-tag preview events, production deploys auto-tag production
  // events. No operator flip required before deploy.
  let env;
  if (process.env.REACT_APP_SENTRY_ENV) {
    env = process.env.REACT_APP_SENTRY_ENV;
  } else if (process.env.REACT_APP_ENV) {
    env = process.env.REACT_APP_ENV;
  } else if (
    typeof window !== "undefined" &&
    window.location &&
    window.location.hostname
  ) {
    const h = window.location.hostname;
    env =
      h.includes("preview") || h === "localhost" || h === "127.0.0.1"
        ? "preview"
        : "production";
  } else {
    env = "production";
  }

  const tracesRate = parseFloat(process.env.REACT_APP_SENTRY_TRACES_RATE || "0");
  const replayRate = parseFloat(process.env.REACT_APP_SENTRY_REPLAY_RATE || "0");
  // Per operator directive 2026-02-XX (Phase 2 production cutover):
  // keep Sentry lightweight — errors + exceptions + release visibility
  // only. Tracing and Session Replay are explicitly OFF. Both rates
  // honour the env var verbatim; no floor is applied, so leaving the
  // var unset (or setting it to 0) means truly zero traces / replays.
  const safeTracesRate = isNaN(tracesRate) ? 0 : Math.max(0, Math.min(1, tracesRate));
  const safeReplayRate = isNaN(replayRate) ? 0 : Math.max(0, Math.min(1, replayRate));

  try {
    Sentry.init({
      dsn,
      environment: env,
      release: release || process.env.REACT_APP_RELEASE || "unknown",
      autoSessionTracking: true,
      tracesSampleRate: safeTracesRate,
      replaysSessionSampleRate: safeReplayRate,
      replaysOnErrorSampleRate: safeReplayRate,
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
