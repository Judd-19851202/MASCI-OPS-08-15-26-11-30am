// odrApi.js — Phase V.1 · M0.3 frontend client.
//
// Thin axios wrapper for the ODR substrate (M0.1) + engines (M0.2) +
// guidance (M0.2A) + observation (M0.3). Uses the existing `api`
// instance so portal tokens (Admin / PM / FL / etc.) attach via the
// shared interceptor.
//
// Doctrine:
//   /app/memory/ODR_DATA_MODEL.md
//   /app/memory/M0_2A_OPERATOR_REVIEW_GUIDE.md
//   /app/memory/ODR_TRUST_BANNER_DOCTRINE.md
//   /app/memory/ODR_ADOPTION_OBSERVATION_PLAN.md
//
// All functions throw on non-2xx with a normalized Error carrying
// `status` + `detail`.

import { api } from "@/lib/api";

function _err(e) {
  const detail = e?.response?.data?.detail || e?.message || "Request failed";
  const err = new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  err.status = e?.response?.status;
  err.detail = e?.response?.data?.detail;
  return err;
}

// ── ODR substrate (M0.1) ────────────────────────────────────────────

export async function createOdr(body) {
  try { return (await api.post(`/odr`, body)).data; } catch (e) { throw _err(e); }
}

export async function listOdrs(params = {}) {
  try { return (await api.get(`/odr`, { params })).data; } catch (e) { throw _err(e); }
}

export async function getOdr(id) {
  try { return (await api.get(`/odr/${encodeURIComponent(id)}`)).data; } catch (e) { throw _err(e); }
}

export async function patchOdr(id, body) {
  try {
    return (await api.patch(`/odr/${encodeURIComponent(id)}`, body)).data;
  } catch (e) { throw _err(e); }
}

export async function submitOdr(id, body = {}) {
  try {
    return (await api.post(`/odr/${encodeURIComponent(id)}/submit`, body)).data;
  } catch (e) { throw _err(e); }
}

export async function listSectionEvents(id) {
  try {
    return (await api.get(`/odr/${encodeURIComponent(id)}/section-events`)).data;
  } catch (e) { throw _err(e); }
}

// ── Amendments (M0.2) ───────────────────────────────────────────────

export async function amendOdr(id, body) {
  try {
    return (await api.post(`/odr/${encodeURIComponent(id)}/amend`, body)).data;
  } catch (e) { throw _err(e); }
}

export async function listAmendments(id) {
  try {
    return (await api.get(`/odr/${encodeURIComponent(id)}/amendments`)).data;
  } catch (e) { throw _err(e); }
}

export async function getVersionChain(id) {
  try {
    return (await api.get(`/odr/${encodeURIComponent(id)}/version-chain`)).data;
  } catch (e) { throw _err(e); }
}

// ── Continuity (M0.2) ───────────────────────────────────────────────

export async function mintPublicLink(id, body = { link_scope: "project_crew" }) {
  try {
    return (await api.post(`/odr/${encodeURIComponent(id)}/link`, body)).data;
  } catch (e) { throw _err(e); }
}

export async function listPublicLinks(params = {}) {
  try { return (await api.get(`/odr/public-links`, { params })).data; } catch (e) { throw _err(e); }
}

export async function revokePublicLink(link_id) {
  try {
    return (await api.patch(
      `/odr/public-links/${encodeURIComponent(link_id)}`,
      { revoke: true },
    )).data;
  } catch (e) { throw _err(e); }
}

// ── Guidance (M0.2A) ────────────────────────────────────────────────

export async function listGuidancePrompts() {
  try { return (await api.get(`/odr/guidance/prompts`)).data; } catch (e) { throw _err(e); }
}

export async function resolveGuidance(prompt_key, crew_type, lang = "en") {
  try {
    return (await api.get(`/odr/guidance/resolve`, {
      params: { prompt_key, crew_type, lang },
    })).data;
  } catch (e) { throw _err(e); }
}

export async function getCrewReadiness(crew_type) {
  try {
    return (await api.get(
      `/odr/guidance/crew-readiness/${encodeURIComponent(crew_type)}`,
    )).data;
  } catch (e) { throw _err(e); }
}

// ── Observation (M0.3) ──────────────────────────────────────────────
//
// Fire-and-forget telemetry. Never blocks the user flow.

export function logObservation(event) {
  try {
    return api.post(`/odr/observation/event`, event).catch(() => null);
  } catch {
    return Promise.resolve();   // swallow — telemetry must never break UI
  }
}

// ── PDF (M0.2) ──────────────────────────────────────────────────────

export function pdfUrl(id, audience = "foreman") {
  return `${api.defaults.baseURL.replace(/\/$/, "")}/odr/${encodeURIComponent(id)}/pdf?audience=${audience}`;
}

// ── Unified Operational Records (M1 · Option C) ─────────────────────
// Doctrine: /app/memory/UNIFIED_RECORDS_PROJECTOR_CERTIFICATION.md
// Read-only · two-substrate projection · zero mutation.

export async function listOperationalRecords(params = {}) {
  try {
    return (await api.get(`/operational-records`, { params })).data;
  } catch (e) { throw _err(e); }
}

export async function resolveDocId(docId) {
  try {
    return (await api.get(`/operational-records/resolve/${encodeURIComponent(docId)}`)).data;
  } catch (e) { throw _err(e); }
}
