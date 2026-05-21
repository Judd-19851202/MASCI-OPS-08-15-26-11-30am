// employeesApi.js — Iter152 (Phase C). Thin client for HR employee
// lifecycle management.
import axios from "axios";
import { getAdminToken } from "@/lib/adminAuth";
import { getHrToken } from "@/lib/hrAuth";
import { getSafetyToken } from "@/lib/safetyAuth";
import { getPmToken } from "@/lib/pmAuth";
import { getShopToken } from "@/lib/shopAuth";
import { getDispatchToken } from "@/lib/dispatchAuth";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function authHeaders() {
  const h = {};
  const a = getAdminToken(); if (a) h["X-Admin-Token"] = a;
  const hr = getHrToken(); if (hr) h["X-HR-Token"] = hr;
  const s = getSafetyToken(); if (s) h["X-Safety-Token"] = s;
  const p = getPmToken(); if (p) h["X-PM-Token"] = p;
  const sh = getShopToken(); if (sh) h["X-Shop-Token"] = sh;
  const d = getDispatchToken(); if (d) h["X-Dispatch-Token"] = d;
  return h;
}

export const LIFECYCLE_STATUSES = [
  "Pending Hire", "Active", "Seasonal", "Leave of Absence",
  "Inactive", "Suspended", "Terminated", "Resigned", "Retired",
];

export async function listHrEmployees(params = {}) {
  const r = await axios.get(`${API}/hr/employees`, { headers: authHeaders(), params });
  return r.data;
}
export async function createHrEmployee(body, opts = {}) {
  const { force = false } = opts;
  const r = await axios.post(
    `${API}/hr/employees`,
    body,
    { headers: authHeaders(), params: force ? { force: "true" } : {} },
  );
  return r.data;
}

// iter316 · Reactivate / rehire — flips an inactive/terminated employee
// back to Active or Pending Hire, preserving original_hire_date.
export async function reactivateHrEmployee(id, body) {
  const r = await axios.post(
    `${API}/hr/employees/${id}/reactivate`,
    body,
    { headers: authHeaders() },
  );
  return r.data;
}
export async function patchHrEmployee(id, patch) {
  const r = await axios.patch(`${API}/hr/employees/${id}`, patch, { headers: authHeaders() });
  return r.data;
}
export async function changeHrEmployeeStatus(id, lifecycle_status, reason, extra) {
  const body = { lifecycle_status, reason, ...(extra || {}) };
  // The caller may pass `extra` containing lifecycle_status/reason — the
  // explicit args take precedence so the API contract stays stable.
  body.lifecycle_status = lifecycle_status;
  body.reason = reason;
  const r = await axios.post(`${API}/hr/employees/${id}/status`,
    body, { headers: authHeaders() });
  return r.data;
}
export async function offboardingSummary(id) {
  const r = await axios.get(`${API}/hr/employees/${id}/offboarding-summary`,
    { headers: authHeaders() });
  return r.data;
}
