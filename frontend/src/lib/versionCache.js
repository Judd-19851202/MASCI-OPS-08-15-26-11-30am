// versionCache.js — TRACK 14.0-RC1-FERRARI (2026-02-15).
//
// Tiny single-flight memoizer around GET /api/version. The endpoint
// returns essentially-immutable per-process data (release hash,
// app_env, uptime seconds). Without this cache, EnvBanner +
// BackendVersionBadge + index.js each fired their own fetch on every
// mount, so portal navigation produced ~3x /api/version hits per nav
// (~65 hits in 28s during iter509 stress test).
//
// Behavior:
//   - First call fetches and stores the promise.
//   - Subsequent callers within `VERSION_CACHE_TTL_MS` reuse the same
//     resolved value (or in-flight promise).
//   - After TTL the next caller re-fetches once. TTL is deliberately
//     long because the only field that changes meaningfully is
//     `uptime_seconds`, and a stale uptime by a few minutes is not a
//     trust issue.
//
// Doctrine:
//   - Failures are NOT cached; we let the next caller retry.
//   - Uses raw fetch (not the shared `api` instance) because the
//     /api/version endpoint is intentionally public — no token
//     headers, no interceptor. The skipSessionStatus story doesn't
//     apply.

const API = process.env.REACT_APP_BACKEND_URL;
const VERSION_CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes — uptime drift is fine

let _cached = null;        // last resolved {data, fetchedAt}
let _inflight = null;      // last unresolved Promise

export function fetchVersionCached() {
  // Reuse a still-fresh cached value.
  if (_cached && Date.now() - _cached.fetchedAt < VERSION_CACHE_TTL_MS) {
    return Promise.resolve(_cached.data);
  }
  // Reuse an in-flight request so 3 mounts within the same tick
  // share one network call.
  if (_inflight) return _inflight;
  _inflight = fetch(`${API}/api/version`, { cache: "no-store" })
    .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
    .then((data) => {
      _cached = { data, fetchedAt: Date.now() };
      _inflight = null;
      return data;
    })
    .catch((err) => {
      _inflight = null;          // do NOT cache failures
      throw err;
    });
  return _inflight;
}

// Test-only: reset the cache between unit tests.
export function _resetVersionCache() {
  _cached = null;
  _inflight = null;
}
