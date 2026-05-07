// Field Leadership password gate.
// Stores the leadership token in sessionStorage so it clears when the tab
// closes — supervisors must re-enter the password at the start of each
// browser session. Backend issues a 12h token; we also age-check on read.

import { api } from "@/lib/api";

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

export function setLeadershipToken(tok) {
  try {
    window.sessionStorage.setItem(KEY, tok);
    window.sessionStorage.setItem(ISSUED_KEY, String(Date.now()));
  } catch {
    /* sessionStorage disabled — gate becomes per-page-load */
  }
}

export function clearLeadershipToken() {
  try {
    window.sessionStorage.removeItem(KEY);
    window.sessionStorage.removeItem(ISSUED_KEY);
  } catch { /* noop */ }
}

export async function loginLeadership(password) {
  const res = await api.post("/field-leadership/login", { password });
  const tok = res.data?.token;
  if (tok) setLeadershipToken(tok);
  return tok;
}

export function isLeadershipAuthed() {
  return Boolean(getLeadershipToken());
}
