// docExpirationsApi.js — Iter151 (Phase B). Thin client for the
// /api/document-expirations service.
import axios from "axios";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function authHeaders() {
  return buildScopedPortalAuthHeaders(["admin", "safety", "hr", "pm", "shop", "dispatch"]);
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
