// photoDraftStore.js — P0 field-incident remediation · 2026-05-27.
//
// Stores photo Blobs separately from the form draft payload to keep
// the autosave envelope small (< 1 MB). Defends RCM hypothesis H4:
// 6× 5MB photos base64'd into the form payload was blowing the iOS
// Safari quota (~50-100 MB under ITP) on every autosave, causing
// silent QuotaExceededError that the UI translated as "Saved".
//
// API
// ----
//   storePhotoBlob(actorId, formKey, blob, meta?)  → { ok, stageId, error? }
//   getPhotoBlob(actorId, formKey, stageId)         → Blob | null
//   listPhotoBlobs(actorId, formKey)                → [{ stageId, blob, meta }]
//   discardPhotoBlobs(actorId, formKey)             → number (deleted count)
//   discardPhotoBlob(actorId, formKey, stageId)     → boolean
//
// Storage key shape:
//   masci.draft-photo.<actorId>.<formKey>.<stageId>
//
// The form draft payload only carries lightweight refs:
//   { stageId, sizeBytes, mime, takenAt }

import { get, set, del, keys as idbKeys } from "idb-keyval";

const PREFIX = "masci.draft-photo.";

function _baseKey(actorId, formKey) {
  return `${PREFIX}${actorId || "anon"}.${formKey}.`;
}

function _stageKey(actorId, formKey, stageId) {
  return `${_baseKey(actorId, formKey)}${stageId}`;
}

function _newStageId() {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

export async function storePhotoBlob(actorId, formKey, blob, meta) {
  if (!formKey || !blob) {
    return { ok: false, stageId: null, error: "formKey and blob required" };
  }
  const stageId = _newStageId();
  const entry = {
    stageId,
    blob,                          // Blob/File preserved in IDB
    mime: blob.type || "image/jpeg",
    sizeBytes: blob.size || 0,
    takenAt: Date.now(),
    meta: meta || {},
  };
  try {
    await set(_stageKey(actorId, formKey, stageId), entry);
    return { ok: true, stageId };
  } catch (e) {
    return {
      ok: false,
      stageId: null,
      error: e?.message || "idb-write-failed",
      errorName: e?.name || "Error",
    };
  }
}

export async function getPhotoBlob(actorId, formKey, stageId) {
  if (!formKey || !stageId) return null;
  try {
    const e = await get(_stageKey(actorId, formKey, stageId));
    return e?.blob || null;
  } catch {
    return null;
  }
}

export async function getPhotoEntry(actorId, formKey, stageId) {
  if (!formKey || !stageId) return null;
  try {
    return (await get(_stageKey(actorId, formKey, stageId))) || null;
  } catch {
    return null;
  }
}

export async function listPhotoBlobs(actorId, formKey) {
  if (!formKey) return [];
  const prefix = _baseKey(actorId, formKey);
  try {
    const ks = await idbKeys();
    const matched = ks.filter((k) => typeof k === "string" && k.startsWith(prefix));
    const out = [];
    for (const k of matched) {
      const v = await get(k);
      if (v && v.stageId) out.push(v);
    }
    out.sort((a, b) => (a.takenAt || 0) - (b.takenAt || 0));
    return out;
  } catch {
    return [];
  }
}

export async function discardPhotoBlob(actorId, formKey, stageId) {
  if (!formKey || !stageId) return false;
  try {
    await del(_stageKey(actorId, formKey, stageId));
    return true;
  } catch {
    return false;
  }
}

export async function discardPhotoBlobs(actorId, formKey) {
  if (!formKey) return 0;
  const prefix = _baseKey(actorId, formKey);
  let n = 0;
  try {
    const ks = await idbKeys();
    const matched = ks.filter((k) => typeof k === "string" && k.startsWith(prefix));
    await Promise.all(matched.map(async (k) => {
      try { await del(k); n += 1; } catch { /* ignore */ }
    }));
  } catch { /* ignore */ }
  return n;
}
