// Dispatch Portal session helpers. Mirrors lib/safetyAuth.js exactly.
const KEY = "masci.dispatch.token";
const USER_KEY = "masci.dispatch.user";
const REMEMBER_KEY = "masci.dispatch.remember";

const storeOf = () =>
  (sessionStorage.getItem(REMEMBER_KEY) === "0" ? sessionStorage : localStorage);

export function getDispatchToken() {
  try {
    return localStorage.getItem(KEY) || sessionStorage.getItem(KEY) || "";
  } catch {
    return "";
  }
}

export function setDispatchToken(token, remember = true) {
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

export function clearDispatchToken() {
  try {
    localStorage.removeItem(KEY);
    sessionStorage.removeItem(KEY);
    localStorage.removeItem(USER_KEY);
    sessionStorage.removeItem(USER_KEY);
  } catch { /* noop */ }
}

export function setDispatchUser(user) {
  try {
    storeOf().setItem(USER_KEY, JSON.stringify(user || {}));
  } catch { /* noop */ }
}

export function getDispatchUser() {
  try {
    const raw = localStorage.getItem(USER_KEY) || sessionStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function isDispatch() {
  return !!getDispatchToken();
}
