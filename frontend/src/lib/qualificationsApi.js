// TRACK 23.10-B · Professional Qualifications Engine API client.
// Reads: any authenticated portal token. Writes: HR / Safety-Training-admin / Admin.
import axios from "axios";
import { getHrToken } from "@/lib/hrAuth";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function authHeaders() {
  // HR Portal is the primary write surface. Attach both HR and Admin
  // headers when available so the multi-role gate resolves cleanly.
  const headers = { "Content-Type": "application/json" };
  const hr = getHrToken();
  if (hr) headers["X-HR-Token"] = hr;
  try {
    const adm = window.localStorage.getItem("adminToken");
    if (adm) headers["X-Admin-Token"] = adm;
  } catch (e) {
    // localStorage may be blocked — ignore.
  }
  try {
    const saf = window.localStorage.getItem("safety_token");
    if (saf) headers["X-Safety-Token"] = saf;
  } catch (e) {
    // ignore
  }
  return headers;
}

export async function listQualificationTypes() {
  const r = await axios.get(`${API}/employees/qualifications/types`, {
    headers: authHeaders(),
  });
  return r.data;
}

export async function listActiveQualifications(type, warningDays = 30) {
  const r = await axios.get(`${API}/employees/qualifications`, {
    params: { type, active: true, warning_days: warningDays },
    headers: authHeaders(),
  });
  return r.data;
}

export async function qualificationSummary(type, warningDays = 30) {
  const r = await axios.get(`${API}/employees/qualifications/summary`, {
    params: { type, warning_days: warningDays },
    headers: authHeaders(),
  });
  return r.data;
}

export async function employeeQualifications(employeeId, opts = {}) {
  const r = await axios.get(
    `${API}/employees/${encodeURIComponent(employeeId)}/qualifications`,
    {
      params: {
        type: opts.type || undefined,
        include_history: opts.includeHistory ? true : false,
      },
      headers: authHeaders(),
    },
  );
  return r.data;
}

export async function createQualification(body) {
  const r = await axios.post(`${API}/hr/qualifications`, body, {
    headers: authHeaders(),
  });
  return r.data;
}

export async function updateQualification(qid, body) {
  const r = await axios.patch(
    `${API}/hr/qualifications/${encodeURIComponent(qid)}`,
    body,
    { headers: authHeaders() },
  );
  return r.data;
}

export async function transitionQualification(qid, action, reason) {
  const r = await axios.post(
    `${API}/hr/qualifications/${encodeURIComponent(qid)}/${action}`,
    { reason },
    { headers: authHeaders() },
  );
  return r.data;
}

export async function renewQualification(qid, payload) {
  const r = await axios.post(
    `${API}/hr/qualifications/${encodeURIComponent(qid)}/renew`,
    payload,
    { headers: authHeaders() },
  );
  return r.data;
}

export async function qualificationSnapshot(qid) {
  const r = await axios.get(
    `${API}/hr/qualifications/${encodeURIComponent(qid)}/snapshot`,
    { headers: authHeaders() },
  );
  return r.data;
}
