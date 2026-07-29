// Track 19.16 · Phase B1 · Incident Intelligence Engine — HTTP adapter.
// Thin wrapper around the Phase A `/api/incident-cases/*` endpoints. All
// calls include cross-portal auth headers (Safety / Admin / PM) via the
// shared helper.

import axios from "axios";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Pull whichever portal token is present. Order mirrors the backend
// `make_require_safety_admin_or_pm` gate.
function _authHeaders() {
  return buildScopedPortalAuthHeaders(["safety", "admin", "pm"]);
}

function _client() {
  return axios.create({
    baseURL: API,
    headers: { "Content-Type": "application/json", ..._authHeaders() },
    timeout: 30000,
  });
}

export async function fetchVocabulary() {
  const c = _client();
  const { data } = await c.get("/incident-cases/vocabulary");
  return data;
}

export async function createCase(fieldBlock) {
  const c = _client();
  const { data } = await c.post("/incident-cases", { field_block: fieldBlock });
  return data;
}

export async function patchFieldBlock(caseId, patch) {
  const c = _client();
  const { data } = await c.patch(
    `/incident-cases/${caseId}/field-block`,
    { patch },
  );
  return data;
}

export async function transitionCase(caseId, toState, reason = "") {
  const c = _client();
  const { data } = await c.post(
    `/incident-cases/${caseId}/transitions`,
    { to_state: toState, reason },
  );
  return data;
}

export async function addEvidence(caseId, payload) {
  const c = _client();
  const { data } = await c.post(
    `/incident-cases/${caseId}/evidence`,
    payload,
  );
  return data;
}

// TRACK 19.16 · UX Hardening Batch 1 ────────────────────────────────
// Auto-fill helpers. All read-only; degrade silently to null so the
// form still works when a helper is unavailable (offline, unauthed).

// Directory identity of the current user (name / email / role).
export async function fetchDirectoryMe() {
  try {
    const headers = buildScopedPortalAuthHeaders(["directory"]);
    if (!headers["X-Directory-Token"]) return null;
    const c = axios.create({
      baseURL: API,
      headers: { "Content-Type": "application/json", ...headers },
      timeout: 6000,
    });
    const { data } = await c.get("/auth/me-directory");
    return data?.user || null;
  } catch {
    return null;
  }
}

// Canonical project row + last-known superintendent.
export async function fetchProjectContext(projectNumber) {
  if (!projectNumber) return null;
  try {
    const c = _client();
    const { data } = await c.get(
      `/incident-intelligence/project-context/${encodeURIComponent(projectNumber)}`,
    );
    return data || null;
  } catch {
    return null;
  }
}

// Auto-fetch weather at GPS coordinates. Returns compact structured
// payload (summary/description/temp/wind). Silent-fail returns null.
export async function fetchWeather(lat, lng) {
  if (typeof lat !== "number" || typeof lng !== "number") return null;
  try {
    const c = _client();
    const { data } = await c.get(
      `/incident-intelligence/weather?lat=${lat}&lng=${lng}`,
    );
    return data || null;
  } catch {
    return null;
  }
}

export default {
  fetchVocabulary,
  createCase,
  patchFieldBlock,
  transitionCase,
  addEvidence,
  fetchDirectoryMe,
  fetchProjectContext,
  fetchWeather,
};
