/**
 * pm/command/pmCommandApi.js — thin REST client for the PM Command
 * Center Phase 4A backend endpoints (/api/pm/command-center/*).
 *
 * Doctrine:
 *   - Uses REACT_APP_BACKEND_URL.
 *   - Sends X-Admin-Token AND X-PM-Token when present (PM-OR-admin
 *     gated reads on the backend).
 *   - All endpoints support an optional ?project_number=... filter
 *     so the operator can pin one project or view all assigned jobs.
 *   - Returns parsed JSON; raises on non-2xx so the central axios
 *     SessionStatusOverlay surfaces calm session/network errors.
 */
import { getAdminToken } from "@/lib/adminAuth";
import { getPmToken } from "@/lib/pmAuth";

const API = process.env.REACT_APP_BACKEND_URL;

function authHeaders(extra = {}) {
  const h = { "Content-Type": "application/json", ...extra };
  const a = getAdminToken();
  const p = getPmToken();
  if (a) h["X-Admin-Token"] = a;
  if (p) h["X-PM-Token"] = p;
  return h;
}

function q(params) {
  const usp = new URLSearchParams();
  Object.entries(params || {}).forEach(([k, v]) => {
    if (v != null && v !== "") usp.set(k, String(v));
  });
  const s = usp.toString();
  return s ? `?${s}` : "";
}

async function _get(path, params) {
  const r = await fetch(`${API}${path}${q(params)}`, {
    method: "GET",
    headers: authHeaders(),
  });
  if (!r.ok) {
    const txt = await r.text().catch(() => "");
    throw new Error(`GET ${path} → ${r.status} ${txt.slice(0, 120)}`);
  }
  return r.json();
}

export const pmCommandApi = {
  overview:     (project_number)        => _get("/api/pm/command-center/overview", { project_number }),
  resources:    (project_number, limit = 1000) => _get("/api/pm/command-center/resources", { project_number, limit }),
  hauls:        (project_number, limit = 500)  => _get("/api/pm/command-center/hauls", { project_number, limit }),
  materials:    (project_number, days = 7)     => _get("/api/pm/command-center/materials", { project_number, days }),
  shopImpact:   (project_number)        => _get("/api/pm/command-center/shop-impact", { project_number }),
  safetyImpact: (project_number)        => _get("/api/pm/command-center/safety-impact", { project_number }),
  timeline:     (project_number, days = 7, limit = 300) => _get("/api/pm/command-center/timeline", { project_number, days, limit }),
};

export default pmCommandApi;
