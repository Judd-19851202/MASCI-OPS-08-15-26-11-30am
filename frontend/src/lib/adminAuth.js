// Admin token storage. The "token" is just the admin password — backend
// re-validates it on every protected request via the X-Admin-Token header.
// Stored in localStorage so the admin stays signed in across reloads.

const KEY = "masci.admin.token";

export function getAdminToken() {
  try {
    return window.localStorage.getItem(KEY) || "";
  } catch {
    return "";
  }
}

export function setAdminToken(token) {
  try {
    window.localStorage.setItem(KEY, token);
  } catch {
    /* noop */
  }
}

export function clearAdminToken() {
  try {
    window.localStorage.removeItem(KEY);
  } catch {
    /* noop */
  }
}

export function isAdmin() {
  return !!getAdminToken();
}
