// lib/safetyAccountabilityClass.js — iter324 · Equipment & PPE aging
// accountability classifier.
//
// SCOPE / GOVERNANCE
// ──────────────────
// The Safety Portal "Equipment & PPE Accountability" surface intentionally
// surfaces aging signals (issued > 90 days, no return logged) for a tightly
// curated set of *serialized / recoverable / high-accountability* gear
// classes ONLY.
//
// CONSUMABLE / DAILY-USE PPE are EXPLICITLY EXCLUDED — these items are
// frequently replaced, commonly retained by employees, and create alert
// fatigue rather than meaningful accountability.
//
// Why inclusion (not exclusion) list?
//   The universe of PPE keywords is small and stable on the
//   accountability side. The consumable universe is open-ended (every
//   new vendor, every new product). An explicit allow-list is the
//   cleaner long-term primitive.
//
// Add a new class via ACCOUNTABILITY_CLASSES below. Do not duplicate
// patterns across the codebase — every consumer should reach for
// `getAccountabilityClass(item)` or `isAccountabilityItem(item)`.

// Each entry: { key, label_en, label_es, patterns: RegExp[] }
// `patterns` match against a normalized `item + description` blob.
export const ACCOUNTABILITY_CLASSES = [
  {
    key: "fall_protection",
    label_en: "Fall Protection",
    label_es: "Protección Contra Caídas",
    patterns: [
      /\bharness\b/i,
      /\blanyard\b/i,
      /\bsrl\b/i,
      /\bself.?retracting\b/i,
      /\bretractable\b/i,
      /\banchor\s*point\b/i,
      /\brope\s*grab\b/i,
      /\bfall\s*arrest\b/i,
      /\bfall\s*protect/i,
    ],
  },
  {
    key: "respiratory",
    label_en: "Respiratory Protection",
    label_es: "Protección Respiratoria",
    patterns: [
      /\brespirator\b/i,
      /\bpapr\b/i,
      /\bscba\b/i,
      /\bsupplied.?air\b/i,
      /\bhalf.?face\b/i,
      /\bfull.?face\b/i,
      /\bn95\s*reusable\b/i, // disposable N95 is excluded
    ],
  },
  {
    key: "gas_monitor",
    label_en: "Gas Monitor",
    label_es: "Monitor de Gas",
    patterns: [
      /\bgas\s*monitor\b/i,
      /\b4.?gas\b/i,
      /\bmulti.?gas\b/i,
      /\bh2s\b/i,
      /\bco\s*monitor\b/i,
      /\bcombustible\s*gas\b/i,
      /\blel\s*monitor\b/i,
      /\bbw\s*clip\b/i,
      /\bventis\b/i,
    ],
  },
  {
    key: "confined_space",
    label_en: "Confined Space Equipment",
    label_es: "Equipo de Espacio Confinado",
    patterns: [
      /\bconfined\s*space\b/i,
      /\btripod\b/i,
      /\bwinch\b/i,
      /\bblower\b/i,
      /\bventilator\b/i,
    ],
  },
  {
    key: "fr_arc_flash",
    label_en: "FR / Arc-Flash Gear",
    label_es: "Equipo FR / Arco Eléctrico",
    patterns: [
      /\barc.?flash\b/i,
      /\bfr\s*(coverall|jacket|pant|suit|hood|gear)\b/i,
      /\bflame.?resist/i,
      /\bcat\s*[234]\b/i,
    ],
  },
  {
    key: "specialty_traffic",
    label_en: "Traffic-Control Specialty",
    label_es: "Equipo de Control de Tráfico",
    patterns: [
      /\bspotter\s*kit\b/i,
      /\bflagger\s*kit\b/i,
      /\btraffic\s*control\s*kit\b/i,
      /\bcone\s*cart\b/i,
    ],
  },
  {
    key: "calibrated_device",
    label_en: "Calibrated Safety Device",
    label_es: "Dispositivo Calibrado",
    patterns: [
      /\bcalibrat/i,
      /\bbump\s*test\b/i,
      /\bsound\s*level\s*meter\b/i,
      /\bdosimeter\b/i,
      /\btorque\s*wrench\s*calibrated\b/i,
    ],
  },
  {
    key: "welding",
    label_en: "Welding Hood / Shield",
    label_es: "Casco de Soldadura",
    patterns: [
      /\bwelding\s*hood\b/i,
      /\bwelding\s*helmet\b/i,
      /\bwelding\s*shield\b/i,
      /\bauto.?darkening\b/i,
    ],
  },
];

// ───────── Explicit consumable / daily-use exclusions ─────────
//
// These keywords are evaluated FIRST. Any match here disqualifies the
// item even if it otherwise matches an accountability pattern (e.g.,
// "hard hat with fall-protection chin strap" — still a hard hat).
const CONSUMABLE_PATTERNS = [
  /\bhard\s*hat\b/i,
  /\bsafety\s*glasses?\b/i,
  /\bsafety\s*goggles?\b/i,
  /\bsafety\s*vest\b/i,
  /\bhi.?vis\s*vest\b/i,
  /\bclass\s*[23]\s*vest\b/i,
  /\bgloves?\b/i,
  /\bear\s*plug/i,
  /\bhearing\s*protect/i,
  /\bearmuffs?\b/i,
  /\bdust\s*mask\b/i,
  /\bdisposable\s*n95\b/i,
  /\bdisposable\s*mask\b/i,
  /\bsteel\s*toe\s*boots?\b/i,
  /\brain\s*coat\b/i, // basic rain coat — expensive rain *suits* still match welding/FR if labeled
  /\bpoly\s*boots?\b/i,
  /\bknee\s*pads?\b/i,
  /\bsunscreen\b/i,
  /\bwater\s*bottle\b/i,
  /\bcooling\s*towel\b/i,
];

function _blob(item) {
  // Issuance line-items use `item_type` (and sometimes `item_type_other`
  // for free-text). Older shapes used `item`. Match all of them.
  return `${item?.item_type || ""} ${item?.item_type_other || ""} ${item?.item || ""} ${item?.description || ""}`.trim();
}

/**
 * Returns the accountability class key for an issuance line-item, or
 * null when the item is consumable / unclassified.
 *
 * @param {object} item — an entry from `issuance.items[]`
 * @returns {string|null}
 */
export function getAccountabilityClass(item) {
  if (!item) return null;
  const blob = _blob(item);
  if (!blob) return null;
  // Consumable exclusions win — daily PPE never raises a signal.
  for (const p of CONSUMABLE_PATTERNS) if (p.test(blob)) return null;
  for (const cls of ACCOUNTABILITY_CLASSES) {
    for (const p of cls.patterns) if (p.test(blob)) return cls.key;
  }
  return null;
}

export function isAccountabilityItem(item) {
  return getAccountabilityClass(item) !== null;
}

/**
 * Days since YYYY-MM-DD (UTC-safe enough for day-granularity aging).
 */
export function daysSince(iso) {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  const ms = Date.now() - d.getTime();
  return Math.floor(ms / 86400000);
}

/**
 * True when an issuance record qualifies for the accountability
 * aging signal:
 *   • no return logged AND
 *   • issued more than `thresholdDays` ago AND
 *   • at least one line-item is an accountability class.
 *
 * @param {object} rec — issuance record from /api/safety-forms/equipment-issuances
 * @param {number} thresholdDays — default 90
 */
export function isAgingAccountability(rec, thresholdDays = 90) {
  if (!rec || rec.return) return false;
  const age = daysSince(rec.issued_date);
  if (age === null || age <= thresholdDays) return false;
  const items = Array.isArray(rec.items) ? rec.items : [];
  return items.some(isAccountabilityItem);
}

/**
 * Returns the unique sorted accountability-class labels present on a
 * record. Used by row indicators / tooltips.
 *
 * @param {object} rec — issuance record
 * @param {"en"|"es"} lang
 * @returns {string[]} display labels
 */
export function accountabilityClassLabels(rec, lang = "en") {
  if (!rec) return [];
  const items = Array.isArray(rec.items) ? rec.items : [];
  const keys = new Set(items.map(getAccountabilityClass).filter(Boolean));
  return ACCOUNTABILITY_CLASSES
    .filter((c) => keys.has(c.key))
    .map((c) => (lang === "es" ? c.label_es : c.label_en));
}
