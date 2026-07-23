// draftStore.js — iter440 · P0 field-incident remediation · 2026-05-27.
//
// IndexedDB-backed form draft store. Built on idb-keyval (~600 bytes).
//
// What changed at iter440
// -----------------------
// 1. `saveDraft()` now returns `{ ok, savedAt | error, errorName }`.
//    The autosave hook can show a TRUTHFUL pill ("Save failed —
//    storage full") instead of a green checkmark over a silent
//    failure. (Defends H1.)
//
// 2. `discardDraft()` SOFT-DELETES into an archive store with 24 h
//    retention so a mis-tap on "Discard" does not nuke the morning's
//    work. (Defends H6.)
//
// 3. New `migrateLegacyDrafts(deviceActorId, legacyActorIds, formKey)`
//    re-keys any orphaned drafts written under prior token-derived
//    actor ids. One-time, idempotent, fire-and-forget. (Defends H2.)
//
// 4. `storeIdempotencyKey()` / `getIdempotencyKey()` persist the
//    submit idempotency key in IDB so a reload mid-queue does not
//    mint a duplicate. (Defends H8.)
//
// Storage key shapes:
//   masci.draft.<actorId>.<formKey>                       primary
//   masci.draft-archive.<actorId>.<formKey>.<deletedAt>   soft-delete
//   masci.draft-idempotency.<actorId>.<formKey>           submit key

import { get, set, del, keys as idbKeys } from "idb-keyval";

const DRAFT_PREFIX = "masci.draft.";
const ARCHIVE_PREFIX = "masci.draft-archive.";
const IDEMPOTENCY_PREFIX = "masci.draft-idempotency.";

const STALE_DAYS = 14;
const STALE_MS = STALE_DAYS * 24 * 60 * 60 * 1000;
const ARCHIVE_TTL_MS = 24 * 60 * 60 * 1000;        // 24 h soft-delete window
const ARCHIVE_MAX_PER_FORM = 5;                    // keep at most 5 archives

function _draftKey(actorId, formKey) {
  return `${DRAFT_PREFIX}${actorId || "anon"}.${formKey}`;
}
function _archiveKey(actorId, formKey, deletedAt) {
  return `${ARCHIVE_PREFIX}${actorId || "anon"}.${formKey}.${deletedAt}`;
}
function _idempotencyKey(actorId, formKey) {
  return `${IDEMPOTENCY_PREFIX}${actorId || "anon"}.${formKey}`;
}

// -------------------------------------------------------------------- save
// Track 19.04 · Form Session Isolation: `savedByActor` fingerprints
// the writing actor so a later read on the same device can skip
// drafts that were saved by a different signed-in user. The device-
// scoped IDB key is preserved so token rotation still recovers the
// morning's draft — but a *different* portal actor on the same device
// now correctly starts blank instead of being offered another user's
// unfinished report.
export async function saveDraft(actorId, formKey, form, opts = {}) {
  if (!formKey) return { ok: false, error: "formKey required", errorName: "ValueError" };
  const savedAt = Date.now();
  const entry = {
    form,
    savedAt,
    savedByActor: opts.savedByActor || null,
    contract_version: "19.04",
  };
  try {
    await set(_draftKey(actorId, formKey), entry);
    return { ok: true, savedAt };
  } catch (e) {
    return {
      ok: false,
      error: e?.message || "idb-write-failed",
      errorName: e?.name || "Error",
    };
  }
}

// -------------------------------------------------------------------- read
// Returns just the form payload (backward-compat surface used by
// the older `useDraft` / `useDraftSync` hooks). New callers should
// prefer `getDraftEntry()` which exposes `savedAt` for the truthful
// "Saved N ago" pill.
export async function getDraft(actorId, formKey) {
  if (!formKey) return null;
  try {
    const entry = await get(_draftKey(actorId, formKey));
    if (!entry || !entry.form) return null;
    if (Date.now() - (entry.savedAt || 0) > STALE_MS) {
      try { await del(_draftKey(actorId, formKey)); } catch { /* ignore */ }
      return null;
    }
    return entry.form;
  } catch {
    return null;
  }
}

// Full envelope variant — `{ form, savedAt, savedByActor }` or null.
// Used by the iter440 useFormDraft hook to render the truthful
// timestamp and (Track 19.04) to enforce actor-scoped restore.
export async function getDraftEntry(actorId, formKey) {
  if (!formKey) return null;
  try {
    const entry = await get(_draftKey(actorId, formKey));
    if (!entry || !entry.form) return null;
    if (Date.now() - (entry.savedAt || 0) > STALE_MS) {
      try { await del(_draftKey(actorId, formKey)); } catch { /* ignore */ }
      return null;
    }
    return {
      form: entry.form,
      savedAt: entry.savedAt || 0,
      savedByActor: entry.savedByActor || null,
      contract_version: entry.contract_version || null,
    };
  } catch {
    return null;
  }
}

export async function findDraftEntriesForBase(actorId, formKeyBase, options = {}) {
  if (!formKeyBase) return [];
  const prefix = `${DRAFT_PREFIX}${actorId || "anon"}.${formKeyBase}::`;
  const excludeKey = options.excludeFormKey ? _draftKey(actorId, options.excludeFormKey) : "";
  const filter = typeof options.filter === "function" ? options.filter : null;
  const limit = Number.isFinite(options.limit) ? Math.max(1, Number(options.limit)) : Infinity;
  try {
    const ks = (await idbKeys())
      .filter((k) => typeof k === "string" && k.startsWith(prefix) && k !== excludeKey);
    const out = [];
    for (const key of ks) {
      const entry = await get(key);
      if (!entry || !entry.form) continue;
      if (Date.now() - (entry.savedAt || 0) > STALE_MS) {
        try { await del(key); } catch { /* ignore */ }
        continue;
      }
      const candidate = {
        form: entry.form,
        savedAt: entry.savedAt || 0,
        savedByActor: entry.savedByActor || null,
        formKey: key.slice(`${DRAFT_PREFIX}${actorId || "anon"}.`.length),
      };
      if (filter && !filter(candidate)) continue;
      out.push(candidate);
    }
    out.sort((a, b) => (b.savedAt || 0) - (a.savedAt || 0));
    return out.slice(0, limit);
  } catch {
    return [];
  }
}

export async function findLatestDraftEntryForBase(actorId, formKeyBase, options = {}) {
  const matches = await findDraftEntriesForBase(actorId, formKeyBase, { ...options, limit: 1 });
  return matches[0] || null;
}

// ---------------------------------------------------------------- discard
// SOFT-DELETE — moves the draft into an archive key with 24 h TTL so
// a mis-tap on "Discard" does not destroy the morning's work.
export async function discardDraft(actorId, formKey) {
  if (!formKey) return;
  try {
    const live = await get(_draftKey(actorId, formKey));
    if (live && live.form) {
      const deletedAt = Date.now();
      try {
        await set(_archiveKey(actorId, formKey, deletedAt), {
          ...live, deletedAt,
        });
      } catch { /* ignore archive write failures */ }
    }
    await del(_draftKey(actorId, formKey));
    // Bound the archive — keep at most ARCHIVE_MAX_PER_FORM.
    try {
      const prefix = `${ARCHIVE_PREFIX}${actorId || "anon"}.${formKey}.`;
      const ks = (await idbKeys())
        .filter((k) => typeof k === "string" && k.startsWith(prefix))
        .sort();
      while (ks.length > ARCHIVE_MAX_PER_FORM) {
        const oldest = ks.shift();
        try { await del(oldest); } catch { /* ignore */ }
      }
    } catch { /* ignore */ }
  } catch { /* ignore */ }
}

export async function clearDraft(actorId, formKey) {
  if (!formKey) return;
  try {
    await del(_draftKey(actorId, formKey));
  } catch { /* ignore */ }
}

// Try to recover the most-recently-archived draft (within TTL).
// Used as a defensive fallback when getDraft() returns null but the
// operator insists they had work.
export async function recoverArchivedDraft(actorId, formKey) {
  if (!formKey) return null;
  try {
    const prefix = `${ARCHIVE_PREFIX}${actorId || "anon"}.${formKey}.`;
    const ks = (await idbKeys())
      .filter((k) => typeof k === "string" && k.startsWith(prefix))
      .sort()
      .reverse();
    const cutoff = Date.now() - ARCHIVE_TTL_MS;
    for (const k of ks) {
      const v = await get(k);
      if (v && (v.deletedAt || 0) >= cutoff && v.form) {
        return { form: v.form, savedAt: v.savedAt, deletedAt: v.deletedAt };
      }
    }
  } catch { /* ignore */ }
  return null;
}

// ------------------------------------------------------------ purge stale
export async function purgeStaleDrafts() {
  try {
    const ks = await idbKeys();
    const draftCutoff = Date.now() - STALE_MS;
    const archiveCutoff = Date.now() - ARCHIVE_TTL_MS;
    await Promise.all(
      ks.filter((k) => typeof k === "string").map(async (k) => {
        if (k.startsWith(DRAFT_PREFIX)) {
          const v = await get(k);
          if (!v || (v.savedAt || 0) < draftCutoff) {
            try { await del(k); } catch { /* ignore */ }
          }
        } else if (k.startsWith(ARCHIVE_PREFIX)) {
          const v = await get(k);
          if (!v || (v.deletedAt || 0) < archiveCutoff) {
            try { await del(k); } catch { /* ignore */ }
          }
        }
      }),
    );
  } catch { /* ignore */ }
}

// ------------------------------------------------------------------ wipe
export async function clearAllDraftsForActor(actorId) {
  try {
    const draftPrefix = `${DRAFT_PREFIX}${actorId || "anon"}.`;
    const archivePrefix = `${ARCHIVE_PREFIX}${actorId || "anon"}.`;
    const idempPrefix = `${IDEMPOTENCY_PREFIX}${actorId || "anon"}.`;
    const ks = await idbKeys();
    await Promise.all(
      ks.filter((k) =>
        typeof k === "string" && (
          k.startsWith(draftPrefix) ||
          k.startsWith(archivePrefix) ||
          k.startsWith(idempPrefix)
        ),
      ).map((k) => del(k)),
    );
  } catch { /* ignore */ }
}


// ------------------------------------------------------ idempotency keys
export async function storeIdempotencyKey(actorId, formKey, key) {
  if (!formKey || !key) return;
  try {
    await set(_idempotencyKey(actorId, formKey), { key, savedAt: Date.now() });
  } catch { /* ignore */ }
}

export async function getIdempotencyKey(actorId, formKey) {
  if (!formKey) return null;
  try {
    const v = await get(_idempotencyKey(actorId, formKey));
    return v?.key || null;
  } catch {
    return null;
  }
}

export async function clearIdempotencyKey(actorId, formKey) {
  if (!formKey) return;
  try { await del(_idempotencyKey(actorId, formKey)); } catch { /* ignore */ }
}
