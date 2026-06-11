/* eslint-disable max-len */
/* Phase 5B · Live Operations Map V1 · SVG sprite definitions
 * Eleven asset categories rendered as 24×24 status-ringed glyphs.
 * Color is applied at render-time via the `fill` token; the ring
 * uses the band color via stroke.
 */
export const ASSET_KIND_LABEL = {
  paver:        "Paver",
  mill:         "Mill",
  roller:       "Roller",
  excavator:    "Excavator",
  dozer:        "Dozer",
  motor_grader: "Motor Grader",
  loader:       "Loader",
  water_truck:  "Water Truck",
  dump_truck:   "Dump Truck",
  service_truck:"Service Truck",
  pickup:       "Pickup",
};

const BAND_COLOR = { green: "#22c55e", amber: "#f59e0b", red: "#ef4444", gray: "#64748b" };

const GLYPHS = {
  // Each glyph is a single <path> drawn inside a 24×24 viewbox, fill-current.
  paver:        "M3 14h18v3H3zM4 11h16v3H4zM6 8h12v3H6z",
  mill:         "M3 13h18v4H3zM6 9h12l-2 4H8z",
  roller:       "M5 15a4 4 0 1 1 8 0 4 4 0 0 1-8 0zm9-2h7v4h-7z",
  excavator:    "M3 15h10v3H3zM4 12h2v3H4zM7 9l4 3v3H7zM13 8l7-4 1 2-6 4z",
  dozer:        "M3 13h12v4H3zm12 0l4-2v6h-4zM4 10h10v3H4z",
  motor_grader: "M3 14h18v3H3zM7 11h14v3H7zM5 8l6 3-2 1z",
  loader:       "M3 14h12v3H3zM12 11l5 1 3 2-3 3h-5zM4 11h7v3H4z",
  water_truck:  "M3 13h6l2-3h6v3h4v4H3zM6 8h2v3H6zm6 0h2v3h-2z",
  dump_truck:   "M3 14h11v3H3zM14 9h6l1 5h-7zM5 11h7v3H5z",
  service_truck:"M3 14h11v3H3zM14 11h7v3h-7zM5 11h7v3H5zM16 8h3v3h-3z",
  pickup:       "M3 14h10v3H3zM13 11l5 1 3 2v3h-8z",
};

export function spriteUrl(kind, band) {
  const glyph = GLYPHS[kind] || GLYPHS.service_truck;
  const ring  = BAND_COLOR[band] || BAND_COLOR.gray;
  // 32x32 with a 14-radius ring around a 24x24 glyph (centered).
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
    <circle cx="16" cy="16" r="14" fill="#0e1626" stroke="${ring}" stroke-width="2.5"/>
    <g transform="translate(4,4)" fill="#f1f5f9"><path d="${glyph}"/></g>
  </svg>`;
  return "data:image/svg+xml;base64," + btoa(svg);
}

export const KIND_LIST = Object.keys(ASSET_KIND_LABEL);
