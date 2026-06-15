// tasksApi.js — Iter150 (Phase A) + TRACK 14.0-RC1-FERRARI (2026-02-15).
//
// Thin client for the tasks + notifications shared services. Routed
// through the shared `api` axios instance — auto-injects all portal
// tokens via the request interceptor and absorbs namespaced 401s.
//
// TRACK 14.0-RC1-FERRARI: `skipSessionStatus: true` on every call
// because notifications/tasks are background-polled / dashboard-
// embedded. A 401 (e.g. token rotation in flight, or a widget
// rendered without the matching portal grant) must NEVER raise the
// global Session Expired modal over valid content. Local empty
// states / counts handle the recovery.
import { api } from "@/lib/api";

function _opts(extra = {}) {
  // Track 14.0-NOTIFY-OWNERSHIP-LOCK D3 — additive Asset Admin scope.
  // When the directory record carries `is_asset_admin=true` (mirrored
  // into localStorage on multi-login), forward the flag so backend
  // OR-extends the notification feed with the `asset_admin` slice.
  const headers = {};
  try {
    if (typeof window !== "undefined" &&
        window.localStorage.getItem("masci.is_asset_admin") === "true") {
      headers["X-Asset-Admin"] = "1";
    }
  } catch (e) { /* ignore */ }
  return { skipSessionStatus: true, headers, ...extra };
}

export async function listTasks(params = {}) {
  const r = await api.get("/tasks", { ..._opts(), params });
  return r.data;
}
export async function getTaskSummary() {
  const r = await api.get("/tasks/summary", _opts());
  return r.data;
}
export async function getTask(id) {
  const r = await api.get(`/tasks/${id}`, _opts());
  return r.data;
}
export async function patchTask(id, patch) {
  const r = await api.patch(`/tasks/${id}`, patch, _opts());
  return r.data;
}
export async function commentTask(id, body) {
  const r = await api.post(`/tasks/${id}/comment`, { body }, _opts());
  return r.data;
}

export async function listNotifications(params = {}) {
  const r = await api.get("/notifications", { ..._opts(), params });
  return r.data;
}
export async function getUnreadCount() {
  try {
    const r = await api.get("/notifications/unread-count", _opts());
    return r.data?.unread || 0;
  } catch { return 0; }
}
export async function markRead(id) {
  return api.post(`/notifications/${id}/read`, {}, _opts());
}
export async function markAllRead() {
  return api.post("/notifications/read-all", {}, _opts());
}
export async function acknowledge(id) {
  return api.post(`/notifications/${id}/acknowledge`, {}, _opts());
}
