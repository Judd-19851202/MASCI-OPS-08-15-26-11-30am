// dateUtils.js — TRUST-TIME-1 doctrine (2026-05-28)
// UPDATED 2026-07-09 · TRACK 27.03 · Final Completion Track.
// This module now DELEGATES all formatting to the canonical
// `platformTime.js` formatter. It is kept as a compatibility surface
// for older imports across the codebase — every helper below is a
// thin wrapper. New code should import from `platformTime.js` directly.
// ─────────────────────────────────────────────────────────────────
import {
  formatPlatformTime,
  formatPlatformDate,
  formatPlatformTimeOnly,
  formatRelativeTime as _formatRelativeTime,
} from "@/lib/platformTime";

const _pad = (n) => String(n).padStart(2, "0");

// Defensively coerce: if the incoming string lacks ANY tz suffix
// (no `Z`, no `+HH:MM`, no `-HH:MM` past the date), JS treats it as
// LOCAL time per the ECMAScript spec. This is the exact bug that
// caused PO receipt uploads to show +4h. Tag naive ISO as UTC so
// older records still localize correctly.
function _coerce(ts) {
  if (!ts) return null;
  if (ts instanceof Date) return ts;
  if (typeof ts === "number") return new Date(ts);
  if (typeof ts !== "string") return null;
  const s = ts.trim();
  // Has explicit tz? Use as-is.
  if (/Z$|[+-]\d\d:?\d\d$/.test(s)) {
    const d = new Date(s);
    return Number.isNaN(d.getTime()) ? null : d;
  }
  // Naive ISO ("2026-05-28T13:43:00" or "2026-05-28T13:43:00.123") →
  // treat as UTC.
  if (/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(s)) {
    const d = new Date(s + "Z");
    return Number.isNaN(d.getTime()) ? null : d;
  }
  // Date-only "2026-05-28" → treat as that calendar day in LOCAL time.
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) {
    const d = new Date(`${s}T00:00:00`);
    return Number.isNaN(d.getTime()) ? null : d;
  }
  const d = new Date(s);
  return Number.isNaN(d.getTime()) ? null : d;
}

export function todayLocalIso(now = new Date()) {
  return `${now.getFullYear()}-${_pad(now.getMonth() + 1)}-${_pad(now.getDate())}`;
}

export function toLocalIso(date) {
  const d = _coerce(date);
  if (!d) return "";
  return `${d.getFullYear()}-${_pad(d.getMonth() + 1)}-${_pad(d.getDate())}`;
}

export function formatLocalDateTime(ts) {
  return _coerce(ts) ? formatPlatformTime(_coerce(ts)) : "";
}

export function formatLocalDate(ts) {
  return _coerce(ts) ? formatPlatformDate(_coerce(ts)) : "";
}

export function formatLocalTime(ts) {
  return _coerce(ts) ? formatPlatformTimeOnly(_coerce(ts)) : "";
}

// Compact "5/28 9:43 AM" for narrow list cells.
export function formatLocalShort(ts) {
  const d = _coerce(ts);
  if (!d) return "";
  return `${formatPlatformDate(d)} ${formatPlatformTimeOnly(d)}`;
}

export function formatRelativeTime(ts) {
  const d = _coerce(ts);
  if (!d) return "";
  return _formatRelativeTime(d);
}

// AUDIT ONLY. Preserved for legacy admin/audit surfaces that
// explicitly need UTC (e.g. comparing timestamps across timezones).
// New surfaces MUST use `formatPlatformTime` instead.
export function formatUtcForAudit(ts) {
  const d = _coerce(ts);
  if (!d) return "";
  const yyyy = d.getUTCFullYear();
  const mm = _pad(d.getUTCMonth() + 1);
  const dd = _pad(d.getUTCDate());
  const hh = _pad(d.getUTCHours());
  const mn = _pad(d.getUTCMinutes());
  return `${yyyy}-${mm}-${dd} ${hh}:${mn} UTC`;  // TRACK-27.03-EXEMPT: audit-only helper; caller must intentionally opt in for cross-tz comparison; NOT used in default display paths
}

// Test seam.
export const __TESTING__ = { _coerce };
