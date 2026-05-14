// Safety Portal session helpers. Mirrors lib/hrAuth.js exactly.
const KEY = "masci.safety.token";
const USER_KEY = "masci.safety.user";
const REMEMBER_KEY = "masci.safety.remember";

const storeOf = () =>
  (sessionStorage.getItem(REMEMBER_KEY) === "0" ? sessionStorage : localStorage);

export function getSafetyToken() {
  try {
    return localStorage.getItem(KEY) || sessionStorage.getItem(KEY) || "";
  } catch {
    return "";
  }
}

export function setSafetyToken(token, remember = true) {
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
  } catch { /* noop */ }
}

export function clearSafetyToken() {
  try {
    localStorage.removeItem(KEY);
    sessionStorage.removeItem(KEY);
    localStorage.removeItem(USER_KEY);
    sessionStorage.removeItem(USER_KEY);
  } catch { /* noop */ }
}

export function setSafetyUser(user) {
  try {
    storeOf().setItem(USER_KEY, JSON.stringify(user || {}));
  } catch { /* noop */ }
}

export function getSafetyUser() {
  try {
    const raw = localStorage.getItem(USER_KEY) || sessionStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function isSafety() {
  return !!getSafetyToken();
}
