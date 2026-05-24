/**
 * driverAuth.js · iter393 · DLS Driver session helpers (frontend).
 *
 * Mirrors the existing tokenStorage pattern (PM/HR/Shop/Safety) but
 * keeps the driver surface deliberately tiny — driver opens a magic
 * link, exchanges it for a session token, taps to transition. No
 * passwords. No portal-scope enforcement noise.
 *
 * Storage key: `masci.driver.token` (localStorage — shift may span
 * tab close/reopen on a phone).
 *
 * The driver token is always sent as the `X-Driver-Token` header on
 * /api/dispatch/driver/* calls. Tenant-Id is auto-attached when
 * present so multi-tenant dev (e.g. `dls-demo`) works transparently.
 */
const TOKEN_KEY = "masci.driver.token";
const SESSION_KEY = "masci.driver.session";
const TENANT_KEY = "masci.driver.tenant";

export function getDriverToken() {
  try {
    return localStorage.getItem(TOKEN_KEY) || "";
  } catch {
    return "";
  }
}

export function getDriverTenantId() {
  try {
    return localStorage.getItem(TENANT_KEY) || "";
  } catch {
    return "";
  }
}

export function getDriverSession() {
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function persistDriverSession({ driver_token, session_id, expires_at, tenant_id, driver }) {
  try {
    localStorage.setItem(TOKEN_KEY, driver_token || "");
    if (tenant_id) localStorage.setItem(TENANT_KEY, tenant_id);
    localStorage.setItem(
      SESSION_KEY,
      JSON.stringify({ session_id, expires_at, driver: driver || null }),
    );
  } catch {
    /* localStorage unavailable — driver UI will re-exchange on next link tap */
  }
}

export function clearDriverSession() {
  try {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(SESSION_KEY);
    localStorage.removeItem(TENANT_KEY);
  } catch {
    /* no-op */
  }
}

export function driverHeaders(extra = {}) {
  const headers = { "Content-Type": "application/json", ...extra };
  const token = getDriverToken();
  if (token) headers["X-Driver-Token"] = token;
  const tenant = getDriverTenantId();
  if (tenant) headers["X-Tenant-Id"] = tenant;
  return headers;
}
