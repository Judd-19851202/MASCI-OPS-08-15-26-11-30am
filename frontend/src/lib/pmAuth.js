// PM (Project Manager) portal token storage. Same shape as adminAuth/shopAuth.
// Token is sent on every request via the X-PM-Token header.
// Backend's `require_admin` accepts admin OR PM tokens; backup/recovery
// routes use `require_admin_strict` which rejects PM tokens.

const KEY = "masci.pm.token";

export function getPmToken() {
  try {
    return window.localStorage.getItem(KEY) || "";
  } catch {
    return "";
  }
}

export function setPmToken(token) {
  try {
    window.localStorage.setItem(KEY, token);
  } catch {
    /* noop */
  }
}

export function clearPmToken() {
  try {
    window.localStorage.removeItem(KEY);
  } catch {
    /* noop */
  }
}

export function isPm() {
  return !!getPmToken();
}
