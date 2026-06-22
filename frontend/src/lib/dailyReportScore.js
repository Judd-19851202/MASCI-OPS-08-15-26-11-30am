// TRACK 15.62 · Session B · Daily Report score helper.
// Mirrors the backend `lib/daily_report_rollup.py` narrative_health
// scoring so the CompletenessChip lights up in real time as the
// operator fills in fields. NO fake percentages — every point is
// awarded ONLY for operationally meaningful content.

export const DR_SCORE_DIMENSIONS = [
  { key: "narrative_work",   label: "Work narrative",          weight: 2 },
  { key: "narrative_delays", label: "Delays / constraints",    weight: 1 },
  { key: "narrative_tomorrow", label: "Tomorrow plan",         weight: 1 },
  { key: "haul_recorded",    label: "Haul activity",           weight: 1 },
  { key: "materials_or_production", label: "Materials / production", weight: 1 },
  { key: "crew_present",     label: "Crew listed",             weight: 1 },
  { key: "photos_captioned", label: "Photos w/ captions",      weight: 1 },
  { key: "identity_bound",   label: "Preparer identity",       weight: 1 },
];

const wc = (s) => (typeof s === "string" ? s.trim().split(/\s+/).filter(Boolean).length : 0);

export function scoreDailyReport(d = {}) {
  const ns = d.narrative_sections || {};
  const acts = d.activities || [];
  const captions = (d.photo_captions || []).filter((c) => typeof c === "string" && c.trim());
  const photos = d.photos || [];
  const haul = d.outbound_materials || [];
  const inMats = d.materials || [];
  const prod = d.production || [];
  const crews = d.masci_crews || [];
  const subs = d.subcontractors || [];

  const dims = {};

  // Work narrative — counts ONLY if there is meaningful prose (≥ 10 words
  // somewhere) OR ≥ 1 activity row with description. Photos alone do NOT
  // satisfy this dimension — that was the 15.61 anti-pattern.
  const workWords = wc(ns.work_completed) + wc(d.general_notes) +
    acts.reduce((n, a) => n + wc((a && a.description) || ""), 0);
  dims.narrative_work = workWords >= 10 ? 2 : workWords >= 4 ? 1 : 0;

  // Delays / constraints
  dims.narrative_delays = (wc(ns.delays) >= 4 || (d.constraints || []).length > 0 ||
    wc(d.schedule_delays_notes) >= 4 || wc(d.weather_impact_notes) >= 4) ? 1 : 0;

  // Tomorrow plan
  dims.narrative_tomorrow = wc(ns.tomorrow_plan) >= 4 ? 1 : 0;

  // Haul activity — at least one outbound row with a material
  dims.haul_recorded = haul.some((r) => r && (r.material || "").trim()) ? 1 : 0;

  // Materials in OR production — at least one row
  dims.materials_or_production = (inMats.length > 0 || prod.length > 0) ? 1 : 0;

  // Crew present
  dims.crew_present = (crews.length > 0 || subs.length > 0) ? 1 : 0;

  // Photos with captions — at least one captioned photo (NOT just photo count)
  dims.photos_captioned = (photos.length > 0 && captions.length > 0) ? 1 : 0;

  // Identity bound — preparer carries an employee id (not free-text only)
  dims.identity_bound = ((d.prepared_by_identity || d.prepared_by_employee_id || "").toString().trim()) ? 1 : 0;

  const total = Object.values(dims).reduce((a, b) => a + b, 0);
  const max = DR_SCORE_DIMENSIONS.reduce((a, d) => a + d.weight, 0);
  const pct = Math.round((100 * total) / max);

  let label = "Needs work";
  let color = "red";
  if (pct >= 80) { label = "Operationally complete"; color = "green"; }
  else if (pct >= 60) { label = "Good"; color = "emerald"; }
  else if (pct >= 40) { label = "Partial"; color = "amber"; }

  return { total, max, pct, label, color, dimensions: dims };
}

export default scoreDailyReport;
