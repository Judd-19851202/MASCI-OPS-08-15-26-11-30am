// searchApi.js — Iter155 (Phase G). Thin client for the unified
// /api/search endpoint. Uses the canonical scoped auth-header builder
// so directory-bound portal sessions carry X-Directory-Token too.
import axios from "axios";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function authHeaders() {
  return buildScopedPortalAuthHeaders(
    ["admin", "safety", "hr", "pm", "shop", "dispatch", "fl"],
  );
}

export function hasAnyPortalToken() {
  return Object.keys(authHeaders()).length > 0;
}

export async function globalSearch(q, { kinds, limit = 6, signal } = {}) {
  const params = { q, limit };
  if (kinds && kinds.length) params.kinds = Array.isArray(kinds) ? kinds.join(",") : String(kinds);
  const r = await axios.get(`${API}/search`, {
    headers: authHeaders(), params, signal,
  });
  return r.data;
}
