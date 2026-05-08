// Admin portal token storage.
// Token is sent on every request via the X-Admin-Token header.
//
// "Remember me" support: tokens written with {remember:true} live in
// localStorage (persistent); {remember:false} writes to sessionStorage
// (cleared on tab close).

import { readToken, writeToken, clearToken } from "@/lib/tokenStorage";
import { clearThumbCache } from "@/lib/thumbCache";

const KEY = "masci.admin.token";

export function getAdminToken() {
  return readToken(KEY);
}

export function setAdminToken(token, opts = {}) {
  writeToken(KEY, token, opts);
  // Fresh sign-in → wipe any prior user's cached thumbs.
  clearThumbCache();
}

export function clearAdminToken() {
  clearToken(KEY);
  clearThumbCache();
}

export function isAdmin() {
  return !!getAdminToken();
}
