// poApi.js — Iter153 (Phase D). Thin client for /api/po-requests.
import axios from "axios";
import { getAdminToken } from "@/lib/adminAuth";
import { getHrToken } from "@/lib/hrAuth";
import { getSafetyToken } from "@/lib/safetyAuth";
import { getPmToken } from "@/lib/pmAuth";
import { getShopToken } from "@/lib/shopAuth";
import { getDispatchToken } from "@/lib/dispatchAuth";
import { getLeadershipToken } from "@/lib/leadershipAuth";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function authHeaders() {
  const h = {};
  const a = getAdminToken(); if (a) h["X-Admin-Token"] = a;
  const hr = getHrToken(); if (hr) h["X-HR-Token"] = hr;
  const s = getSafetyToken(); if (s) h["X-Safety-Token"] = s;
  const p = getPmToken(); if (p) h["X-PM-Token"] = p;
  const sh = getShopToken(); if (sh) h["X-Shop-Token"] = sh;
  const d = getDispatchToken(); if (d) h["X-Dispatch-Token"] = d;
  const l = getLeadershipToken(); if (l) h["X-Leadership-Token"] = l;
  return h;
}

export const PO_CATEGORIES = [
  "Materials", "Small tools", "Safety supplies", "Fuel",
  "Equipment repair", "Rental", "Subcontractor support",
  "Office/admin", "Emergency purchase", "Other",
];
export const PO_URGENCY = ["Normal", "Urgent", "Emergency"];

export async function listPos(params = {}) {
  const r = await axios.get(`${API}/po-requests`, { headers: authHeaders(), params });
  return r.data;
}
export async function poSummary() {
  const r = await axios.get(`${API}/po-requests/summary`, { headers: authHeaders() });
  return r.data;
}
export async function getPo(id) {
  const r = await axios.get(`${API}/po-requests/${id}`, { headers: authHeaders() });
  return r.data;
}
export async function submitPo(body) {
  const r = await axios.post(`${API}/po-requests`, body, { headers: authHeaders() });
  return r.data;
}
export async function approvePo(id, action, payload = {}) {
  const r = await axios.post(`${API}/po-requests/${id}/approve`,
    { action, ...payload }, { headers: authHeaders() });
  return r.data;
}
export async function uploadReceipt(id, file, amount, notes) {
  const fd = new FormData();
  fd.append("file", file);
  if (amount !== undefined && amount !== null && amount !== "") fd.append("receipt_amount", amount);
  if (notes) fd.append("receipt_notes", notes);
  const r = await axios.post(`${API}/po-requests/${id}/receipt`, fd,
    { headers: { ...authHeaders(), "Content-Type": "multipart/form-data" } });
  return r.data;
}
export async function closePo(id) {
  const r = await axios.post(`${API}/po-requests/${id}/close`, {}, { headers: authHeaders() });
  return r.data;
}
export async function cancelPo(id) {
  const r = await axios.post(`${API}/po-requests/${id}/cancel`, {}, { headers: authHeaders() });
  return r.data;
}
export async function respondClarification(id, response) {
  const r = await axios.post(`${API}/po-requests/${id}/respond-clarification`,
    { response }, { headers: authHeaders() });
  return r.data;
}
export function poExportCsvUrl(params = {}) {
  const qp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "" && v !== false) qp.set(k, String(v));
  });
  return `${API}/po-requests/export.csv${qp.toString() ? "?" + qp.toString() : ""}`;
}
export async function downloadPoExportCsv(params = {}) {
  // Streams the CSV with auth headers (anchor download can't carry headers).
  const r = await axios.get(`${API}/po-requests/export.csv`, {
    headers: authHeaders(), params, responseType: "blob",
  });
  const url = URL.createObjectURL(r.data);
  const a = document.createElement("a");
  a.href = url;
  a.download = `masci-po-requests-${new Date().toISOString().slice(0,10)}.csv`;
  document.body.appendChild(a); a.click();
  setTimeout(() => { URL.revokeObjectURL(url); a.remove(); }, 1000);
}
