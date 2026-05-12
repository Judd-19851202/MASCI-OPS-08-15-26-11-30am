// HR Portal session helpers. Mirrors lib/shopAuth.js exactly.
const KEY = "masci.hr.token";
const USER_KEY = "masci.hr.user";
const REMEMBER_KEY = "masci.hr.remember";

const storeOf = () => (sessionStorage.getItem(REMEMBER_KEY) === "0" ? sessionStorage : localStorage);

export function getHrToken() {
  try {
    return localStorage.getItem(KEY) || sessionStorage.getItem(KEY) || "";
  } catch {
    return "";
  }
}

export function setHrToken(token, remember = true) {
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

export function clearHrToken() {
  try {
    localStorage.removeItem(KEY);
    sessionStorage.removeItem(KEY);
    localStorage.removeItem(USER_KEY);
    sessionStorage.removeItem(USER_KEY);
  } catch {/* ignore */}
}

export function setHrUser(user) {
  try {
    storeOf().setItem(USER_KEY, JSON.stringify(user || {}));
  } catch {/* ignore */}
}

export function getHrUser() {
  try {
    const raw = localStorage.getItem(USER_KEY) || sessionStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function isHr() {
  return !!getHrToken();
}
