// src/lib/teamRosterApi.js — Track 14.0-JOB-OWNERSHIP-FOUNDATION Phase 1.
// Client for the project_team_assignments backend.

import { getAdminToken } from "./adminAuth";
import { getPmToken } from "./pmAuth";
import { getSafetyToken } from "./safetyAuth";
import { getHrToken } from "./hrAuth";
import { getShopToken } from "./shopAuth";
import { getDispatchToken } from "./dispatchAuth";
import { getFlToken } from "./flAuth";

const API = process.env.REACT_APP_BACKEND_URL;

function headers(json = false) {
  const h = {};
  if (json) h["Content-Type"] = "application/json";
  const a = getAdminToken(); if (a) h["X-Admin-Token"] = a;
  const p = getPmToken(); if (p) h["X-PM-Token"] = p;
  const s = getSafetyToken(); if (s) h["X-Safety-Token"] = s;
  const hr = getHrToken(); if (hr) h["X-HR-Token"] = hr;
  const sh = getShopToken(); if (sh) h["X-Shop-Token"] = sh;
  const d = getDispatchToken(); if (d) h["X-Dispatch-Token"] = d;
  const fl = getFlToken(); if (fl) h["X-FL-Token"] = fl;
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
  if (!r.ok) throw new Error(data.detail || `patch: ${r.status}`);
  return data;
}

export async function removeTeamMember(projectNumber, assignmentId, reason, { adminScope = false } = {}) {
  const path = adminScope
    ? `/api/admin/jobs/${encodeURIComponent(projectNumber)}/team/${assignmentId}`
    : `/api/pm/job/${encodeURIComponent(projectNumber)}/team/${assignmentId}`;
  const url = reason
    ? `${API}${path}?reason=${encodeURIComponent(reason)}`
    : `${API}${path}`;
  const r = await fetch(url, { method: "DELETE", headers: headers() });
  if (!r.ok) {
    const data = await r.json().catch(() => ({}));
    throw new Error(data.detail || `remove: ${r.status}`);
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
