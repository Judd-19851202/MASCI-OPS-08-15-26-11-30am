// docExpirationsApi.js — Iter151 (Phase B). Thin client for the
// /api/document-expirations service.
import axios from "axios";
import { getAdminToken } from "@/lib/adminAuth";
import { getSafetyToken } from "@/lib/safetyAuth";
import { getHrToken } from "@/lib/hrAuth";
import { getPmToken } from "@/lib/pmAuth";
import { getShopToken } from "@/lib/shopAuth";
import { getDispatchToken } from "@/lib/dispatchAuth";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function authHeaders() {
  const h = {};
  const a = getAdminToken(); if (a) h["X-Admin-Token"] = a;
  const s = getSafetyToken(); if (s) h["X-Safety-Token"] = s;
  const hr = getHrToken(); if (hr) h["X-HR-Token"] = hr;
  const p = getPmToken(); if (p) h["X-PM-Token"] = p;
  const sh = getShopToken(); if (sh) h["X-Shop-Token"] = sh;
  const d = getDispatchToken(); if (d) h["X-Dispatch-Token"] = d;
  return h;
}

export async function listExpirations(params = {}) {
  const r = await axios.get(`${API}/document-expirations`, { headers: authHeaders(), params });
  return r.data;
}
export async function summary() {
  const r = await axios.get(`${API}/document-expirations/summary`, { headers: authHeaders() });
  return r.data;
}
export async function createExpiration(body) {
  const r = await axios.post(`${API}/document-expirations`, body, { headers: authHeaders() });
  return r.data;
}
export async function patchExpiration(id, patch) {
  const r = await axios.patch(`${API}/document-expirations/${id}`, patch, { headers: authHeaders() });
  return r.data;
}
export async function archiveExpiration(id) {
  return axios.delete(`${API}/document-expirations/${id}`, { headers: authHeaders() });
}
export async function adminScan() {
  return axios.post(`${API}/admin/document-expirations/scan`, {}, { headers: authHeaders() });
}
export async function adminScanPreview() {
  const r = await axios.get(`${API}/admin/document-expirations/scan/preview`, { headers: authHeaders() });
  return r.data;
}
