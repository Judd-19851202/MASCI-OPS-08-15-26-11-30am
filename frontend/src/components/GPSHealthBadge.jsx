/**
 * OIS-1F · GPS Health Badge — single source of truth for green/amber/red
 * GPS staleness banding across MASCI Docs. Mirrors the backend bands in
 * `/app/backend/routes/operations_intelligence.py`:
 *   green  : < 30 min       (GPS Active)
 *   amber  : < 24 hr        (GPS Stale)
 *   red    : >= 24 hr | null (Not Reporting)
 *
 * Used by:
 *   • AssetProfile Motive tab
 *   • Dispatch Board assignment chips (planned)
 *   • Operations Center single-pane tiles
 *   • Shop Hub Equipment-Down list
 */
import React from "react";

const GREEN_MAX_MIN = 30;
const AMBER_MAX_MIN = 24 * 60;

export function gpsBand(locatedAtIso) {
  if (!locatedAtIso) return { band: "red", minutes: null, label: "Not Reporting" };
  try {
    const ts = new Date(locatedAtIso);
    const mins = Math.floor((Date.now() - ts.getTime()) / 60000);
    if (mins < GREEN_MAX_MIN) return { band: "green", minutes: mins, label: `GPS Active · ${mins} min ago` };
    if (mins < AMBER_MAX_MIN) {
      const hrs = Math.floor(mins / 60);
      return { band: "amber", minutes: mins, label: `GPS Stale · ${hrs} hr ago` };
    }
    const days = Math.floor(mins / (60 * 24));
    return { band: "red", minutes: mins, label: `Not Reporting · ${days}d` };
  } catch {
    return { band: "red", minutes: null, label: "Not Reporting" };
  }
}

const PILL = {
  green: "bg-emerald-100 text-emerald-900 border-emerald-300",
  amber: "bg-amber-100 text-amber-900 border-amber-300",
  red:   "bg-rose-100 text-rose-900 border-rose-300",
};

export function GPSHealthBadge({ locatedAt, compact = false, testId }) {
  const b = gpsBand(locatedAt);
  const cls = PILL[b.band] || PILL.red;
  if (compact) {
    return (
      <span
        className={`inline-block w-2.5 h-2.5 rounded-full border ${cls}`}
        title={b.label}
        data-testid={testId || `gps-dot-${b.band}`}
      />
    );
  }
  return (
    <span
      className={`px-1.5 py-0.5 rounded border font-mono text-[10px] uppercase tracking-[0.15em] font-bold ${cls}`}
      data-testid={testId || `gps-badge-${b.band}`}
    >
      {b.label}
    </span>
  );
}

export default GPSHealthBadge;
