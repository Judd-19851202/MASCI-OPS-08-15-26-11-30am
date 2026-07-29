// signaturesApi.js — Iter154 (Phase F). Thin client for the unified
// signature engine.
import axios from "axios";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function authHeaders() {
  return buildScopedPortalAuthHeaders(["admin", "hr", "safety", "pm", "shop", "dispatch", "fl"]);
}

export const SIGNATURE_TYPES = [
  "supervisor", "employee", "witness", "approver",
  "receiver", "inspector", "trainer", "trainee", "other",
];

export async function captureSignature(body) {
  const r = await axios.post(`${API}/signatures`, body, { headers: authHeaders() });
  return r.data;
}

export async function listSignatures(params = {}) {
  const r = await axios.get(`${API}/signatures`, { headers: authHeaders(), params });
  return r.data;
}
