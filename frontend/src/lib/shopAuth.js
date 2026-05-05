// Shop token storage. Mirrors adminAuth.js / pmAuth.js but for the
// mechanic / shop console (Pre-Op + sign-offs only).
//
// "Remember me" support: tokens written with {remember:true} live in
// localStorage (persistent); {remember:false} writes to sessionStorage
// (cleared on tab close).

import { readToken, writeToken, clearToken } from "@/lib/tokenStorage";

const KEY = "masci.shop.token";

export function getShopToken() {
  return readToken(KEY);
}

export function setShopToken(token, opts = {}) {
  writeToken(KEY, token, opts);
}

export function clearShopToken() {
  clearToken(KEY);
}

export function isShop() {
  return !!getShopToken();
}
