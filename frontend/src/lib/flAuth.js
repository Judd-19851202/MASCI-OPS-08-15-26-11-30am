// Field Leadership Portal session helpers. Mirrors hrAuth.js exactly.
// NOTE: this is the GOVERNED PER-USER portal (iter314), NOT the legacy
// shared-password document gate which uses `leadershipAuth.js`.
const KEY = "masci.fl.token";
const USER_KEY = "masci.fl.user";
const REMEMBER_KEY = "masci.fl.remember";

export function getFlToken() {
  try {
    return localStorage.getItem(KEY) || sessionStorage.getItem(KEY) || "";
  } catch {
    return "";
  }
}

export function setFlToken(token, remember = true) {
  try {
    if (remember) {
      localStorage.setItem(KEY, token);
      sessionStorage.removeItem(KEY);
      sessionStorage.setItem(REMEMBER_KEY, "1");
    } else {
      sessionStorage.setItem(KEY, token);
      localStorage.removeItem(KEY);
      sessionStorage.setItem(REMEMBER_KEY, "0");
    }
  } catch {/* ignore */}
}

export function clearFlToken() {
  try {
    localStorage.removeItem(KEY);
    sessionStorage.removeItem(KEY);
    localStorage.removeItem(USER_KEY);
    sessionStorage.removeItem(USER_KEY);
  } catch {/* ignore */}
}

export function setFlUser(user) {
  try {
    const blob = JSON.stringify(user || {});
    localStorage.setItem(USER_KEY, blob);
  } catch {/* ignore */}
}

export function getFlUser() {
  try {
    const raw = localStorage.getItem(USER_KEY) || sessionStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function isFl() {
  return !!getFlToken();
}
