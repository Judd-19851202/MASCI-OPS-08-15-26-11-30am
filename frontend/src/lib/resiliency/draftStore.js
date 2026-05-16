// draftStore.js — IndexedDB-backed form draft store.
// Built on idb-keyval (~600 bytes). Drafts bound to actor identity
// per device; cleared on logout; auto-purge after 14 days idle.
//
// Storage key shape:
//   masci.draft.{actorId}.{formKey}
// Bundles the form payload + photo blobs base64-encoded together so
// nothing is lost on reload.

import { get, set, del, keys as idbKeys } from "idb-keyval";

const DRAFT_PREFIX = "masci.draft.";
const STALE_DAYS = 14;
const STALE_MS = STALE_DAYS * 24 * 60 * 60 * 1000;

function _draftKey(actorId, formKey) {
  return `${DRAFT_PREFIX}${actorId || "anon"}.${formKey}`;
}

/**
 * Save a draft. Wraps the payload in {form, savedAt} envelope so
 * staleness pruning is cheap.
 */
export async function saveDraft(actorId, formKey, form) {
  if (!formKey) return;
  try {
    await set(_draftKey(actorId, formKey), {
      form, savedAt: Date.now(),
    });
  } catch {
    // Quota exceeded / disabled — silent.
  }
}

/**
 * Retrieve a draft if it exists AND isn't stale.
 * Returns null when missing or stale (and purges stale entries).
 */
export async function getDraft(actorId, formKey) {
  if (!formKey) return null;
  try {
    const entry = await get(_draftKey(actorId, formKey));
    if (!entry || !entry.form) return null;
    if (Date.now() - (entry.savedAt || 0) > STALE_MS) {
      await del(_draftKey(actorId, formKey));
      return null;
    }
    return entry.form;
  } catch {
    return null;
  }
}

/**
 * Discard a single draft (post-successful-submit OR on user discard).
 */
export async function discardDraft(actorId, formKey) {
  if (!formKey) return;
  try {
    await del(_draftKey(actorId, formKey));
  } catch {
    // ignore
  }
}

/**
 * Purge ALL drafts older than 14 days. Cheap O(n) keys scan — fine for
 * tens of drafts per device. Call on app boot.
 */
export async function purgeStaleDrafts() {
  try {
    const ks = await idbKeys();
    const cutoff = Date.now() - STALE_MS;
    await Promise.all(
      ks.filter((k) => typeof k === "string" && k.startsWith(DRAFT_PREFIX))
        .map(async (k) => {
          const v = await get(k);
          if (!v || (v.savedAt || 0) < cutoff) {
            await del(k);
          }
        }),
    );
  } catch {
    // ignore
  }
}

/**
 * Wipe ALL drafts for a given actor — call on logout.
 */
export async function clearAllDraftsForActor(actorId) {
  try {
    const prefix = `${DRAFT_PREFIX}${actorId || "anon"}.`;
    const ks = await idbKeys();
    await Promise.all(
      ks.filter((k) => typeof k === "string" && k.startsWith(prefix))
        .map((k) => del(k)),
    );
  } catch {
    // ignore
  }
}
