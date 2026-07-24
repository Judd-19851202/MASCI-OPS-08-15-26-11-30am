// Legacy Field Leadership shared-secret auth has been retired.
import { clearThumbCache } from "@/lib/thumbCache";

const KEY = "masci.leadership.token";
const ISSUED_KEY = "masci.leadership.issued";
const MAX_AGE_MS = 12 * 60 * 60 * 1000;

export function getLeadershipToken() {
  if (typeof window === "undefined") return null;
  try {
    const tok = window.sessionStorage.getItem(KEY);
    const issued = parseInt(window.sessionStorage.getItem(ISSUED_KEY) || "0", 10);
    if (!tok || !issued) return null;
    if (Date.now() - issued > MAX_AGE_MS) {
      clearLeadershipToken();
      return null;
    }
    return tok;
  } catch {
    return null;
  }
}

export function clearLeadershipToken() {
  try {
    window.sessionStorage.removeItem(KEY);
    window.sessionStorage.removeItem(ISSUED_KEY);
    clearThumbCache();
  } catch { /* noop */ }
}

export async function loginLeadership(password) {
  throw new Error("Legacy Field Leadership shared-secret login has been retired.");
}

export function isLeadershipAuthed() {
  return Boolean(getLeadershipToken());
}
