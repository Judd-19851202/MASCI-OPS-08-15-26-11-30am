import axios from "axios";
import { getDirectoryToken } from "@/lib/directoryAuth";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function headers() {
  const out = { "Content-Type": "application/json" };
  try {
    const admin =
      localStorage.getItem("masci.admin.token") ||
      localStorage.getItem("adminToken") ||
      localStorage.getItem("admin_token") ||
      "";
    const directory = getDirectoryToken();
    if (admin) out["X-Admin-Token"] = admin;
    if (directory) out["X-Directory-Token"] = directory;
  } catch {
    // ignore storage access failures
  }
  return out;
}

const client = () => axios.create({ baseURL: API, headers: headers(), timeout: 45000 });

export async function listOperationalCases(params = {}) {
  const { data } = await client().get("/admin/operations-control/cases", { params });
  return data;
}

export async function getOperationalCase(caseId) {
  const { data } = await client().get(`/admin/operations-control/cases/${encodeURIComponent(caseId)}`);
  return data;
}

export async function getOperationalCaseAssembly(caseId) {
  const { data } = await client().get(`/admin/operations-control/cases/${encodeURIComponent(caseId)}/assembly`);
  return data;
}

export async function getOperationalCaseTimeline(caseId) {
  const { data } = await client().get(`/admin/operations-control/cases/${encodeURIComponent(caseId)}/timeline`);
  return data;
}

export async function getOperationalCaseGraph(caseId) {
  const { data } = await client().get(`/admin/operations-control/cases/${encodeURIComponent(caseId)}/graph`);
  return data;
}

export async function transitionOperationalCase(caseId, body) {
  const { data } = await client().post(`/admin/operations-control/cases/${encodeURIComponent(caseId)}/transitions`, body);
  return data;
}

export async function createOperationalCaseTask(caseId, body) {
  const { data } = await client().post(`/admin/operations-control/cases/${encodeURIComponent(caseId)}/tasks`, body);
  return data;
}

export async function acknowledgeOperationalCaseCommunication(caseId, communicationId, body = {}) {
  const { data } = await client().post(
    `/admin/operations-control/cases/${encodeURIComponent(caseId)}/communications/${encodeURIComponent(communicationId)}/ack`,
    body,
  );
  return data;
}

export async function linkOperationalRelatedCase(caseId, body) {
  const { data } = await client().post(`/admin/operations-control/cases/${encodeURIComponent(caseId)}/related`, body);
  return data;
}

export async function captureOperationalCaseEvidence(caseId) {
  const { data } = await client().post(`/admin/operations-control/cases/${encodeURIComponent(caseId)}/evidence`, {});
  return data;
}

export async function includeOperationalCaseBaseline(caseId, body) {
  const { data } = await client().post(`/admin/operations-control/cases/${encodeURIComponent(caseId)}/baseline`, body);
  return data;
}

export async function exportOperationalCase(caseId) {
  const { data } = await client().post(`/admin/operations-control/cases/${encodeURIComponent(caseId)}/export`, {});
  return data;
}

export async function createPreviewOperationalCaseCertification() {
  const { data } = await client().post("/admin/operations-control/certifications/preview-daily-report", {});
  return data;
}

export async function runOperationalCaseCertification() {
  const { data } = await client().post("/admin/operations-control/certifications/run", {});
  return data;
}
