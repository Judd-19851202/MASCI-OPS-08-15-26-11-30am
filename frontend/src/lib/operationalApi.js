// operationalApi.js — Phase V-Prelude · Wave 1.
//
// Thin client for the V-Prelude substrate endpoints. Uses the shared
// `api` axios instance from `@/lib/api` so all portal tokens
// (admin/PM/HR/safety/dispatch/FL/etc.) are attached automatically via
// the existing interceptor chain. NO state — pure call/response.

import { api } from "@/lib/api";

function _err(e) {
  const detail = e?.response?.data?.detail || e?.message || "Request failed";
  const err = new Error(detail);
  err.status = e?.response?.status;
  err.detail = e?.response?.data?.detail;
  return err;
}

// ── Operational Constraints ──────────────────────────────────────────

export async function listConstraints(params = {}) {
  try {
    const r = await api.get(`/constraints`, { params });
    return r.data;
  } catch (e) { throw _err(e); }
}

export async function getConstraint(id) {
  try {
    const r = await api.get(`/constraints/${encodeURIComponent(id)}`);
    return r.data;
  } catch (e) { throw _err(e); }
}

export async function createConstraint(body) {
  try {
    const r = await api.post(`/constraints`, body);
    return r.data;
  } catch (e) { throw _err(e); }
}

export async function patchConstraint(id, body) {
  try {
    const r = await api.patch(`/constraints/${encodeURIComponent(id)}`, body);
    return r.data;
  } catch (e) { throw _err(e); }
}

export async function resolveConstraint(id, resolution_note) {
  try {
    const r = await api.post(
      `/constraints/${encodeURIComponent(id)}/resolve`,
      { resolution_note },
    );
    return r.data;
  } catch (e) { throw _err(e); }
}

export async function appendChronology(id, action, note) {
  try {
    const r = await api.post(
      `/constraints/${encodeURIComponent(id)}/chronology`,
      { action, note },
    );
    return r.data;
  } catch (e) { throw _err(e); }
}

// ── Operational Links ────────────────────────────────────────────────

export async function listLinks(params = {}) {
  try {
    const r = await api.get(`/operational-links`, { params });
    return r.data;
  } catch (e) { throw _err(e); }
}

export async function createLink(body) {
  try {
    const r = await api.post(`/operational-links`, body);
    return r.data;
  } catch (e) { throw _err(e); }
}

export async function archiveLink(id, reason = "") {
  try {
    const r = await api.patch(
      `/operational-links/${encodeURIComponent(id)}/status`,
      { status: "archived", reason },
    );
    return r.data;
  } catch (e) { throw _err(e); }
}

export async function voidLink(id, reason = "") {
  try {
    const r = await api.patch(
      `/operational-links/${encodeURIComponent(id)}/status`,
      { status: "voided", reason },
    );
    return r.data;
  } catch (e) { throw _err(e); }
}

// ── Timeline (read-only aggregator) ─────────────────────────────────

export async function getTimeline(project_id, { from, to } = {}) {
  try {
    const r = await api.get(`/timeline`, {
      params: { project_id, ...(from ? { from } : {}), ...(to ? { to } : {}) },
    });
    return r.data;
  } catch (e) { throw _err(e); }
}

// ── Photo Governance ────────────────────────────────────────────────

export async function getPhotoGovernance(photo_id) {
  try {
    const r = await api.get(
      `/photos/${encodeURIComponent(photo_id)}/governance`,
    );
    return r.data;
  } catch (e) { throw _err(e); }
}

export async function patchPhoto(photo_id, body) {
  try {
    const r = await api.patch(
      `/photos/${encodeURIComponent(photo_id)}`,
      body,
    );
    return r.data;
  } catch (e) { throw _err(e); }
}

export async function linkPhoto(photo_id, body) {
  try {
    const r = await api.post(
      `/photos/${encodeURIComponent(photo_id)}/link`,
      body,
    );
    return r.data;
  } catch (e) { throw _err(e); }
}
