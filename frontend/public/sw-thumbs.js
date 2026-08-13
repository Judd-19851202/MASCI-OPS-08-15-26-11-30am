/* eslint-disable no-restricted-globals */
// MASCI Hub — Photo thumbnail Service Worker (session-isolated)
// =================================================================
// PURPOSE
// Cache the last ~400 /api/job-photos/*/thumb responses on-device so
// returning to the photos page on flaky trailer Wi-Fi feels instant.
//
// SESSION ISOLATION (hardening)
// Thumbnails are cached in a namespace derived from the authenticated
// principal id: `masci-thumbs-v3:<principal>`. A thumbnail cached by
// one identity can never be served to another user, another role, an
// unauthenticated session, or a replaced/downgraded session, because
// each identity reads/writes ONLY its own namespace.
//
// FAIL-CLOSED
// If no principal is currently established (logout, SW restart before
// the client re-identifies, or unauthenticated), the SW does NOT read
// or write the cache at all — every request goes straight to the
// network so backend authorization stays authoritative. Offline with
// no established principal fails safely (no prior-session image bytes).
//
// SAFETY GUARANTEES
// 1. SCOPE-LIMITED to /api/job-photos/<id>/thumb(-signed)?. Everything
//    else (auth, JSON APIs, app shell, HTML) falls through to network.
// 2. NO SECRETS in cache names/keys — only an opaque principal id.
// 3. LRU-BOUNDED per namespace (max 400). Orphan namespaces are purged
//    on principal change / logout so abandoned caches can't grow.
// 4. SAFE UPGRADES: version-tagged; old versions purged on activate.
// 5. MESSAGES: SET_THUMB_CACHE_PRINCIPAL, CLEAR_THUMB_CACHE,
//    CLEAR_ALL_THUMB_CACHES.
// 6. NO HTML CACHING.

const CACHE_VERSION = "v3";
const CACHE_PREFIX = `masci-thumbs-${CACHE_VERSION}:`;
const LEGACY_PREFIX = "masci-thumbs-";
const MAX_ENTRIES = 400;
const THUMB_URL_RE = /\/api\/job-photos\/[^/]+\/thumb(-signed)?(\?|$)/;

// In-memory only. Lost on SW restart -> fail-closed until the client
// re-establishes it via SET_THUMB_CACHE_PRINCIPAL.
let currentPrincipal = null;

function sanitizePrincipal(p) {
  if (!p) return null;
  // Opaque id only. Strip anything that could smuggle a token/URL.
  const s = String(p).trim();
  if (!s) return null;
  return s.replace(/[^A-Za-z0-9_.:-]/g, "").slice(0, 128) || null;
}

function currentCacheName() {
  return currentPrincipal ? CACHE_PREFIX + currentPrincipal : null;
}

async function purgeOtherNamespaces(keepName) {
  const names = await caches.keys();
  await Promise.all(
    names
      .filter((n) => n.startsWith(LEGACY_PREFIX) && n !== keepName)
      .map((n) => caches.delete(n)),
  );
}

self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      // Drop legacy (v1/v2, non-namespaced) caches from prior deploys.
      const names = await caches.keys();
      await Promise.all(
        names
          .filter((n) => n.startsWith(LEGACY_PREFIX) && !n.startsWith(CACHE_PREFIX))
          .map((n) => caches.delete(n)),
      );
      await self.clients.claim();
    })(),
  );
});

self.addEventListener("message", (event) => {
  const data = event.data || {};
  if (data.type === "SET_THUMB_CACHE_PRINCIPAL") {
    const next = sanitizePrincipal(data.principal);
    currentPrincipal = next;
    // Isolate: keep only the active principal's namespace, purge others
    // (prior users, orphans). If unset -> purge everything.
    event.waitUntil(purgeOtherNamespaces(currentCacheName()));
  } else if (data.type === "CLEAR_THUMB_CACHE") {
    // Logout / role switch: wipe the active namespace and fail closed.
    const name = currentCacheName();
    currentPrincipal = null;
    event.waitUntil(
      (async () => {
        if (name) await caches.delete(name);
      })(),
    );
  } else if (data.type === "CLEAR_ALL_THUMB_CACHES") {
    currentPrincipal = null;
    event.waitUntil(purgeOtherNamespaces(null));
  }
});

async function trimCache(cache) {
  const keys = await cache.keys();
  if (keys.length <= MAX_ENTRIES) return;
  const overflow = keys.length - MAX_ENTRIES;
  for (let i = 0; i < overflow; i++) {
    cache.delete(keys[i]);
  }
}

function thumbCacheKey(req) {
  try {
    const u = new URL(req.url);
    u.searchParams.delete("t"); // strip rotating signed-URL token
    return new Request(u.toString(), { method: "GET" });
  } catch {
    return req;
  }
}

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  let url;
  try { url = new URL(req.url); } catch { return; }
  if (url.origin !== self.location.origin) return;
  if (!THUMB_URL_RE.test(url.pathname + url.search)) return;

  // FAIL-CLOSED: with no established principal we never read or write
  // the cache — the network (backend auth) decides, and offline fails
  // safely instead of leaking a prior session's image bytes.
  const cacheName = currentCacheName();
  if (!cacheName) return; // default browser/network behavior

  event.respondWith(
    (async () => {
      try {
        const cache = await caches.open(cacheName);
        const key = thumbCacheKey(req);
        const cached = await cache.match(key, { ignoreVary: false });
        const networkPromise = fetch(req)
          .then(async (res) => {
            if (res && res.ok && res.status === 200) {
              try {
                await cache.put(key, res.clone());
                trimCache(cache);
              } catch { /* QuotaExceededError, ignore */ }
            }
            return res;
          })
          .catch(() => null);

        if (cached) {
          event.waitUntil(networkPromise);
          return cached;
        }
        const fresh = await networkPromise;
        return fresh || fetch(req);
      } catch {
        return fetch(req);
      }
    })(),
  );
});
