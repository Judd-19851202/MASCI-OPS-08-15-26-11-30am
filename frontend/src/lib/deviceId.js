/**
 * deviceId — stable per-browser device identifier for banner ack
 * tracking.
 *
 * The Hub site is partially unauthenticated — anyone can submit a daily
 * report without logging in — so we can't tie acknowledgments to a PM
 * or shop token. Instead we mint a one-time UUID on first visit, persist
 * it in localStorage, and use that as the per-device identity for
 * "Acknowledge" / "Dismiss" actions on hub banners.
 *
 * Reset semantics: clearing browser data resets the id; the user will be
 * asked to ack again on the next page load (this is by design — if a
 * device is shared between two foremen and one clears storage, the
 * other should re-ack on their next visit).
 */
const KEY = "masci.device.id";

export function getDeviceId() {
  try {
    let id = localStorage.getItem(KEY);
    if (!id) {
      // Prefer crypto.randomUUID() when available; fall back to a
      // 32-char hex string built from Math.random() so we still work
      // on older WebViews.
      if (typeof crypto !== "undefined" && crypto.randomUUID) {
        id = crypto.randomUUID().replace(/-/g, "");
      } else {
        id =
          Math.random().toString(16).slice(2).padStart(16, "0") +
          Math.random().toString(16).slice(2).padStart(16, "0");
      }
      localStorage.setItem(KEY, id);
    }
    return id;
  } catch {
    // If localStorage is blocked (private mode etc.) fall back to a
    // per-session random id. Ack tracking won't survive a reload but
    // the banner still renders.
    return `ephemeral-${Math.random().toString(16).slice(2)}`;
  }
}
