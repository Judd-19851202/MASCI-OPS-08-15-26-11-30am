// Track 19.16 · Phase B1 · Incident Intelligence Engine — HTTP adapter.
// Thin wrapper around the Phase A `/api/incident-cases/*` endpoints. All
// calls include the governed incident-report auth contract via the
// shared helper.

import { api } from "@/lib/api";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";

function _authHeaders() {
  return buildScopedPortalAuthHeaders(["safety", "admin", "pm", "field_leadership"]);
}

export async function fetchVocabulary() {
  const { data } = await api.get("/incident-cases/vocabulary", { headers: _authHeaders() });
  return data;
}

export async function createCase(fieldBlock) {
  const { data } = await api.post(
    "/incident-cases",
    { field_block: fieldBlock },
    { headers: _authHeaders() },
  );
  return data;
}

export async function patchFieldBlock(caseId, patch) {
  const { data } = await api.patch(
    `/incident-cases/${caseId}/field-block`,
    { patch },
    { headers: _authHeaders() },
  );
  return data;
}

export async function transitionCase(caseId, toState, reason = "") {
  const { data } = await api.post(
    `/incident-cases/${caseId}/transitions`,
    { to_state: toState, reason },
    { headers: _authHeaders() },
  );
  return data;
}

export async function addEvidence(caseId, payload) {
  const { data } = await api.post(
    `/incident-cases/${caseId}/evidence`,
    payload,
    { headers: _authHeaders() },
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
    const { data } = await api.get("/auth/me-directory", { headers, skipSessionStatus: true });
    return data?.user || null;
  } catch {
    return null;
  }
}

// Canonical project row + last-known superintendent.
export async function fetchProjectContext(projectNumber) {
  if (!projectNumber) return null;
  try {
    const { data } = await api.get(
      `/incident-intelligence/project-context/${encodeURIComponent(projectNumber)}`,
      { headers: _authHeaders() },
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
    const { data } = await api.get(
      `/incident-intelligence/weather?lat=${lat}&lng=${lng}`,
      { headers: _authHeaders() },
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
