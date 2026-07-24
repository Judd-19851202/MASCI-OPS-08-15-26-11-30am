// employeesApi.js — Iter152 (Phase C). Thin client for HR employee
// lifecycle management.
//
// TRACK 19.03 · HR is gospel. Every successful HR write here emits
// the `hr:roster-changed` bus event so every employee picker on the
// page (EmployeeCombo, trench EmployeePicker, every dropdown that
// subscribes to `lib/hrRoster.js`) re-fetches the canonical roster
// instantly — no page reload, no stale cache, no delayed sync.
import axios from "axios";
import { getAdminToken } from "@/lib/adminAuth";
import { getHrToken } from "@/lib/hrAuth";
import { getSafetyToken } from "@/lib/safetyAuth";
import { getPmToken } from "@/lib/pmAuth";
import { getShopToken } from "@/lib/shopAuth";
import { getDispatchToken } from "@/lib/dispatchAuth";
import { emitHrRosterChanged } from "@/lib/hrRoster";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function authHeaders() {
  return buildScopedPortalAuthHeaders(["admin", "hr", "safety", "pm", "shop", "dispatch"]);
}

export const LIFECYCLE_STATUSES = [
  "Pending Hire", "Active", "Seasonal", "Leave of Absence",
  "Inactive", "Suspended", "Terminated", "Resigned", "Retired",
];

// TRACK 27.00 · Canonical employment buckets — MUST stay in sync with
// /app/backend/lib/employee_status.py::BUCKET_STATUSES. If you edit
// one, edit both. The bucket is the primary HR filter primitive; the
// detailed lifecycle_status is a secondary filter used to narrow
// within a bucket.
//
// TRACK 27.02 label cleanup — human-clear names. HR sees "Active" in
// both dropdowns; the two are mapped through the canonical resolver
// so picking Active in EITHER dropdown returns the same rowset.
export const EMPLOYMENT_BUCKETS = [
  { value: "any",        label: "All employees" },
  { value: "active",     label: "Active",                  statuses: ["Active", "Seasonal", "Leave of Absence"] },
  { value: "pending",    label: "Pending / Onboarding",    statuses: ["Pending Hire"] },
  { value: "off_roll",   label: "Off-roll / Inactive",     statuses: ["Inactive", "Suspended"] },
  { value: "terminated", label: "Terminated / Separated",  statuses: ["Terminated", "Resigned"] },
  { value: "retired",    label: "Retired",                 statuses: ["Retired"] },
];

export function statusesForBucket(bucketValue) {
  const b = EMPLOYMENT_BUCKETS.find((x) => x.value === bucketValue);
  return b?.statuses || null;   // null means "any"
}

export async function fetchHrFacets() {
  const r = await axios.get(`${API}/hr/employees/facets`, { headers: authHeaders() });
  return r.data;
}

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
  emitHrRosterChanged();
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
  emitHrRosterChanged();
  return r.data;
}
export async function patchHrEmployee(id, patch) {
  const r = await axios.patch(`${API}/hr/employees/${id}`, patch, { headers: authHeaders() });
  emitHrRosterChanged();
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
  emitHrRosterChanged();
  return r.data;
}
export async function offboardingSummary(id) {
  const r = await axios.get(`${API}/hr/employees/${id}/offboarding-summary`,
    { headers: authHeaders() });
  return r.data;
}
