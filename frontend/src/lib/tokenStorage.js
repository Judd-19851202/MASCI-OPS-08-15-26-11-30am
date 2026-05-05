// tokenStorage — shared "Remember me" token storage helper.
//
// Two storage tiers:
//   • localStorage  — persists across browser restarts (default, "remember me on")
//   • sessionStorage — wiped when the tab/window closes (used when "remember me" is unchecked)
//
// On read, we check sessionStorage first (newer write wins) then fall back
// to localStorage. On clear, we wipe both — there must never be a stale
// token lingering in one tier after the user logs out.
//
// Used by adminAuth, pmAuth, and shopAuth. Each portal passes its own
// localStorage KEY; we own all the storage-tier logic in one place.

export function readToken(key) {
  try {
    const s = window.sessionStorage.getItem(key);
    if (s) return s;
    return window.localStorage.getItem(key) || "";
  } catch {
    return "";
  }
}

export function writeToken(key, token, { remember = true } = {}) {
  try {
    if (remember) {
      window.localStorage.setItem(key, token);
      // Clear sessionStorage so we don't have two copies.
      window.sessionStorage.removeItem(key);
    } else {
      window.sessionStorage.setItem(key, token);
      // Clear any old "remember me" copy from localStorage.
      window.localStorage.removeItem(key);
    }
  } catch {
    /* noop */
  }
}

export function clearToken(key) {
  try {
    window.localStorage.removeItem(key);
    window.sessionStorage.removeItem(key);
  } catch {
    /* noop */
  }
}
