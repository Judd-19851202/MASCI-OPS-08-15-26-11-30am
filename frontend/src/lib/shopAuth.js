// Shop token storage. Mirrors adminAuth.js but for the mechanic / shop
// console (Pre-Op + sign-offs only).
const KEY = "masci.shop.token";

export function getShopToken() {
  try {
    return window.localStorage.getItem(KEY) || "";
  } catch {
    return "";
  }
}

export function setShopToken(token) {
  try {
    window.localStorage.setItem(KEY, token);
  } catch {
    /* noop */
  }
}

export function clearShopToken() {
  try {
    window.localStorage.removeItem(KEY);
  } catch {
    /* noop */
  }
}

export function isShop() {
  return !!getShopToken();
}
