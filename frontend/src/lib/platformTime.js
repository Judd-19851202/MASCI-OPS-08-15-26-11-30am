/**
 * TRACK 27.03 · Canonical platform time formatter.
 *
 * ONE code path — the only one — that turns a UTC timestamp into
 * something an operator sees. Every user-facing surface (dashboards,
 * PDFs, emails, exports, AI outputs, toasts, success screens, audit
 * viewers, history panels, snapshot cards) MUST import from this
 * module. Never call `toISOString`, `toUTCString`, `.utc()`, or
 * `strftime` in user-facing code.
 *
 * Timezone resolution (highest priority first):
 *   1. User preference (localStorage: `masci.tz.user`)
 *   2. Organization preference (localStorage: `masci.tz.org`)
 *   3. Browser timezone (`Intl.DateTimeFormat().resolvedOptions().timeZone`)
 *   4. Server fallback: 'America/New_York' — ONLY reached if all
 *      three above fail (impossible in a real browser).
 *
 * Never hardcode a specific zone in a component. If you catch
 * yourself typing `'America/New_York'` outside this file, stop —
 * you're violating the rule.
 *
 * Storage remains UTC. Backend still writes UTC to Mongo, logs still
 * use UTC. This module is exclusively for display.
 */

const LS_USER_TZ = "masci.tz.user";
const LS_ORG_TZ  = "masci.tz.org";
const LS_HOUR_FMT = "masci.tz.hour_format";        // "12" | "24"

const SERVER_FALLBACK_TZ = "America/New_York";


/**
 * Resolve the current operator timezone using the documented priority.
 * Safe to call anywhere — never throws. Always returns a valid IANA
 * zone string.
 */
export function getPlatformTimezone() {
  try {
    const userTz = typeof localStorage !== "undefined" && localStorage.getItem(LS_USER_TZ);
    if (userTz) return userTz;
    const orgTz = typeof localStorage !== "undefined" && localStorage.getItem(LS_ORG_TZ);
    if (orgTz) return orgTz;
    const browserTz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    if (browserTz) return browserTz;
  } catch (_) {
    // fall through
  }
  return SERVER_FALLBACK_TZ;
}

export function setUserTimezone(tz)         { try { localStorage.setItem(LS_USER_TZ, tz); } catch (_) {} }
export function setOrganizationTimezone(tz) { try { localStorage.setItem(LS_ORG_TZ, tz); }  catch (_) {} }
export function clearUserTimezone()         { try { localStorage.removeItem(LS_USER_TZ); }  catch (_) {} }

export function getHourFormat() {
  try {
    const v = localStorage.getItem(LS_HOUR_FMT);
    if (v === "12" || v === "24") return v;
  } catch (_) {}
  return "12";
}


/**
 * Coerce any accepted input (Date, ISO string, epoch ms number, null,
 * undefined) into a Date. Returns null for unusable inputs so
 * callers can render a placeholder instead of crashing.
 */
function _toDate(value) {
  if (value === null || value === undefined || value === "") return null;
  if (value instanceof Date) return isNaN(value.getTime()) ? null : value;
  if (typeof value === "number") {
    const d = new Date(value);
    return isNaN(d.getTime()) ? null : d;
  }
  if (typeof value === "string") {
    const d = new Date(value);
    return isNaN(d.getTime()) ? null : d;
  }
  return null;
}


/**
 * The canonical formatter: full local date + time.
 *   formatPlatformTime("2026-07-09T18:53:24Z") → "Jul 9, 2026 · 2:53 PM"
 *
 * Never renders UTC, GMT, Z, or the raw ISO string.
 */
export function formatPlatformTime(value, opts = {}) {
  const d = _toDate(value);
  if (!d) return opts.fallback ?? "—";
  const tz = opts.timezone || getPlatformTimezone();
  const hour12 = (opts.hourFormat || getHourFormat()) === "12";
  try {
    const datePart = new Intl.DateTimeFormat(undefined, {
      timeZone: tz, year: "numeric", month: "short", day: "numeric",
    }).format(d);
    const timePart = new Intl.DateTimeFormat(undefined, {
      timeZone: tz, hour: "numeric", minute: "2-digit", hour12,
    }).format(d);
    return `${datePart} · ${timePart}`;
  } catch (_) {
    return opts.fallback ?? "—";
  }
}


/**
 * Date only. Used in table cells that can't fit a full timestamp.
 *   formatPlatformDate("2026-07-09T18:53:24Z") → "Jul 9, 2026"
 */
export function formatPlatformDate(value, opts = {}) {
  const d = _toDate(value);
  if (!d) return opts.fallback ?? "—";
  const tz = opts.timezone || getPlatformTimezone();
  try {
    return new Intl.DateTimeFormat(undefined, {
      timeZone: tz, year: "numeric", month: "short", day: "numeric",
    }).format(d);
  } catch (_) {
    return opts.fallback ?? "—";
  }
}


/**
 * Time only. Used in dense list rows.
 *   formatPlatformTimeOnly("2026-07-09T18:53:24Z") → "2:53 PM"
 */
export function formatPlatformTimeOnly(value, opts = {}) {
  const d = _toDate(value);
  if (!d) return opts.fallback ?? "—";
  const tz = opts.timezone || getPlatformTimezone();
  const hour12 = (opts.hourFormat || getHourFormat()) === "12";
  try {
    return new Intl.DateTimeFormat(undefined, {
      timeZone: tz, hour: "numeric", minute: "2-digit", hour12,
    }).format(d);
  } catch (_) {
    return opts.fallback ?? "—";
  }
}


/**
 * Relative time with local-time hover (e.g. "Today · 2:53 PM",
 * "Yesterday · 4:12 PM", "3 days ago · 9:11 AM", "Jul 9, 2026 · 2:53 PM").
 *
 * Anything older than 6 days falls back to the full date-time so
 * operators never squint at "23 days ago" and wonder which day.
 */
export function formatRelativeTime(value, opts = {}) {
  const d = _toDate(value);
  if (!d) return opts.fallback ?? "—";
  const tz = opts.timezone || getPlatformTimezone();
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffSec = Math.round(diffMs / 1000);
  const time = formatPlatformTimeOnly(d, { timezone: tz, hourFormat: opts.hourFormat });

  if (Math.abs(diffSec) < 60) return "Just now";
  if (Math.abs(diffSec) < 3600) {
    const m = Math.round(diffSec / 60);
    return diffSec > 0 ? `${m} min ago` : `in ${Math.abs(m)} min`;
  }

  // Day-based classification — compare local-tz calendar days, not
  // raw ms, so 11:59 PM on Monday and 12:01 AM on Tuesday show as
  // "Yesterday" and "Today" respectively for the operator.
  const localYMD = (dt) => new Intl.DateTimeFormat("en-CA", {
    timeZone: tz, year: "numeric", month: "2-digit", day: "2-digit",
  }).format(dt);
  const today = localYMD(now);
  const target = localYMD(d);

  if (today === target) return `Today · ${time}`;

  const yesterday = new Date(now);
  yesterday.setDate(yesterday.getDate() - 1);
  if (localYMD(yesterday) === target) return `Yesterday · ${time}`;

  const daysDiff = Math.round(diffSec / 86400);
  if (daysDiff > 0 && daysDiff <= 6) return `${daysDiff} days ago · ${time}`;

  return formatPlatformTime(d, { timezone: tz, hourFormat: opts.hourFormat });
}


/**
 * Machine-readable local ISO-like stamp for PDF footers / exports
 * that need a compact but LOCAL string (never UTC).
 *   → "2026-07-09 14:53 EDT"
 */
export function formatPlatformStamp(value, opts = {}) {
  const d = _toDate(value);
  if (!d) return opts.fallback ?? "—";
  const tz = opts.timezone || getPlatformTimezone();
  const hour12 = (opts.hourFormat || getHourFormat()) === "12";
  try {
    const parts = new Intl.DateTimeFormat("en-CA", {
      timeZone: tz, year: "numeric", month: "2-digit", day: "2-digit",
      hour: "2-digit", minute: "2-digit", hour12,
      timeZoneName: "short",
    }).formatToParts(d);
    const get = (t) => parts.find((p) => p.type === t)?.value || "";
    return `${get("year")}-${get("month")}-${get("day")} ${get("hour")}:${get("minute")}${hour12 ? " " + get("dayPeriod") : ""} ${get("timeZoneName")}`.trim();
  } catch (_) {
    return opts.fallback ?? "—";
  }
}


/**
 * Test-only reset used by the regression suite; safe to call in
 * production — clears any user or org override so we fall back to
 * the browser zone.
 */
export function _resetForTests() {
  try {
    localStorage.removeItem(LS_USER_TZ);
    localStorage.removeItem(LS_ORG_TZ);
    localStorage.removeItem(LS_HOUR_FMT);
  } catch (_) {}
}
