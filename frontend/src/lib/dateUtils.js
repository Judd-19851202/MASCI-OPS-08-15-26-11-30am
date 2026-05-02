// Local-time date helpers.
//
// We previously defaulted every form's date field to
// `new Date().toISOString().slice(0, 10)`, which returns the UTC date.
// For any crew member east of UTC‑0 (Florida foremen included), after
// ~7 PM local the default would roll forward to "tomorrow" even though
// the user was still living in "today". That's the "I pick one date but
// a different one auto-populates" bug PMs reported.
//
// `todayLocalIso()` returns YYYY-MM-DD in the browser's local timezone,
// which is what a native <input type="date"> shows and what the user
// actually means when they look at the calendar.

const _pad = (n) => String(n).padStart(2, "0");

export function todayLocalIso(now = new Date()) {
  return `${now.getFullYear()}-${_pad(now.getMonth() + 1)}-${_pad(now.getDate())}`;
}

export function toLocalIso(date) {
  if (!date) return "";
  const d = date instanceof Date ? date : new Date(date);
  if (Number.isNaN(d.getTime())) return "";
  return `${d.getFullYear()}-${_pad(d.getMonth() + 1)}-${_pad(d.getDate())}`;
}
