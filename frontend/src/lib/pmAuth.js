// PM (Project Manager) portal token storage. Same shape as adminAuth/shopAuth.
// Token is sent on every request via the X-PM-Token header.
// Backend's `require_admin` accepts admin OR PM tokens; backup/recovery
// routes use `require_admin_strict` which rejects PM tokens.
//
// "Remember me" support: tokens written with {remember:true} live in
// localStorage (persistent); {remember:false} writes to sessionStorage
// (cleared on tab close).

import { readToken, writeToken, clearToken } from "@/lib/tokenStorage";
import { clearThumbCache } from "@/lib/thumbCache";

const KEY = "masci.pm.token";

export function getPmToken() {
  return readToken(KEY);
}

export function setPmToken(token, opts = {}) {
  writeToken(KEY, token, opts);
  clearThumbCache();
}

export function clearPmToken() {
  clearToken(KEY);
  clearThumbCache();
}

export function isPm() {
  return !!getPmToken();
}
