// photoStaging.js — iter435 · Phase 31 · Pass B · Part 3.
//
// IndexedDB-backed photo upload staging with foreground retry. When an
// attachment upload fails (offline, network blip, server 5xx), the
// File/Blob is staged locally and replayed on `online` + `focus`
// events. The user sees a calm "Waiting to send" indicator — never a
// red error banner, never a stack trace.
//
// Doctrine
// --------
// - **Foreground only.** No Service Worker, no Background Sync API.
//   iOS-safe · WebView-safe. Replay runs while the tab is alive.
// - **Per-actor, per-host scoping.** Two operators on the same phone
//   never see each other's staged photos.
// - **Append-only.** Staged photos are removed ONLY after the upload
//   confirms 2xx. 4xx domain rejections also clear the entry (the
//   driver cannot resolve a rejected ticket from a quiet phone).
// - **Capped at 20 staged photos per actor.** Beyond that we drop the
//   oldest to prevent a runaway IDB. Field operators rarely stack > 5.
// - **NO retry panel UI.** A tiny count badge ("3 waiting to send") is
//   the entire surface.
//
// API
// ---
//   stagePhoto({ file, hostKind, hostId, attachmentType, note }) → string  (stageId)
//   listStagedFor(hostKind, hostId)                                  → Promise<staged[]>
//   listAllStaged()                                                   → Promise<staged[]>
//   getStagedCount()                                                  → Promise<number>
//   flushStaged()                                                     → Promise<{sent, kept}>
//   removeStaged(stageId)                                             → Promise<void>
//   onStagedChange(cb)                                                → unsubscribe()
//
// Storage key shape:
//   masci.staged-photo.<actorId>.<stageId>

import { get, set, del, keys as idbKeys } from "idb-keyval";
import { getActorId } from "./actorId";
import { getAdminToken } from "@/lib/adminAuth";
import { getDispatchToken } from "@/lib/dispatchAuth";
import { getDriverToken } from "@/lib/driverAuth";

const STAGED_PREFIX_BASE = "masci.staged-photo.";
const MAX_STAGED_PER_ACTOR = 20;
const API = process.env.REACT_APP_BACKEND_URL;
const _listeners = new Set();
let _flushing = false;

function _actorPrefix() {
  return `${STAGED_PREFIX_BASE}${getActorId() || "anon"}.`;
}

function _randId() {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

function _stageKey(stageId) {
  return `${_actorPrefix()}${stageId}`;
}

function _uploadHeaders() {
  const h = {};
  const a = getAdminToken && getAdminToken();
  const d = getDispatchToken && getDispatchToken();
  const drv = getDriverToken && getDriverToken();
  if (a) h["X-Admin-Token"] = a;
  if (d) h["X-Dispatch-Token"] = d;
  if (drv) h["X-Driver-Token"] = drv;
  return h;
}

function _notify() {
  for (const cb of _listeners) {
    try { cb(); } catch { /* ignore */ }
  }
}

export function onStagedChange(cb) {
  _listeners.add(cb);
  return () => _listeners.delete(cb);
}

async function _allKeysForActor() {
  const prefix = _actorPrefix();
  const ks = await idbKeys();
  return ks.filter((k) => typeof k === "string" && k.startsWith(prefix));
}

async function _readAll() {
  const ks = await _allKeysForActor();
  const out = [];
  for (const k of ks) {
    const v = await get(k);
    if (v && v.stageId) out.push(v);
  }
  out.sort((a, b) => (a.stagedAt || 0) - (b.stagedAt || 0));
  return out;
}

export async function stagePhoto({ file, hostKind, hostId, attachmentType, note }) {
  if (!file || !hostKind || !hostId) {
    throw new Error("stagePhoto: file + hostKind + hostId required");
  }
  // Cap: drop oldest if exceeded.
  const existing = await _readAll();
  while (existing.length >= MAX_STAGED_PER_ACTOR) {
    const oldest = existing.shift();
    try { await del(_stageKey(oldest.stageId)); } catch { /* ignore */ }
  }
  const stageId = _randId();
  const entry = {
    stageId,
    hostKind,
    hostId,
    attachmentType: attachmentType || "operational_note_photo",
    note: (note || "").slice(0, 500),
    file,                              // Blob/File preserved in IDB
    fileName: file.name || "photo.jpg",
    fileType: file.type || "image/jpeg",
    fileSize: file.size || 0,
    stagedAt: Date.now(),
    tries: 0,
    lastError: null,
  };
  try {
    await set(_stageKey(stageId), entry);
  } catch (e) {
    throw new Error(`stagePhoto: IDB write failed (${e?.message || e})`);
  }
  _notify();
  return stageId;
}

export async function removeStaged(stageId) {
  try { await del(_stageKey(stageId)); } catch { /* ignore */ }
  _notify();
}

export async function listStagedFor(hostKind, hostId) {
  const all = await _readAll();
  return all.filter((s) => s.hostKind === hostKind && s.hostId === hostId);
}

export async function listAllStaged() {
  return _readAll();
}

export async function getStagedCount() {
  return (await _readAll()).length;
}

async function _attemptOne(entry) {
  const form = new FormData();
  form.append("host_kind", entry.hostKind);
  form.append("host_id", entry.hostId);
  form.append("attachment_type", entry.attachmentType);
  form.append("operational_note", entry.note || "");
  form.append("file", entry.file, entry.fileName);
  const r = await fetch(`${API}/api/operational-attachments/upload`, {
    method: "POST",
    headers: _uploadHeaders(),
    body: form,
  });
  return r;
}

export async function flushStaged() {
  if (_flushing) return { sent: 0, kept: 0 };
  if (typeof navigator !== "undefined" && !navigator.onLine) {
    return { sent: 0, kept: await getStagedCount() };
  }
  _flushing = true;
  let sent = 0;
  let kept = 0;
  try {
    const all = await _readAll();
    for (const entry of all) {
      try {
        const r = await _attemptOne(entry);
        if (r.status === 401 || r.status === 403) {
          // Auth lost — preserve so the operator can retry after login.
          kept += 1;
          continue;
        }
        if (r.ok || (r.status >= 400 && r.status < 500)) {
          // 2xx OK · 4xx domain rejection — clear (operator cannot
          // resolve a stale rejection from a quiet phone screen).
          await del(_stageKey(entry.stageId));
          sent += 1;
        } else {
          // 5xx · keep for retry.
          entry.tries = (entry.tries || 0) + 1;
          entry.lastError = `HTTP ${r.status}`;
          await set(_stageKey(entry.stageId), entry);
          kept += 1;
        }
      } catch (e) {
        entry.tries = (entry.tries || 0) + 1;
        entry.lastError = e?.message || "network";
        try { await set(_stageKey(entry.stageId), entry); } catch { /* ignore */ }
        kept += 1;
      }
    }
  } finally {
    _flushing = false;
    _notify();
  }
  return { sent, kept };
}

if (typeof window !== "undefined") {
  window.addEventListener("online", () => { flushStaged(); });
  window.addEventListener("focus", () => { flushStaged(); });
}
