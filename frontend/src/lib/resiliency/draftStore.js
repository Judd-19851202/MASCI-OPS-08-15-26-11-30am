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

export async function listDraftEntriesForPrefix(formKeyPrefix) {
  if (!formKeyPrefix) return [];
  try {
    const ks = await idbKeys();
    const rows = [];
    for (const k of ks) {
      if (typeof k !== "string") continue;
      if (!k.startsWith(DRAFT_PREFIX) && !k.startsWith(ARCHIVE_PREFIX)) continue;
      if (!k.includes(`.${formKeyPrefix}`)) continue;
      try {
        const v = await get(k);
        rows.push({ key: k, entry: v || null });
      } catch {
        /* ignore corrupt/bad entries during recovery listing */
      }
    }
    return rows;
  } catch {
    return [];
  }
}

function _parseStorageRowKey(key) {
  if (typeof key !== "string") return null;
  const isDraft = key.startsWith(DRAFT_PREFIX);
  const isArchive = key.startsWith(ARCHIVE_PREFIX);
  if (!isDraft && !isArchive) return null;
  const prefix = isDraft ? DRAFT_PREFIX : ARCHIVE_PREFIX;
  const rest = key.slice(prefix.length);
  const firstDot = rest.indexOf(".");
  if (firstDot < 0) return null;
  const actorId = rest.slice(0, firstDot);
  const tail = rest.slice(firstDot + 1);
  if (isDraft) {
    return { kind: "draft", actorId, formKey: tail, deletedAt: null };
  }
  const lastDot = tail.lastIndexOf(".");
  if (lastDot < 0) return null;
  const formKey = tail.slice(0, lastDot);
  const deletedAt = Number(tail.slice(lastDot + 1) || 0) || null;
  return { kind: "archive", actorId, formKey, deletedAt };
}

export function inferDailyReportContextFromForm(entry = {}, parsed = {}) {
  const form = entry?.form || {};
  const byForm = {
    actor_id: entry?.savedByActor || parsed?.actorId || "",
    project_number: form?.project_number || "",
    report_date: form?.report_date || "",
    report_instance: form?.report_instance || "primary",
    report_number: form?.report_number || "",
  };
  const formKey = String(parsed?.formKey || "");
  const match = formKey.match(/daily-report(?:-new)?::(.+)$/);
  if (match && match[1]) {
    const bits = match[1].split("::");
    if (bits.length >= 4) {
      byForm.actor_id = byForm.actor_id || bits[0] || "";
      byForm.project_number = byForm.project_number || bits[1] || "";
      byForm.report_date = byForm.report_date || bits[2] || "";
      byForm.report_instance = byForm.report_instance || bits[3] || "primary";
    } else if (bits.length === 3) {
      byForm.project_number = byForm.project_number || bits[0] || "";
      byForm.report_date = byForm.report_date || bits[1] || "";
      byForm.report_number = byForm.report_number || bits[2] || "";
      byForm.report_instance = byForm.report_instance || "primary";
    } else if (bits.length === 2) {
      byForm.project_number = byForm.project_number || bits[0] || "";
      byForm.report_date = byForm.report_date || bits[1] || "";
    }
  }
  return byForm;
}

export async function promoteLegacyDailyReportDraft({
  targetActorId,
  targetFormKey,
  targetContext,
  candidates,
}) {
  const out = {
    promoted: false,
    preserved: 0,
    retired: 0,
    reason: "no_candidate",
    chosenKey: null,
  };
  if (!targetFormKey || !Array.isArray(candidates) || candidates.length === 0) return out;

  const targetExisting = await get(_draftKey(targetActorId, targetFormKey)).catch(() => null);
  const targetSavedAt = Number(targetExisting?.savedAt || 0);

  const valid = candidates
    .map((row) => {
      const parsed = _parseStorageRowKey(row?.key);
      const entry = row?.entry || null;
      const context = inferDailyReportContextFromForm(entry, parsed || {});
      const sameProject = String(context.project_number || "") === String(targetContext?.project_number || "");
      const sameDate = String(context.report_date || "") === String(targetContext?.report_date || "");
      const sameInstance = String(context.report_instance || "primary") === String(targetContext?.report_instance || "primary");
      const actorMatch = !context.actor_id || String(context.actor_id) === String(targetContext?.actor_id || "");
      return {
        row,
        parsed,
        entry,
        context,
        valid: Boolean(entry?.form && sameProject && sameDate && sameInstance && actorMatch),
      };
    })
    .filter((row) => row.valid)
    .sort((a, b) => Number(b.entry?.savedAt || 0) - Number(a.entry?.savedAt || 0));

  out.preserved = candidates.length;
  if (!valid.length) {
    out.reason = "no_valid_candidate";
    return out;
  }

  const newest = valid[0];
  out.chosenKey = newest.row.key;
  if (targetSavedAt && targetSavedAt >= Number(newest.entry?.savedAt || 0)) {
    out.reason = "target_newer";
    return out;
  }

  const promoted = await promoteDraftEntry(targetActorId, targetFormKey, {
    ...newest.entry,
    savedByActor: targetContext?.actor_id || newest.entry?.savedByActor || null,
    migratedFromKey: newest.row.key,
    migratedAt: Date.now(),
  });
  if (!promoted) {
    out.reason = "promote_failed";
    return out;
  }

  const readback = await get(_draftKey(targetActorId, targetFormKey)).catch(() => null);
  if (!readback?.form) {
    out.reason = "readback_failed";
    return out;
  }

  try {
    await del(newest.row.key);
    out.retired = 1;
  } catch {
    out.retired = 0;
  }
  out.promoted = true;
  out.reason = "promoted";
  return out;
}

export async function promoteDraftEntry(actorId, formKey, entry) {
  if (!formKey || !entry || typeof entry !== "object" || !entry.form) return false;
  try {
    await set(_draftKey(actorId, formKey), {
      ...entry,
      savedByActor: entry.savedByActor || actorId || null,
      promotedAt: Date.now(),
    });
    const readback = await get(_draftKey(actorId, formKey));
    return Boolean(readback?.form);
  } catch {
    return false;
  }
}

// --------------------------------------------------------- legacy migration
// Re-keys any legacy token-derived drafts under the new device-scoped
// actor id. One-time, idempotent, safe to call on every mount.
// Returns { migrated, kept }.
export async function migrateLegacyDrafts(deviceActorId, legacyActorIds, formKey) {
  if (!deviceActorId || !formKey || !Array.isArray(legacyActorIds)) {
    return { migrated: 0, kept: 0 };
  }
  let migrated = 0;
  let kept = 0;
  try {
    const target = _draftKey(deviceActorId, formKey);
    const existing = await get(target);
    let best = existing && existing.form ? { key: target, value: existing } : null;
    for (const legacyId of legacyActorIds) {
      if (!legacyId || legacyId === deviceActorId) continue;
      const legacyKey = _draftKey(legacyId, formKey);
      if (legacyKey === target) continue;
      let v;
      try { v = await get(legacyKey); } catch { v = null; }
      if (!v || !v.form) continue;
      const candidate = { key: legacyKey, value: v };
      if (!best || (v.savedAt || 0) > (best.value.savedAt || 0)) best = candidate;
      else kept += 1;
    }
    if (best && best.key !== target) {
      try {
        await set(target, best.value);
        const readback = await get(target);
        if (readback && readback.form && (readback.savedAt || 0) === (best.value.savedAt || 0)) {
          migrated += 1;
          try { await del(best.key); } catch { /* ignore */ }
        }
      } catch { /* leave legacy source intact on failed promotion */ }
    }
  } catch { /* ignore */ }
  return { migrated, kept };
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
