// TRUST-DIAGNOSTICS-001 · Shared error classification.
//
// One pure function, one canonical contract, one place to evolve the
// rules. Every loader that previously fell back to "0 records" or
// generic toasts now routes its failures through this classifier so
// the user sees the same precise message wherever the failure happens.
//
// Contract (see /app/memory/TRUST_DIAGNOSTICS_001_CERTIFICATION.md §3):
//
//   kind ∈ {
//     "session_expired",    // 401 — auth missing / expired
//     "access_restricted",  // 403 — permission denied
//     "network_unreachable",// fetch failed, ECONNABORTED, DNS, offline
//     "backend_unavailable",// 500/502/503/504
//     "success_empty",      // 2xx, but payload is empty
//     "success_loaded",     // 2xx, with data
//   }
//
// Each classification also carries:
//   status:        HTTP status or null
//   retryable:     true for network/5xx; false for 401/403
//   title, body:   user-facing strings (English; i18n is layered above)
//   action:        suggested next-step verb ("Log Back In" | "Retry" |
//                  "Dismiss" | null)
//
// The classifier is OFFLINE-aware. `navigator.onLine === false` is
// treated as `network_unreachable` even if axios reports an aborted
// upload.

const T = {
  SESSION_EXPIRED: "session_expired",
  ACCESS_RESTRICTED: "access_restricted",
  NETWORK_UNREACHABLE: "network_unreachable",
  BACKEND_UNAVAILABLE: "backend_unavailable",
  SUCCESS_EMPTY: "success_empty",
  SUCCESS_LOADED: "success_loaded",
};

export const ERROR_KINDS = T;

const COPY = {
  [T.SESSION_EXPIRED]: {
    title: "Session Expired",
    body: "Your login session has expired. No data has been lost. Please log back in to continue.",
    action: "Log Back In",
  },
  [T.ACCESS_RESTRICTED]: {
    title: "Access Restricted",
    body: "Your account does not have permission to view this area.",
    action: "Dismiss",
  },
  [T.NETWORK_UNREACHABLE]: {
    title: "Connection Problem",
    body: "Your device cannot reach MASCI services right now. Any drafts or pending uploads remain protected locally.",
    action: "Retry",
  },
  [T.BACKEND_UNAVAILABLE]: {
    title: "MASCI Services Temporarily Unavailable",
    body: "The server is reachable but returned an error. Try again shortly. Field drafts remain protected locally.",
    action: "Retry",
  },
};

function _decorate(kind, status, extra = {}) {
  const copy = COPY[kind] || { title: "", body: "", action: null };
  return {
    kind,
    status: status ?? null,
    retryable: kind === T.NETWORK_UNREACHABLE || kind === T.BACKEND_UNAVAILABLE,
    title: copy.title,
    body: copy.body,
    action: copy.action,
    ...extra,
  };
}

/**
 * Classify an axios / fetch rejection or a successful response.
 *
 * @param {unknown} errOrRes
 *   • axios error  — has .response.status (or no response = network fail)
 *   • Error        — generic Error from fetch / abort
 *   • Response-shaped {status, data} — for raw fetch callers
 *   • {ok:true, data} successful response
 * @param {{offline?: boolean, isEmpty?: (data:any)=>boolean}} [opts]
 */
export function classifyApiError(errOrRes, opts = {}) {
  const offline = opts.offline ?? (typeof navigator !== "undefined" && navigator.onLine === false);

  // --- Success path -------------------------------------------------
  // Callers can pass a successful response to ask "empty vs loaded?".
  if (errOrRes && typeof errOrRes === "object" && (errOrRes.ok === true || errOrRes.status === 200 || errOrRes.status === 204)) {
    const data = errOrRes.data;
    const isEmpty = typeof opts.isEmpty === "function"
      ? !!opts.isEmpty(data)
      : (data === null || data === undefined ||
         (Array.isArray(data) && data.length === 0) ||
         (typeof data === "object" && !Array.isArray(data) && Object.keys(data || {}).length === 0));
    return _decorate(isEmpty ? T.SUCCESS_EMPTY : T.SUCCESS_LOADED, errOrRes.status ?? 200);
  }

  // --- Failure path -------------------------------------------------
  // Offline takes precedence — the browser knows definitively.
  if (offline) return _decorate(T.NETWORK_UNREACHABLE, null, { reason: "navigator.onLine=false" });

  // Axios-style error
  if (errOrRes && typeof errOrRes === "object") {
    const status = errOrRes?.response?.status;
    const code = errOrRes?.code;

    if (status === 401) return _decorate(T.SESSION_EXPIRED, 401);
    if (status === 403) return _decorate(T.ACCESS_RESTRICTED, 403);
    if (typeof status === "number" && status >= 500 && status <= 599) {
      return _decorate(T.BACKEND_UNAVAILABLE, status);
    }

    // No response at all → network failure (DNS, dropped TCP, CORS pre-flight failure, timeout).
    const noResponse = !errOrRes.response;
    const isTimeout = code === "ECONNABORTED" || code === "ETIMEDOUT" || /timeout/i.test(String(errOrRes.message || ""));
    const isNetwork = code === "ERR_NETWORK" || code === "ENETUNREACH" || /network/i.test(String(errOrRes.message || ""));
    if (noResponse && (isTimeout || isNetwork || true)) {
      return _decorate(T.NETWORK_UNREACHABLE, null, { reason: isTimeout ? "timeout" : "no_response" });
    }

    // 4xx that isn't 401/403/timeout is a per-call client error — not a
    // platform-wide condition. We surface it as `null` so the global
    // overlay does NOT preempt. Callers are responsible for their own
    // local toasts in that case (e.g. 422 validation, 404 not found).
    if (typeof status === "number" && status >= 400 && status < 500) {
      return { kind: null, status, retryable: false, title: "", body: "", action: null };
    }
  }

  // Unknown — treat conservatively as network so we don't mask outages.
  return _decorate(T.NETWORK_UNREACHABLE, null, { reason: "unknown" });
}

export const _testing = { T, COPY };
