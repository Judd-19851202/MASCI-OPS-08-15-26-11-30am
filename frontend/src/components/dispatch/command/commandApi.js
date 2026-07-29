/**
 * dispatch/command/commandApi.js — thin REST client for the Dispatch
 * Command Center Phase 1 backend endpoints.
 *
 * Doctrine:
 *   - Uses REACT_APP_BACKEND_URL.
 *   - Sends X-Admin-Token AND X-Dispatch-Token when present (any-portal
 *     reads).
 *   - Returns parsed JSON; raises on non-2xx so callers can surface
 *     calm error toasts via the existing trust contract.
 */
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";

const API = process.env.REACT_APP_BACKEND_URL;

function authHeaders(extra = {}) {
  return {
    "Content-Type": "application/json",
    ...buildScopedPortalAuthHeaders(["admin", "dispatch"]),
    ...extra,
  };
}

async function _get(path) {
  const r = await fetch(`${API}${path}`, {
    method: "GET",
    headers: authHeaders(),
  });
  if (!r.ok) {
    const txt = await r.text().catch(() => "");
    throw new Error(`GET ${path} → ${r.status} ${txt.slice(0, 120)}`);
  }
  return r.json();
}

async function _post(path, body) {
  const r = await fetch(`${API}${path}`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(body || {}),
  });
  if (!r.ok) {
    const txt = await r.text().catch(() => "");
    throw new Error(`POST ${path} → ${r.status} ${txt.slice(0, 200)}`);
  }
  return r.json();
}

export const commandApi = {
  summary: () => _get("/api/dispatch/command/summary"),
  fleet:   (limit = 1000) => _get(`/api/dispatch/command/fleet?limit=${limit}`),
  drivers: (limit = 1000) => _get(`/api/dispatch/command/drivers?limit=${limit}`),
  jobs:    (limit = 500)  => _get(`/api/dispatch/command/jobs?limit=${limit}`),
  haul:    (limit = 500)  => _get(`/api/dispatch/command/haul?limit=${limit}`),
  shopFeed:(limit = 200)  => _get(`/api/shop/command-feed?limit=${limit}`),
  broadcasts: (limit = 50) => _get(`/api/dispatch/command/broadcasts?limit=${limit}`),
  sendBroadcast: (body) => _post("/api/dispatch/command/broadcast-sms", body),
};

export default commandApi;
