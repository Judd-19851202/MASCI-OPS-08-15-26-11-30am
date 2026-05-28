// priorUsage.js — TRUST-1 · TF-001 · 2026-05-27.
//
// Tiny localStorage beacon that records "this device has saved or
// submitted a Daily Report at least once." The autosave hook and the
// submit handler both write to it. On a subsequent mount where the
// live draft AND the archive are both absent, the presence of this
// beacon is what triggers the calm "no recent draft data on this
// iPad" soft banner — letting us tell a returning-foreman from a
// genuinely first-time user.
//
// Doctrine
// --------
//   * localStorage only — no server roundtrip, no admin visibility.
//   * Per-formKey beacon: `masci.prior-usage.<formKey>` →
//     `{ first: <ms>, last: <ms>, count: n }`.
//   * The beacon NEVER stores form content. Just three numbers.
//   * Stale window: a banner is only meaningful after >= 24h since
//     last save, so the helper exposes `hasStalePriorUsage(formKey,
//     minAgeMs)` to gate the banner.
//   * No clear API beyond test reset — the beacon is calm metadata,
//     not operator-managed.

const PREFIX = "masci.prior-usage.";
const DEFAULT_MIN_STALE_AGE_MS = 24 * 60 * 60 * 1000; // 24h

function _key(formKey) {
  return `${PREFIX}${formKey || "default"}`;
}

function _read(formKey) {
  try {
    const raw = localStorage.getItem(_key(formKey));
    if (!raw) return null;
    const obj = JSON.parse(raw);
    if (!obj || typeof obj !== "object") return null;
    return obj;
  } catch {
    return null;
  }
}

function _write(formKey, obj) {
  try {
    localStorage.setItem(_key(formKey), JSON.stringify(obj));
  } catch { /* ignore quota / disabled */ }
}

/**
 * Record that this device has saved or submitted on `formKey`.
 * Called from useFormDraft on first successful write, and from form
 * submit handlers on confirmed delivery. Idempotent / additive.
 */
export function markPriorUsage(formKey) {
  if (!formKey) return;
  const now = Date.now();
  const existing = _read(formKey);
  if (existing) {
    _write(formKey, {
      first: existing.first || now,
      last: now,
      count: (existing.count || 0) + 1,
    });
  } else {
    _write(formKey, { first: now, last: now, count: 1 });
  }
}

/** Returns the beacon record or null. */
export function getPriorUsage(formKey) {
  return _read(formKey);
}

/**
 * Returns true when the beacon exists and `last` is at least
 * `minAgeMs` old. This is the calm gate for the TF-001 soft banner —
 * we only surface "no recent draft data" when the device clearly HAS
 * used the form before AND enough time has passed that local storage
 * could realistically have been swept (e.g., Safari ITP).
 */
export function hasStalePriorUsage(formKey, minAgeMs = DEFAULT_MIN_STALE_AGE_MS) {
  const rec = _read(formKey);
  if (!rec || !rec.last) return false;
  return (Date.now() - rec.last) >= minAgeMs;
}

// Test-only seam.
export const __TESTING__ = { PREFIX, DEFAULT_MIN_STALE_AGE_MS };
