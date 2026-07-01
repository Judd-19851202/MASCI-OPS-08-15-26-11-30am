// Track 19.16 · Phase B1 · Incident Intelligence Engine — HTTP adapter.
// Thin wrapper around the Phase A `/api/incident-cases/*` endpoints. All
// calls include cross-portal auth headers (Safety / Admin / PM) via the
// shared helper.

import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Pull whichever portal token is present. Order mirrors the backend
// `make_require_safety_admin_or_pm` gate.
function _authHeaders() {
  const h = {};
  try {
    const safety = window.localStorage.getItem("safety_token");
    const admin = window.localStorage.getItem("admin_token");
    const pm = window.localStorage.getItem("pm_token");
    if (safety) h["X-Safety-Token"] = safety;
    if (admin) h["X-Admin-Token"] = admin;
    if (pm) h["X-PM-Token"] = pm;
  } catch { /* noop */ }
  return h;
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

export default {
  fetchVocabulary,
  createCase,
  patchFieldBlock,
  transitionCase,
  addEvidence,
};
