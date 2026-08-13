// queuePayloadMigration.js — P0-QUEUE-2026-08-13 · Legacy submission-queue
// compatibility owner.
//
// Purpose
// -------
// Autosaved/queued operational submissions persist on a device under one app
// version and may replay days later against a newer backend. When a payload
// carries client-only transport/helper metadata that a stricter backend model
// rejects (HTTP 422 "Extra inputs are not permitted"), legitimate operator
// work gets stranded in the Submission Queue. This module is the ONE shared,
// versioned, deterministic migration applied to EVERY queued body immediately
// before an HTTP attempt.
//
// Doctrine (zero data loss)
// -------------------------
//   • Operate on a DEEP CLONE only. The persisted queue entry body is NEVER
//     mutated, so a discard/restore round-trip and recovery copy remain intact.
//   • Strip ONLY allowlisted, proven client-only transport metadata — never a
//     business field an operator could have entered. The canonical idempotency
//     key travels on the `Idempotency-Key` HTTP header, so `*idempotency*`
//     helper fields in the body are redundant transport metadata.
//   • Deterministic + idempotent: running twice yields the same result.
//   • Stamp `queue_schema_version` so future migrations are versioned.
//
// If a payload contains an UNKNOWN field that is NOT on the client-only
// allowlist, we DO NOT strip it — it is preserved and forwarded so the backend
// (which now tolerates unknown fields on offline-queue create models) can keep
// it. Nothing operator-entered is silently discarded.

export const QUEUE_SCHEMA_VERSION = 2;

// Exact client-only metadata keys proven safe to strip (transport helpers).
const CLIENT_ONLY_META_KEYS = new Set([
  "_track_15_60_client_idempotency_key",
]);

// Prefixes for client-only transport metadata. Kept deliberately narrow:
//   _track_*  — client attribution/idempotency helpers
//   _client_* — client transport helpers
//   _queue_*  — queue bookkeeping helpers
// A key is stripped ONLY if it also looks like transport metadata
// (contains "idempotency", "client", "queue", "track", or "transport").
const CLIENT_ONLY_PREFIXES = ["_track_", "_client_", "_queue_"];

function _isPlainObject(v) {
  return v !== null && typeof v === "object" && !Array.isArray(v);
}

function _looksLikeTransportMeta(key) {
  if (CLIENT_ONLY_META_KEYS.has(key)) return true;
  const k = String(key).toLowerCase();
  if (!CLIENT_ONLY_PREFIXES.some((p) => k.startsWith(p))) return false;
  return ["idempotency", "client", "queue", "track", "transport"].some((tok) =>
    k.includes(tok),
  );
}

function _cloneBody(body) {
  try { return JSON.parse(JSON.stringify(body)); } catch { return body; }
}

/**
 * Migrate a queued payload body for retry submission.
 *
 * @param {*} originalBody  the persisted queue entry body (never mutated)
 * @param {string} [formKey]
 * @returns {{ body:*, stripped:string[], version:number, changed:boolean }}
 */
export function migrateQueuedBody(originalBody, formKey = "") {
  if (!_isPlainObject(originalBody)) {
    return { body: originalBody, stripped: [], version: QUEUE_SCHEMA_VERSION, changed: false };
  }
  const body = _cloneBody(originalBody);
  const stripped = [];

  // Strip allowlisted client-only transport metadata at the top level only.
  // We intentionally do NOT recurse into nested business objects to avoid any
  // risk of touching operator-entered structures.
  for (const key of Object.keys(body)) {
    if (_looksLikeTransportMeta(key)) {
      delete body[key];
      stripped.push(key);
    }
  }

  // NOTE: We deliberately do NOT inject any field (e.g. queue_schema_version)
  // into the outbound body. The migration is STRIP-ONLY so it can never
  // introduce a new "Extra inputs are not permitted" failure on an endpoint
  // whose model still forbids unknown fields. The version is returned
  // separately for queue bookkeeping only.
  const changed = stripped.length > 0;
  return { body, stripped, version: QUEUE_SCHEMA_VERSION, changed };
}
