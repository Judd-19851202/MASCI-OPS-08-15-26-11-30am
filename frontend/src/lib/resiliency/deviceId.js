// deviceId.js — P0 field-incident remediation · 2026-05-27.
//
// Persisted device-scoped identifier, INDEPENDENT of any auth token.
// This is the root fix for hypothesis H2 (token-rotation orphans the
// draft IDB key). With a stable device-bound id, the draft key stays
// the same across login/logout/passkey-rotation/multi-login refresh.
//
// Doctrine
// --------
// - Stored in localStorage at "masci.device-id".
// - Format: "d.<32-hex-chars>" (UUIDv4 stripped of dashes).
// - First call mints + persists; subsequent calls return same value.
// - Survives logout — we want the DEVICE, not the SESSION.
// - Cleared only when the user wipes Safari storage.
// - Not a security boundary. Telemetry segmentation only.

const STORAGE_KEY = "masci.device-id";
let _cached = null;
let _sessionFallback = null;

function _uuidHex32() {
  // crypto.randomUUID is available in modern Safari/iOS 16+ and Chrome.
  try {
    if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
      return crypto.randomUUID().replace(/-/g, "");
    }
  } catch { /* ignore */ }
  // Fallback — 32 hex chars from Math.random. Lower entropy but
  // sufficient for IDB key segmentation.
  let s = "";
  for (let i = 0; i < 32; i++) {
    s += Math.floor(Math.random() * 16).toString(16);
  }
  return s;
}

export function getDeviceId() {
  if (_cached) return _cached;
  try {
    if (typeof localStorage !== "undefined") {
      const existing = localStorage.getItem(STORAGE_KEY);
      if (existing && /^d\.[0-9a-f]{16,64}$/.test(existing)) {
        _cached = existing;
        return existing;
      }
      const minted = `d.${_uuidHex32()}`;
      try {
        localStorage.setItem(STORAGE_KEY, minted);
      } catch {
        // localStorage disabled (Private Browsing) — fall back to
        // session-scoped id. NOT persisted, but at least stable
        // within one tab session.
        if (!_sessionFallback) _sessionFallback = `d.${_uuidHex32()}`;
        return _sessionFallback;
      }
      _cached = minted;
      return minted;
    }
  } catch { /* ignore */ }
  if (!_sessionFallback) _sessionFallback = `d.${_uuidHex32()}`;
  return _sessionFallback;
}

// Alias kept for explicit intent at call sites where the side-effect
// (persist + return) is what's wanted.
export const ensureDeviceId = getDeviceId;

// Test helper — never called in production code paths.
export function _resetDeviceIdForTests() {
  _cached = null;
  _sessionFallback = null;
  try { localStorage.removeItem(STORAGE_KEY); } catch { /* ignore */ }
}
