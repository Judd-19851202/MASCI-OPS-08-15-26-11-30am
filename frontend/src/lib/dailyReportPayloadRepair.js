// OFFLINE-UPLOAD-002 · Daily Report payload normalizer.
//
// Scope: pure transformation applied to the body of a
// `daily-report-new` resiliency-queue item BEFORE the HTTP attempt.
// Repairs the only class of stuck payload observed in the field
// (numeric fields submitted as empty strings or numeric strings)
// without ever mutating the persisted draft, the persisted queue
// entry's body, or the idempotency key.
//
// Backend contract (routes/daily_reports.py):
//   - ProductionRow.quantity:        float (REQUIRED, default 0.0)
//   - ConstraintRow.hours_impact:    Optional[float] (default None)
//   - outbound_materials[]:          List[Dict[str, Any]] (no schema
//                                    enforcement, but the same UI
//                                    initialiser uses "" for quantity
//                                    so we still coerce for hygiene)
//
// Rules (per OMEGA directive):
//   • blank string  → 0 for required floats, null for Optional floats
//   • numeric string ("2.5") → number 2.5
//   • non-numeric string ("abc") → leave as-is AND record a
//     `errors[]` entry so callers can surface a readable, field-named
//     validation error instead of letting the backend reply with a
//     truncated Pydantic message.
//   • null / undefined / missing → 0 for required floats, untouched
//     for Optional floats (backend default applies).
//   • Never delete user-entered text. Never duplicate. Never touch
//     idempotency. Operates on a deep clone of the body only.

const REPAIR_VERSION = 1;

function _isPlainObject(v) {
  return v !== null && typeof v === "object" && !Array.isArray(v);
}

function _cloneBody(body) {
  // Body is JSON-shaped (already serialised through the queue). A
  // structured clone is safe and avoids accidental in-place mutation
  // of the persisted entry.
  try { return JSON.parse(JSON.stringify(body)); }
  catch { return body; }
}

// Coerce a single value according to the field's contract.
//   required=true  → blank/missing/null → 0
//   required=false → blank/missing/null/undefined → null
function _coerceNumber(value, { required, path, errors, warnings }) {
  // null / undefined / missing
  if (value === null || value === undefined) {
    if (required) {
      warnings.push({ path, oldValue: value, newValue: 0, reason: "missing → 0" });
      return 0;
    }
    return value === undefined ? null : value;
  }
  // already a number
  if (typeof value === "number") {
    if (Number.isFinite(value)) return value;
    // NaN / Infinity — same treatment as malformed
    errors.push({ path, value, reason: "not a finite number" });
    return value;
  }
  // string
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (trimmed === "") {
      const replacement = required ? 0 : null;
      warnings.push({
        path, oldValue: value, newValue: replacement,
        reason: required ? "blank → 0" : "blank → null",
      });
      return replacement;
    }
    // Accept "2", "2.5", "-3", "1e2" etc. Reject anything Number() can't parse.
    const n = Number(trimmed);
    if (Number.isFinite(n)) {
      warnings.push({ path, oldValue: value, newValue: n, reason: "string → number" });
      return n;
    }
    errors.push({ path, value, reason: "not a number" });
    return value; // do not silently delete user-entered text
  }
  // any other type (object, array, bool) — flag, leave as-is
  errors.push({ path, value, reason: `not a number (${typeof value})` });
  return value;
}

/**
 * Normalize a Daily Report payload body for retry submission.
 *
 * Returns:
 *   {
 *     body:     <new body — safe deep clone, repairs applied>,
 *     warnings: [{path, oldValue, newValue, reason}],
 *     errors:   [{path, value, reason}],
 *     repaired: <bool — at least one warning applied>,
 *   }
 *
 * `errors` is non-empty when at least one numeric field contains a
 * non-numeric, non-blank string (e.g. "abc"). Callers can refuse to
 * retry until the user fixes it, or surface the field name in the UI.
 */
export function normalizeDailyReportPayload(originalBody) {
  const body = _cloneBody(originalBody);
  const warnings = [];
  const errors = [];

  if (!_isPlainObject(body)) {
    return { body: originalBody, warnings, errors, repaired: false, version: REPAIR_VERSION };
  }

  // production[].quantity — REQUIRED float
  if (Array.isArray(body.production)) {
    body.production = body.production.map((row, i) => {
      if (!_isPlainObject(row)) return row;
      const path = `production[${i}].quantity`;
      const next = _coerceNumber(row.quantity, {
        required: true, path, errors, warnings,
      });
      return { ...row, quantity: next };
    });
  }

  // constraints[].hours_impact — OPTIONAL float
  if (Array.isArray(body.constraints)) {
    body.constraints = body.constraints.map((row, i) => {
      if (!_isPlainObject(row)) return row;
      const path = `constraints[${i}].hours_impact`;
      const next = _coerceNumber(row.hours_impact, {
        required: false, path, errors, warnings,
      });
      return { ...row, hours_impact: next };
    });
  }

  // outbound_materials[].quantity — backend treats as Any, but the UI
  // initialiser uses "" so we coerce for hygiene. Treated as optional
  // (preserves backend tolerance — null means "not entered").
  if (Array.isArray(body.outbound_materials)) {
    body.outbound_materials = body.outbound_materials.map((row, i) => {
      if (!_isPlainObject(row)) return row;
      const path = `outbound_materials[${i}].quantity`;
      const next = _coerceNumber(row.quantity, {
        required: false, path, errors, warnings,
      });
      return { ...row, quantity: next };
    });
  }

  return {
    body,
    warnings,
    errors,
    repaired: warnings.length > 0,
    version: REPAIR_VERSION,
  };
}

// Compact one-line description for telemetry/logs of the rows that
// could not be repaired. Empty string when nothing is unrepairable.
export function formatUnrepairableErrors(errors) {
  if (!Array.isArray(errors) || errors.length === 0) return "";
  const parts = errors.slice(0, 3).map((e) => {
    const valStr = (typeof e.value === "string" && e.value.length > 0)
      ? `"${String(e.value).slice(0, 20)}"`
      : String(e.value);
    return `${e.path}: ${e.reason} (got ${valStr})`;
  });
  const extra = errors.length > 3 ? ` (+${errors.length - 3} more)` : "";
  return parts.join("; ") + extra;
}
