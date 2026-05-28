// dateUtils.js — TRUST-TIME-1 doctrine (2026-05-28)
// ─────────────────────────────────────────────────────────────────
//
// Truthful-state doctrine for time on the platform:
//
//   1. The backend STORES timestamps in UTC and emits them as
//      ABSOLUTE (tz-aware) ISO strings — `2026-05-28T13:43:00+00:00`.
//   2. The frontend RENDERS them in the operator's local browser
//      timezone — `5/28/2026, 9:43 AM` for a Florida foreman.
//   3. Any UTC string shown to an operator MUST be visibly labeled
//      "UTC" so they can spot an audit-only render.
//   4. NEVER use `.slice(11, 16)` on an ISO string to "get the time"
//      — that displays the UTC clock as if it were local time, which
//      is what produced the +4h delta on PO receipt uploads.
//
// Helpers
// -------
//   todayLocalIso(now?)         · "YYYY-MM-DD" in the local timezone
//   toLocalIso(date)            · same, accepts Date/string/Date-able
//   formatLocalDateTime(ts)     · "5/28/2026, 9:43 AM" — primary helper
//   formatLocalDate(ts)         · "5/28/2026"
//   formatLocalTime(ts)         · "9:43 AM"
//   formatLocalShort(ts)        · "5/28 9:43 AM" — compact list view
//   formatRelativeTime(ts)      · "3m ago" · "2h ago" · "yesterday"
//   formatUtcForAudit(ts)       · "2026-05-28 13:43 UTC" — only when
//                                 the audit log explicitly wants UTC

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
  // Date-only "2026-05-28" → treat as that calendar day in LOCAL time
  // (so "tomorrow's PO" doesn't shift to today on the UTC side).
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
  const d = _coerce(ts);
  if (!d) return "";
  return d.toLocaleString();
}

export function formatLocalDate(ts) {
  const d = _coerce(ts);
  if (!d) return "";
  return d.toLocaleDateString();
}

export function formatLocalTime(ts) {
  const d = _coerce(ts);
  if (!d) return "";
  return d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

// Compact "5/28 9:43 AM" for narrow list cells. Skips the year on
// purpose — operators reading a recent list rarely need it.
export function formatLocalShort(ts) {
  const d = _coerce(ts);
  if (!d) return "";
  const date = d.toLocaleDateString([], { month: "numeric", day: "numeric" });
  const time = d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  return `${date} ${time}`;
}

export function formatRelativeTime(ts) {
  const d = _coerce(ts);
  if (!d) return "";
  const now = Date.now();
  const delta = Math.round((now - d.getTime()) / 1000);
  if (delta < 0) return "just now";
  if (delta < 60) return `${delta}s ago`;
  const mins = Math.round(delta / 60);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  if (days === 1) return "yesterday";
  if (days < 30) return `${days}d ago`;
  return formatLocalDate(d);
}

// AUDIT ONLY. Use exclusively when the surface is explicitly an
// admin/audit view and the operator needs to compare clocks across
// timezones. Output is suffixed with " UTC".
export function formatUtcForAudit(ts) {
  const d = _coerce(ts);
  if (!d) return "";
  const yyyy = d.getUTCFullYear();
  const mm = _pad(d.getUTCMonth() + 1);
  const dd = _pad(d.getUTCDate());
  const hh = _pad(d.getUTCHours());
  const mn = _pad(d.getUTCMinutes());
  return `${yyyy}-${mm}-${dd} ${hh}:${mn} UTC`;
}

// Test seam.
export const __TESTING__ = { _coerce };
