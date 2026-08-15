// humanDuration.js — shared, human-readable elapsed-time formatter.
//
// Truth-program readability guard: raw-minute strings ("113996 min",
// "6594m") are technically accurate but unreadable. This renders the
// same magnitude as days/hours/minutes without changing the value.
//   null / NaN            → "—"  (unavailable, never "0m")
//   < 60 min              → "42m"
//   < 24 h                → "3h" / "3h 15m"
//   ≥ 24 h                → "4d" / "4d 6h"
export function humanDuration(minutes) {
  if (minutes == null || Number.isNaN(Number(minutes))) return "—";
  const m = Math.max(0, Math.round(Number(minutes)));
  if (m < 60) return `${m}m`;
  const h = Math.floor(m / 60);
  if (h < 24) {
    const r = m % 60;
    return r ? `${h}h ${r}m` : `${h}h`;
  }
  const d = Math.floor(h / 24);
  const rh = h % 24;
  return rh ? `${d}d ${rh}h` : `${d}d`;
}
