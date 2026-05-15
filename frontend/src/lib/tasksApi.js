// tasksApi.js — Iter150 (Phase A). Thin client for the tasks +
// notifications shared services. Uses the existing /api/* base and
// forwards whichever portal token is live.
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

export async function listTasks(params = {}) {
  const r = await axios.get(`${API}/tasks`, { headers: authHeaders(), params });
  return r.data;
}
export async function getTaskSummary() {
  const r = await axios.get(`${API}/tasks/summary`, { headers: authHeaders() });
  return r.data;
}
export async function getTask(id) {
  const r = await axios.get(`${API}/tasks/${id}`, { headers: authHeaders() });
  return r.data;
}
export async function patchTask(id, patch) {
  const r = await axios.patch(`${API}/tasks/${id}`, patch, { headers: authHeaders() });
  return r.data;
}
export async function commentTask(id, body) {
  const r = await axios.post(`${API}/tasks/${id}/comment`, { body }, { headers: authHeaders() });
  return r.data;
}

export async function listNotifications(params = {}) {
  const r = await axios.get(`${API}/notifications`, { headers: authHeaders(), params });
  return r.data;
}
export async function getUnreadCount() {
  try {
    const r = await axios.get(`${API}/notifications/unread-count`, { headers: authHeaders() });
    return r.data?.unread || 0;
  } catch { return 0; }
}
export async function markRead(id) {
  return axios.post(`${API}/notifications/${id}/read`, {}, { headers: authHeaders() });
}
export async function markAllRead() {
  return axios.post(`${API}/notifications/read-all`, {}, { headers: authHeaders() });
}
export async function acknowledge(id) {
  return axios.post(`${API}/notifications/${id}/acknowledge`, {}, { headers: authHeaders() });
}
