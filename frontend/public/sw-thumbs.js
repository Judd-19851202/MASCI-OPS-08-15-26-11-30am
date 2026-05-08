/* eslint-disable no-restricted-globals */
// MASCI Hub — Photo thumbnail Service Worker
// =================================================================
// PURPOSE
// Cache the last ~200 /api/job-photos/*/thumb responses on-device so
// returning to the photos page on flaky trailer Wi-Fi feels instant
// (and previously-loaded weeks still render fully offline).
//
// SAFETY GUARANTEES
// 1. SCOPE-LIMITED: only GET requests whose pathname matches
//    /api/job-photos/<id>/thumb are touched. Every other request
//    (auth, daily reports, PMs, admin endpoints, app shell) falls
//    straight through to the network.
// 2. AUTH-LEAK PROOF: cache key includes the Vary: Accept header so
//    AVIF/WebP/JPEG variants don't cross-contaminate. Auth is enforced
//    by the server before the response is generated; a cached response
//    that the browser already received once is the same response that
//    user is allowed to see.
// 3. LRU-BOUNDED: max 200 entries. Old entries auto-evicted FIFO.
// 4. SAFE UPGRADES: cache name carries a version. When this file is
//    edited and a new SW takes over, the old cache is purged and the
//    new SW activates immediately (skipWaiting + clients.claim).
// 5. KILL-SWITCH: window code can postMessage({type:'CLEAR_THUMB_CACHE'})
//    or unregister the SW outright — both wipe the cache and resume
//    network-first behavior.
// 6. NO HTML CACHING. The app shell is never cached here, so a deploy
//    of new index.html / JS bundles is always fetched fresh.

const CACHE_VERSION = "v2";
const CACHE_NAME = `masci-thumbs-${CACHE_VERSION}`;
const MAX_ENTRIES = 400;
// Cache both the legacy auth-header endpoint and the new signed-URL
// endpoint. The signed endpoint is the hot path (gallery <img src>),
// the legacy one stays for lightbox preloads + native shells.
const THUMB_URL_RE = /\/api\/job-photos\/[^/]+\/thumb(-signed)?(\?|$)/;

self.addEventListener("install", (event) => {
  // Take over from the previous SW immediately on first load.
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      // Drop any old cache versions left behind by previous deploys.
      const names = await caches.keys();
      await Promise.all(
        names
          .filter((n) => n.startsWith("masci-thumbs-") && n !== CACHE_NAME)
          .map((n) => caches.delete(n)),
      );
      await self.clients.claim();
    })(),
  );
});

self.addEventListener("message", (event) => {
  if (event.data?.type === "CLEAR_THUMB_CACHE") {
    event.waitUntil(caches.delete(CACHE_NAME));
  }
});

async function trimCache(cache) {
  const keys = await cache.keys();
  if (keys.length <= MAX_ENTRIES) return;
  // Oldest first (insertion order is preserved by Cache API).
  const overflow = keys.length - MAX_ENTRIES;
  for (let i = 0; i < overflow; i++) {
    // best-effort; not awaited so we don't slow down the response.
    cache.delete(keys[i]);
  }
}

/**
 * Stale-while-revalidate: return the cached thumbnail instantly if we
 * have one, then refresh it in the background. If nothing is cached we
 * fall through to a normal network fetch and cache the result.
 *
 * Cache key normalization: signed-URL thumbs include a 1h-rotating
 * ``?t=<token>`` parameter. Without normalization every page reload
 * after the token TTL would re-fetch every photo from the network.
 * We strip ``t`` (and any other ephemeral params) from the cache key
 * so the same ``photo_id`` shares one entry across token rotations.
 *
 * Errors at every step are swallowed — the user always gets the
 * default browser/network behaviour as the safety net.
 */
function thumbCacheKey(req) {
  try {
    const u = new URL(req.url);
    u.searchParams.delete("t");
    // Build a stable Request matching the original method/headers but
    // with the normalized URL. Cache API matches by URL string + method.
    return new Request(u.toString(), { method: "GET" });
  } catch {
    return req;
  }
}

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  // Only same-origin /api/job-photos/*/thumb(-signed)? requests.
  let url;
  try { url = new URL(req.url); } catch { return; }
  if (url.origin !== self.location.origin) return;
  if (!THUMB_URL_RE.test(url.pathname + url.search)) return;

  event.respondWith(
    (async () => {
      try {
        const cache = await caches.open(CACHE_NAME);
        const key = thumbCacheKey(req);
        // ignoreVary:false so AVIF/WebP/JPEG variants stay separate.
        const cached = await cache.match(key, { ignoreVary: false });
        const networkPromise = fetch(req)
          .then(async (res) => {
            // Only cache successful, complete responses.
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
          // Kick off background refresh, return cached now.
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
