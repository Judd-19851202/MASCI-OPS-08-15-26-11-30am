// /app/frontend/src/lib/mustChangePassword.js
//
// Track 15.14A · Layer 2 — client-side temp-password flag storage.
//
// The backend is the source of truth (Layer 3 enforces with HTTP 403
// PASSWORD_CHANGE_REQUIRED on any protected route). This module gives
// the SPA a fast local signal so route guards can bounce users to the
// right /change-password page BEFORE any protected fetch is attempted.
//
// Per-portal storage key: `${portal}_must_change_password` → "1" | absent.
// Cleared on successful change-password (mints fresh tokens + flag clear).

const KEY = (portal) => `${portal}_must_change_password`;

export const PORTAL_CHANGE_PASSWORD_PATH = {
  hr: "/hr/change-password",
  pm: "/pm/change-password",
  shop: "/shop/change-password",
  safety: "/safety-portal/change-password",
  dispatch: "/dispatch-portal/change-password",
  field_leadership: "/field-leadership/portal/change-password",
  fl: "/field-leadership/portal/change-password",
  admin: "/change-password", // directory user master rotation
  directory: "/change-password",
};

export function setMustChange(portal, value) {
  if (!portal) return;
  try {
    if (value) {
      localStorage.setItem(KEY(portal), "1");
    } else {
      localStorage.removeItem(KEY(portal));
    }
  } catch {
    // localStorage may be unavailable (private mode); silent.
  }
}

export function getMustChange(portal) {
  if (!portal) return false;
  try {
    return localStorage.getItem(KEY(portal)) === "1";
  } catch {
    return false;
  }
}

export function clearAllMustChange() {
  try {
    [
      "hr",
      "pm",
      "shop",
      "safety",
      "dispatch",
      "field_leadership",
      "fl",
      "admin",
      "directory",
    ].forEach((p) => localStorage.removeItem(KEY(p)));
  } catch {
    // ignore
  }
}

export function changePasswordPath(portal) {
  return PORTAL_CHANGE_PASSWORD_PATH[portal] || "/change-password";
}

// Centralised redirect helper used by route guards and the api.js 403
// interceptor. The current path is appended via the `from` query string
// so the change-password page can land the user back where they were.
export function redirectToChangePassword(portal, opts = {}) {
  if (typeof window === "undefined") return;
  const target = changePasswordPath(portal);
  const from = opts.preserveFrom !== false
    ? `?from=${encodeURIComponent(window.location.pathname + window.location.search)}`
    : "";
  // Use a soft navigation if a router is wired (consumer passes navigate);
  // fall back to window.location for guards.
  if (typeof opts.navigate === "function") {
    opts.navigate(`${target}${from}`, { replace: true });
  } else {
    window.location.replace(`${target}${from}`);
  }
}
