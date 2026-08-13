// Service worker registration / lifecycle helpers for the photo
// thumbnail cache. Only runs in production builds and only registers
// the narrowly-scoped `sw-thumbs.js` file. Has a hard kill-switch
// callable from anywhere to wipe the cache (e.g. on logout / role
// switch / "something is wrong, fresh from server please").

const SW_PATH = "/sw-thumbs.js";

function isSupported() {
  return (
    typeof window !== "undefined" &&
    "serviceWorker" in navigator &&
    // Only run on a secure, real origin — local dev hot reload and
    // non-HTTPS shells are intentionally excluded.
    window.location.protocol === "https:"
  );
}

let registration = null;

// Post a message to the active thumbnail SW, waiting for it to be ready
// so first-load / restart races don't drop the principal.
async function postToThumbSw(message) {
  if (!isSupported()) return;
  try {
    const ready = await navigator.serviceWorker.ready.catch(() => null);
    const reg = ready || registration || (await navigator.serviceWorker.getRegistration("/"));
    const ctrl = reg?.active || navigator.serviceWorker.controller;
    if (ctrl) ctrl.postMessage(message);
  } catch {
    /* swallow — never break the page on cache messaging */
  }
}

/**
 * Establish (or clear) the authenticated principal namespace for the
 * thumbnail cache. `principal` MUST be a non-secret opaque id (e.g. the
 * directory user id) — never a token/session secret. Passing a falsy
 * value fails the SW closed (no cached thumbnails served).
 */
export async function setThumbCachePrincipal(principal) {
  await postToThumbSw({ type: "SET_THUMB_CACHE_PRINCIPAL", principal: principal || null });
}

export async function registerThumbCache() {
  if (!isSupported()) return null;
  try {
    registration = await navigator.serviceWorker.register(SW_PATH, { scope: "/" });
    return registration;
  } catch {
    return null;
  }
}

/**
 * Wipe every cached thumbnail. Called automatically on auth changes
 * (admin/PM/shop/leadership login or logout) so a different user on
 * the same device never sees another user's previously-cached photos
 * — even though the server already enforces scope on every fetch.
 */
export async function clearThumbCache() {
  if (!isSupported()) return;
  try {
    const reg = registration || (await navigator.serviceWorker.getRegistration("/"));
    const ctrl = reg?.active || navigator.serviceWorker.controller;
    if (ctrl) {
      ctrl.postMessage({ type: "CLEAR_THUMB_CACHE" });
    }
    // Defensive: also nuke matching caches directly in case the SW
    // hasn't activated yet on first load.
    if ("caches" in window) {
      const names = await caches.keys();
      await Promise.all(
        names.filter((n) => n.startsWith("masci-thumbs-")).map((n) => caches.delete(n)),
      );
    }
  } catch {
    /* swallow — never break the page on cache cleanup */
  }
}

export async function unregisterThumbCache() {
  if (!isSupported()) return;
  try {
    const reg = registration || (await navigator.serviceWorker.getRegistration("/"));
    if (reg) await reg.unregister();
    await clearThumbCache();
  } catch {
    /* swallow */
  }
}
