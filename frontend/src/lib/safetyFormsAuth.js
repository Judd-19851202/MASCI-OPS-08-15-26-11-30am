// Safety Forms token storage. Mirrors shopAuth.js / pmAuth.js for the
// /safety/forms password-gated forms (Equipment Issuance + Training).
// "Remember me" support: tokens written with {remember:true} live in
// localStorage; {remember:false} writes to sessionStorage (cleared on
// tab close).

import { readToken, writeToken, clearToken } from "@/lib/tokenStorage";

const KEY = "masci.safetyforms.token";

export function getSafetyFormsToken() {
  return readToken(KEY);
}

export function setSafetyFormsToken(token, opts = {}) {
  writeToken(KEY, token, opts);
}

export function clearSafetyFormsToken() {
  clearToken(KEY);
}

export function isSafetyForms() {
  return !!getSafetyFormsToken();
}
