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

function publishFrontendReleaseIdentity(data) {
  if (typeof window === "undefined") return;
  window.__MASCI_RELEASE_IDENTITY__ = {
    version: data?.frontend_build_version || data?.release || null,
    commit: data?.frontend_build_commit || data?.commit || null,
    commit_source: data?.frontend_build_commit_source || data?.commit_source || null,
    source_hash: data?.frontend_build_source_hash || data?.source_hash || null,
    built_at: data?.frontend_build_built_at || data?.built_at || null,
    workspace_dirty: Boolean(data?.frontend_workspace_dirty ?? data?.workspace_dirty),
    identity_mode: data?.frontend_identity_mode || "runtime-api-version",
    identity_endpoint: data?.frontend_identity_endpoint || "/api/version",
  };
}

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
      publishFrontendReleaseIdentity(data);
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

// SHARED release-identity owner: derive the human-visible production SHA
// from the AUTHORITATIVE deployable provenance (authorized_saved_sha) — the
// genuine saved Git SHA. It MUST never fall back to the demoted workspace
// diagnostic manifest hash (`commit`/`source_hash`), which is diagnostic-only
// and must not be labelled as the production SHA/build.
// Returns a short (8-char) canonical SHA, or null when no authoritative SHA
// is available (callers then show an explicit "unverified" label — never a
// diagnostic hash masquerading as the SHA).
export function canonicalReleaseShaShort(versionBody) {
  const prov = versionBody?.deployable_release_provenance || {};
  const sha = prov.authorized_saved_sha || versionBody?.authorized_saved_sha || null;
  if (typeof sha === "string" && /^[0-9a-f]{7,40}$/i.test(sha)) return sha.slice(0, 8);
  return null;
}
