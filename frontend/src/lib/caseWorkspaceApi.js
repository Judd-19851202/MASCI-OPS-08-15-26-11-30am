// Track 19.16 · Phase C · Safety Case Workspace — HTTP client.
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function headers() {
  const h = { "Content-Type": "application/json" };
  try {
    const s = localStorage.getItem("safety_token");
    const a = localStorage.getItem("admin_token");
    const p = localStorage.getItem("pm_token");
    if (s) h["X-Safety-Token"] = s;
    if (a) h["X-Admin-Token"] = a;
    if (p) h["X-PM-Token"] = p;
  } catch { /* noop */ }
  return h;
}
const c = () => axios.create({ baseURL: API, headers: headers(), timeout: 20000 });

// Core case
export async function getCase(id) { const {data} = await c().get(`/incident-cases/${id}`); return data; }
export async function listTimeline(id) { const {data} = await c().get(`/incident-cases/${id}/timeline`); return data; }
export async function listEvidence(id) { const {data} = await c().get(`/incident-cases/${id}/evidence`); return data; }
export async function updateSafetyBlock(id, patch) { const {data} = await c().patch(`/incident-cases/${id}/safety-block`, {patch}); return data; }
export async function transition(id, to_state, reason="") { const {data} = await c().post(`/incident-cases/${id}/transitions`, {to_state, reason}); return data; }

// Satellites
export async function listCommunications(id) { const {data} = await c().get(`/incident-cases/${id}/communications`); return data; }
export async function addCommunication(id, body) { const {data} = await c().post(`/incident-cases/${id}/communications`, body); return data; }

export async function listWitnesses(id) { const {data} = await c().get(`/incident-cases/${id}/witnesses`); return data; }
export async function addWitness(id, body) { const {data} = await c().post(`/incident-cases/${id}/witnesses`, body); return data; }
export async function updateWitness(id, witnessId, patch) { const {data} = await c().patch(`/incident-cases/${id}/witnesses/${witnessId}`, {patch}); return data; }

export async function listMedical(id) { const {data} = await c().get(`/incident-cases/${id}/medical`); return data; }
export async function addMedical(id, body) { const {data} = await c().post(`/incident-cases/${id}/medical`, body); return data; }

export async function listAgency(id) { const {data} = await c().get(`/incident-cases/${id}/agency-contacts`); return data; }
export async function addAgency(id, body) { const {data} = await c().post(`/incident-cases/${id}/agency-contacts`, body); return data; }

export async function listTasks(id) { const {data} = await c().get(`/incident-cases/${id}/tasks`); return data; }
export async function addTask(id, body) { const {data} = await c().post(`/incident-cases/${id}/tasks`, body); return data; }
export async function updateTask(id, taskId, patch) { const {data} = await c().patch(`/incident-cases/${id}/tasks/${taskId}`, {patch}); return data; }

export async function listCorrectiveActions(id) { const {data} = await c().get(`/corrective-actions`, {params: {consumer_kind: "incident_case", consumer_id: id}}); return data; }
export async function addCorrectiveAction(body) { const {data} = await c().post(`/corrective-actions`, body); return data; }
export async function verifyCorrectiveAction(actionId, notes="") { const {data} = await c().post(`/corrective-actions/${actionId}/verify`, {verification_notes: notes}); return data; }

// Health + Exec snapshot
export async function getHealth(id) { const {data} = await c().get(`/incident-cases/${id}/health`); return data; }
export async function getExecutiveSnapshot(id) { const {data} = await c().get(`/incident-cases/${id}/executive-snapshot`); return data; }
