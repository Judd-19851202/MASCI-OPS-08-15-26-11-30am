/**
 * gpsBand.js · OIS-1F · Universal GPS Health System (read-only)
 * ─────────────────────────────────────────────────────────────
 * Single source of truth for GPS staleness classification across
 * MASCI Docs surfaces. Mirrors the backend `_gps_band` helper in
 * /app/backend/routes/operations_intelligence.py so frontend and
 * backend never disagree.
 *
 * Bands:
 *   green  → "Reporting"     (< 30 min)
 *   amber  → "Stale"         (< 24 hr)
 *   red    → "Not Reporting" (≥ 24 hr or never)
 *
 * Usage:
 *   import { gpsBand, gpsBandClass } from "@/lib/gpsBand";
 *   const b = gpsBand(asset.located_at);
 *   <span className={gpsBandClass(b.band)}>{b.label}</span>
 */

export const GPS_GREEN_MAX_MIN = 30;
export const GPS_AMBER_MAX_MIN = 24 * 60;

export function gpsBand(locatedAt) {
  if (!locatedAt) return { band: "red", minutes: null, label: "Not Reporting" };
  let ts;
  try {
    ts = new Date(locatedAt).getTime();
  } catch {
    return { band: "red", minutes: null, label: "Not Reporting" };
  }
  if (Number.isNaN(ts)) return { band: "red", minutes: null, label: "Not Reporting" };
  const mins = Math.max(0, Math.round((Date.now() - ts) / 60000));
  if (mins < GPS_GREEN_MAX_MIN) {
    return { band: "green", minutes: mins, label: `Reporting · ${mins} min ago` };
  }
  if (mins < GPS_AMBER_MAX_MIN) {
    const hrs = Math.floor(mins / 60);
    return { band: "amber", minutes: mins, label: `Stale · ${hrs} hr ago` };
  }
  const days = Math.floor(mins / (60 * 24));
  return { band: "red", minutes: mins, label: `Not Reporting · ${days}d` };
}

// Tailwind classes (badge — small inline pill, calm palette)
const BAND_BADGE = {
  green: "bg-emerald-100 text-emerald-900 border-emerald-300",
  amber: "bg-amber-100 text-amber-900 border-amber-300",
  red:   "bg-rose-100 text-rose-900 border-rose-300",
};

export function gpsBandClass(band) {
  return BAND_BADGE[band] || BAND_BADGE.red;
}

// Short label (for tight UI like DispatchBoard row)
export function gpsBandShort(band) {
  if (band === "green") return "GPS";
  if (band === "amber") return "Stale";
  return "No GPS";
}
