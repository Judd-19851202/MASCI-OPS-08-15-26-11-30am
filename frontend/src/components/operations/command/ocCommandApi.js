/**
 * operations/ocCommandApi.js — REST client for the Operations Center
 * Phase 4C backend endpoints (/api/operations-center/command/*).
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

function qs(o) {
  const u = new URLSearchParams();
  Object.entries(o || {}).forEach(([k, v]) => { if (v != null && v !== "") u.set(k, String(v)); });
  const s = u.toString();
  return s ? `?${s}` : "";
}

async function _get(path, params) {
  const r = await fetch(`${API}${path}${qs(params)}`, { headers: authHeaders() });
  if (!r.ok) {
    const t = await r.text().catch(() => "");
    throw new Error(`GET ${path} → ${r.status} ${t.slice(0, 120)}`);
  }
  return r.json();
}

export const ocCommandApi = {
  brief:          () => _get("/api/operations-center/command/brief"),
  projectHealth:  () => _get("/api/operations-center/command/project-health"),
  allocation:     () => _get("/api/operations-center/command/allocation"),
  conflicts:      () => _get("/api/operations-center/command/conflicts"),
  specialtyAssets:(params) => _get("/api/operations-center/command/specialty-assets", params),
  shopImpact:     () => _get("/api/operations-center/command/shop-impact"),
  safetyImpact:   () => _get("/api/operations-center/command/safety-impact"),
  telematics:     () => _get("/api/operations-center/command/telematics"),
  timeline:       (days = 3, limit = 400) =>
                    _get("/api/operations-center/command/timeline", { days, limit }),
  mapContract:    (limit = 500) =>
                    _get("/api/operations-center/command/map-contract", { limit }),
};

export default ocCommandApi;
