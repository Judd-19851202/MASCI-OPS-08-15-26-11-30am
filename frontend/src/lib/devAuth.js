// Developer (ForgedOps LLC / vendor) portal token storage.
// Token is sent on every request via the X-Dev-Token header.
// Backend's `require_dev` accepts ONLY this token — admin and PM tokens
// are explicitly rejected so vendor-internal surfaces (Ops Manual,
// snapshots) stay hidden from MASCI staff.

const KEY = "masci.dev.token";

export function getDevToken() {
  try {
    return window.localStorage.getItem(KEY) || "";
  } catch {
    return "";
  }
}

export function setDevToken(token) {
  try {
    window.localStorage.setItem(KEY, token);
  } catch {
    /* noop */
  }
}

export function clearDevToken() {
  try {
    window.localStorage.removeItem(KEY);
  } catch {
    /* noop */
  }
}

export function isDev() {
  return !!getDevToken();
}
