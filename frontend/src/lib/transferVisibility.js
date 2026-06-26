// transferVisibility.js — TRACK 15.83 · Production Excellence Lockup.
//
// Production showed audit / validation artifacts ("#71 in Masci Equip
// list → AUDIT-2", repeated CANCELLED rows) on the operator-facing
// Recent Transfers list. These rows are deployment validation residue,
// not real dispatch work, and they damage trust on the landing surface.
//
// Conservative front-end filter that scrubs obvious audit / test /
// validation / smoke-test artifacts from operator default views without
// deleting any record. Admin Audit and the full Asset Transfers screen
// still see everything — see `/asset-transfers` for the unfiltered list.
//
// Doctrine:
//   * Don't hide REAL cancelled work — only obvious validation noise.
//   * Use multiple signals (project numbers, reason text, source).
//   * Default OPEN: if we cannot prove a row is noise, show it.
//   * Idempotent + pure: no side effects.

const AUDIT_PROJECT_RX = /^(AUDIT|TEST|DEMO|VALIDATION|VAL|SMOKE|SAMPLE)[-_]?\d*$/i;
const AUDIT_REASON_RX = /\b(audit|smoke[\s-]?test|deployment validation|validation run|self[\s-]?test|test fixture|seed validation)\b/i;
const AUDIT_SOURCE_RX = /\b(audit|seed|validator|fixture|smoke|cert)\b/i;

function _looksLikeAuditProject(value) {
  if (!value) return false;
  return AUDIT_PROJECT_RX.test(String(value).trim());
}

/**
 * Return true if `record` is a normal operational transfer the
 * dispatcher should see. Return false if it is obvious audit /
 * validation / smoke-test residue.
 */
export function isOperatorVisibleTransfer(record) {
  if (!record || typeof record !== "object") return false;

  // Field 1 · destination / source project marker — strongest signal.
  if (_looksLikeAuditProject(record.to_project_number)) return false;
  if (_looksLikeAuditProject(record.from_project_number)) return false;

  // Field 2 · reason text often carries the marker ("deployment
  // validation cancel", "AUDIT-2 smoke test"). Conservative regex.
  if (record.reason && AUDIT_REASON_RX.test(String(record.reason))) return false;
  if (record.decision_reason && AUDIT_REASON_RX.test(String(record.decision_reason))) {
    return false;
  }

  // Field 3 · created_by / requested_by / source_system. If the
  // record was minted by an obvious automated audit / smoke flow,
  // suppress it from the operator surface.
  const sources = [
    record.created_by, record.requested_by, record.source_system,
    record.audit_marker, record.record_type, record.transfer_type,
  ];
  for (const s of sources) {
    if (s && AUDIT_SOURCE_RX.test(String(s))) return false;
  }

  // Field 4 · explicit flags some backends set on validation rows.
  if (record.is_audit === true) return false;
  if (record.is_validation === true) return false;
  if (record.is_test === true) return false;

  return true;
}

/**
 * Filter helper for arrays of transfer records.
 */
export function filterOperatorVisibleTransfers(records) {
  if (!Array.isArray(records)) return [];
  return records.filter(isOperatorVisibleTransfer);
}

export const __TRACK_15_83_TRANSFER_VISIBILITY__ = {
  AUDIT_PROJECT_RX,
  AUDIT_REASON_RX,
  AUDIT_SOURCE_RX,
};
