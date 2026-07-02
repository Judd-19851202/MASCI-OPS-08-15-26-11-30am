// Track 19.21b · Historical Records Intake — API client
//
// Wraps every /api/employee-records/* endpoint. Reads the correct
// per-portal token (HR / Safety / Shop-Asset-Admin / Admin) so the
// backend gate can identify the actor's role and enforce lane RBAC.
//
// Zero drift: pure fetch wrapper — no state, no side effects beyond
// network calls.
import { getHrToken } from "@/lib/hrAuth";
import { getSafetyToken } from "@/lib/safetyAuth";
import { getAdminToken } from "@/lib/adminAuth";
import { getShopToken } from "@/lib/shopAuth";

const API = `${process.env.REACT_APP_BACKEND_URL}/api/employee-records`;

export function authHeaders() {
  const h = {};
  const hr = getHrToken();     if (hr) h["X-HR-Token"] = hr;
  const sf = getSafetyToken(); if (sf) h["X-Safety-Token"] = sf;
  const sh = getShopToken();   if (sh) h["X-Shop-Token"] = sh;
  const ad = getAdminToken();  if (ad) h["X-Admin-Token"] = ad;
  return h;
}

async function _json(res) {
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try { const j = await res.json(); msg = j.detail || j.message || msg; } catch { /* ignore */ }
    throw new Error(msg);
  }
  return res.json();
}

export async function fetchVocabulary() {
  const res = await fetch(`${API}/vocabulary`, { headers: authHeaders() });
  return _json(res);
}

export async function fetchQueue(lane) {
  const res = await fetch(`${API}/queues/${lane}`, { headers: authHeaders() });
  return _json(res);
}

export async function fetchRecord(recordId) {
  const res = await fetch(`${API}/records/${recordId}`, { headers: authHeaders() });
  return _json(res);
}

export async function listRecords({ lane, state, employee_id, batch_id, record_type, limit } = {}) {
  const p = new URLSearchParams();
  if (lane) p.set("lane", lane);
  if (state) p.set("state", state);
  if (employee_id) p.set("employee_id", employee_id);
  if (batch_id) p.set("batch_id", batch_id);
  if (record_type) p.set("record_type", record_type);
  if (limit) p.set("limit", String(limit));
  const res = await fetch(`${API}/records?${p.toString()}`, { headers: authHeaders() });
  return _json(res);
}

export async function fetchEmployeeRecords(empId, { include_pending, lane } = {}) {
  const p = new URLSearchParams();
  if (include_pending) p.set("include_pending", "true");
  if (lane) p.set("lane", lane);
  const res = await fetch(`${API}/employees/${empId}/records?${p.toString()}`, {
    headers: authHeaders(),
  });
  return _json(res);
}

export async function uploadOriginalFile({ lane, file }) {
  const fd = new FormData();
  fd.append("lane", lane);
  fd.append("file", file);
  const res = await fetch(`${API}/uploads`, {
    method: "POST",
    body: fd,
    headers: authHeaders(),
  });
  return _json(res);
}

export async function createRecord(body) {
  const res = await fetch(`${API}/records`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
  });
  return _json(res);
}

export async function approveRecord(recordId, notes = "") {
  const res = await fetch(`${API}/records/${recordId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ notes }),
  });
  return _json(res);
}

export async function rejectRecord(recordId, reason) {
  const res = await fetch(`${API}/records/${recordId}/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ reason }),
  });
  return _json(res);
}

export async function reassignRecord(recordId, patch) {
  const res = await fetch(`${API}/records/${recordId}/reassign`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(patch),
  });
  return _json(res);
}
