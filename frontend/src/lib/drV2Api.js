/*
 * DR-ROI-001 · Phase C · Daily Report V2 API client.
 *
 * ISOLATED axios client. Never imports from lib/api.js so V1 auth
 * interceptors and V1 error toasts never fire for V2 supervisor
 * flows. Zero drift on V1 network layer.
 */
import axios from "axios";

const BASE = `${process.env.REACT_APP_BACKEND_URL}/api/dr-v2`;

const client = axios.create({
  baseURL: BASE,
  timeout: 45000,
  headers: { "Content-Type": "application/json" },
});

/** GET /api/dr-v2/meta — provider + feature flag state. */
export async function fetchDrV2Meta() {
  const { data } = await client.get("/meta");
  return data;
}

/** POST /api/dr-v2/drafts — save/update supervisor V2 draft. */
export async function saveDrV2Draft(payload) {
  const { data } = await client.post("/drafts", payload);
  return data;
}

/** GET /api/dr-v2/drafts/:id */
export async function readDrV2Draft(reportId) {
  const { data } = await client.get(`/drafts/${encodeURIComponent(reportId)}`);
  return data;
}

/** POST /api/dr-v2/ai/synthesize — cached agent synthesis. */
export async function synthesizeDrV2Ai({ report_id, force = false, agents = null }) {
  const body = { report_id, force };
  if (agents) body.agents = agents;
  const { data } = await client.post("/ai/synthesize", body);
  return data;
}

/** POST /api/dr-v2/ai/approve — supervisor decision. */
export async function approveDrV2Ai({ report_id, action, agent, edited_narrative, supervisor_id, reason }) {
  const { data } = await client.post("/ai/approve", {
    report_id, action, agent, edited_narrative, supervisor_id, reason,
  });
  return data;
}

/** GET /api/dr-v2/ai/audit/:id — append-only audit trail. */
export async function auditDrV2Ai(reportId) {
  const { data } = await client.get(`/ai/audit/${encodeURIComponent(reportId)}`);
  return data;
}

export default {
  fetchDrV2Meta,
  saveDrV2Draft,
  readDrV2Draft,
  synthesizeDrV2Ai,
  approveDrV2Ai,
  auditDrV2Ai,
};
