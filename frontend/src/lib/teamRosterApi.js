// src/lib/teamRosterApi.js — Track 14.0-JOB-OWNERSHIP-FOUNDATION Phase 1.
// Client for the project_team_assignments backend.

import { buildScopedPortalAuthHeaders } from "./authHeaders";

const API = process.env.REACT_APP_BACKEND_URL;

function headers(json = false) {
  const h = buildScopedPortalAuthHeaders(["admin", "pm", "safety", "hr", "shop", "dispatch", "fl"]);
  if (json) h["Content-Type"] = "application/json";
  return h;
}

export async function fetchRoleRegistry() {
  const r = await fetch(`${API}/api/team-roster/role-registry`, { headers: headers() });
  if (!r.ok) throw new Error(`role-registry: ${r.status}`);
  return r.json();
}

export async function fetchTeam(projectNumber, { adminScope = false, pmScope = false } = {}) {
  const path = adminScope
    ? `/api/admin/jobs/${encodeURIComponent(projectNumber)}/team`
    : pmScope
      ? `/api/pm/job/${encodeURIComponent(projectNumber)}/team`
      : `/api/jobs/${encodeURIComponent(projectNumber)}/team`;
  const r = await fetch(`${API}${path}`, { headers: headers() });
  if (!r.ok) throw new Error(`team-fetch: ${r.status}`);
  return r.json();
}

export async function fetchTeamAudit(projectNumber) {
  const r = await fetch(
    `${API}/api/admin/jobs/${encodeURIComponent(projectNumber)}/team/audit`,
    { headers: headers() }
  );
  if (!r.ok) throw new Error(`audit: ${r.status}`);
  return r.json();
}

export async function addTeamMember(projectNumber, body, { adminScope = false } = {}) {
  const path = adminScope
    ? `/api/admin/jobs/${encodeURIComponent(projectNumber)}/team`
    : `/api/pm/job/${encodeURIComponent(projectNumber)}/team`;
  const r = await fetch(`${API}${path}`, {
    method: "POST",
    headers: headers(true),
    body: JSON.stringify(body),
  });
  const data = await r.json();
  if (!r.ok) {
    const e = new Error(data.detail || `add: ${r.status}`);
    e.status = r.status;
    throw e;
  }
  return data;
}

export async function patchTeamMember(projectNumber, assignmentId, body) {
  const r = await fetch(
    `${API}/api/admin/jobs/${encodeURIComponent(projectNumber)}/team/${assignmentId}`,
    { method: "PATCH", headers: headers(true), body: JSON.stringify(body) }
  );
  const data = await r.json();
  if (!r.ok) {
    const err = new Error(data.detail || `patch: ${r.status}`);
    err.status = r.status;
    err.detail = data.detail;
    throw err;
  }
  return data;
}

// TRACK 15.39A · structured remove reason — backend now expects a JSON body
// `{ reason_category, reason_text? }` instead of the legacy `?reason=` query.
// `body` may be a plain string (legacy callers — coerced to `{reason_text}` with
// `reason_category=null`) or an object with the new shape.
export async function removeTeamMember(projectNumber, assignmentId, body, { adminScope = false } = {}) {
  const path = adminScope
    ? `/api/admin/jobs/${encodeURIComponent(projectNumber)}/team/${assignmentId}`
    : `/api/pm/job/${encodeURIComponent(projectNumber)}/team/${assignmentId}`;
  const payload =
    body && typeof body === "object"
      ? {
          reason_category: body.reason_category || null,
          reason_text: body.reason_text || null,
        }
      : { reason_category: null, reason_text: body || null };
  const r = await fetch(`${API}${path}`, {
    method: "DELETE",
    headers: headers(true),
    body: JSON.stringify(payload),
  });
  if (!r.ok) {
    const data = await r.json().catch(() => ({}));
    const err = new Error(data.detail || `remove: ${r.status}`);
    err.status = r.status;
    err.detail = data.detail;
    throw err;
  }
  return r.json();
}

export async function runBackfill() {
  const r = await fetch(`${API}/api/admin/team-roster/backfill`, {
    method: "POST",
    headers: headers(),
  });
  if (!r.ok) throw new Error(`backfill: ${r.status}`);
  return r.json();
}

export async function fetchDirectoryUsers() {
  const r = await fetch(`${API}/api/admin/directory/k4/users?limit=300`, { headers: headers() });
  if (!r.ok) throw new Error(`directory: ${r.status}`);
  const data = await r.json();
  return data.users || data.items || [];
}

// TRACK 15.10 · PM-callable read-only directory picker for the Add
// Member flow. Backed by user_directory (the same collection FL/Shop/
// Safety/HR/Dispatch already write to). No new roster system.
export async function fetchPmDirectoryUsers({ q = "", portal = "", limit = 300 } = {}) {
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (portal) params.set("portal", portal);
  params.set("limit", String(limit));
  const r = await fetch(`${API}/api/pm/directory/users?${params.toString()}`, { headers: headers() });
  if (!r.ok) throw new Error(`pm-directory: ${r.status}`);
  const data = await r.json();
  return data.items || [];
}

export async function fetchMyProjects() {
  const r = await fetch(`${API}/api/users/me/projects`, { headers: headers() });
  if (!r.ok) return { items: [], count: 0 };
  return r.json();
}

// ── Track 14.0-JOB-OWNERSHIP-FOUNDATION Phase 2A — lifecycle ────────
export async function transferTeamMember(assignmentId, body) {
  // body: { replacement_user_id?, replacement_email?, reason, end_status?, migrate_open_work? }
  const r = await fetch(
    `${API}/api/admin/team-roster/assignments/${assignmentId}/transfer`,
    { method: "POST", headers: headers(true), body: JSON.stringify(body) }
  );
  const data = await r.json();
  if (!r.ok) throw new Error(data.detail || `transfer: ${r.status}`);
  return data;
}

export async function fetchOpenWorkForUser(userId) {
  const r = await fetch(`${API}/api/admin/users/${userId}/open-work`, { headers: headers() });
  if (!r.ok) throw new Error(`open-work: ${r.status}`);
  return r.json();
}

export async function disableUserPrecheck(userId) {
  const r = await fetch(
    `${API}/api/admin/users/${userId}/disable-precheck`,
    { headers: headers() }
  );
  if (!r.ok) throw new Error(`precheck: ${r.status}`);
  return r.json();
}

export async function disableUserWithMigration(userId, body) {
  // body: { replacement_user_id?, replacement_email?, reason, end_status?, disable_directory_row? }
  const r = await fetch(
    `${API}/api/admin/users/${userId}/disable-with-migration`,
    { method: "POST", headers: headers(true), body: JSON.stringify(body) }
  );
  const data = await r.json();
  if (!r.ok) throw new Error(data.detail || `disable: ${r.status}`);
  return data;
}

export async function captureSnapshot(projectNumber) {
  const r = await fetch(
    `${API}/api/team-roster/snapshot/${encodeURIComponent(projectNumber)}`,
    { headers: headers() }
  );
  if (!r.ok) throw new Error(`snapshot: ${r.status}`);
  return r.json();
}
