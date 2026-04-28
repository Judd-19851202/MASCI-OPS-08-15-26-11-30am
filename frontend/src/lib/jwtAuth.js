/**
 * Crew-Hub JWT storage helpers.
 *
 * Why localStorage instead of httpOnly cookies?
 * The frontend runs at `mascidocs.com`, the backend behind Cloudflare. The
 * Cloudflare/Emergent ingress overwrites our `Access-Control-Allow-Origin`
 * with `*`, which the browser refuses to combine with credentialed cookie
 * requests — every login fails with "Login failed — check connection".
 *
 * Switching to a Bearer token in localStorage avoids credentialed CORS
 * entirely. The token still has the same JWT payload + exp; the backend
 * already accepts `Authorization: Bearer …` as a fallback to the cookie.
 */
const KEY = "masci_jwt_v1";

export function getJwt() {
  try {
    return localStorage.getItem(KEY) || null;
  } catch {
    return null;
  }
}

export function setJwt(token) {
  try {
    if (token) localStorage.setItem(KEY, token);
    else localStorage.removeItem(KEY);
  } catch {
    /* private mode etc. — fail open */
  }
}

export function clearJwt() {
  setJwt(null);
}
