// Admin portal token storage.
// Token is sent on every request via the X-Admin-Token header.
//
// "Remember me" support: tokens written with {remember:true} live in
// localStorage (persistent); {remember:false} writes to sessionStorage
// (cleared on tab close).

import { readToken, writeToken, clearToken } from "@/lib/tokenStorage";

const KEY = "masci.admin.token";

export function getAdminToken() {
  return readToken(KEY);
}

export function setAdminToken(token, opts = {}) {
  writeToken(KEY, token, opts);
}

export function clearAdminToken() {
  clearToken(KEY);
}

export function isAdmin() {
  return !!getAdminToken();
}
