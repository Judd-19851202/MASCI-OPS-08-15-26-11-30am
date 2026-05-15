// portalPalette.js — iter143. Single source of truth for the per-portal
// Tailwind class palettes used on Hub.jsx and the sub-hub landing pages.
//
// Previously the same color tables (admin=slate-900, hr=purple-700,
// pm=indigo-700, etc.) were repeated inline 4× inside Hub.jsx (BigTile,
// MediumTile, PortalPill, WelcomeBackHero). Editing a portal accent
// required 4 synchronized edits and silently invited drift.
//
// This file is paired with /app/frontend/src/styles/tokens.css and
// /app/frontend/src/styles/portal-system.css. The Tailwind classes
// here MUST stay numerically identical to the CSS variables in
// portal-system.css — both are intentionally redundant so:
//   • JSX consumers can keep using Tailwind utility classes (faster
//     to scan, no inline style attribute pollution).
//   • CSS-only consumers (PDF chrome, portal-system rules) can flip
//     a single CSS variable to retheme.
//
// ─── Schema per portal ──────────────────────────────────────────
// {
//   bg:      "bg-<color>-<shade>",      // solid fill (icon chip, bars)
//   bar:     "bg-<color>-<shade>",      // top accent bar (= bg today)
//   pill:    "<text & bg pair>",         // small kicker pill
//   cta:     "text-<color>-<shade>",    // CTA + arrow color
//   border:  "border-<color>-<shade>",  // tile border / focus
//   ring:    "hover:border-<color>-<shade>",
//   onColor: "text-<color>-50",         // text on a solid bg
//   softBg:  "bg-<color>-50",           // tonal background tint
//   btnInverse: "bg-white text-<color>-<shade> hover:bg-<color>-50",
//   // Optional hero slots — only set when the welcome-back inverse
//   // card uses a different shade than the tile (Shop is the only
//   // current example). When unset the consumer falls back to the
//   // tile bg/onColor/btnInverse.
//   heroBg:         (optional override),
//   heroOnColor:    (optional override),
//   heroBtnInverse: (optional override),
// }
//
// Add a portal by extending PORTAL_PALETTE — every Hub consumer
// picks it up automatically.

export const PORTAL_PALETTE = {
  admin: {
    bg:         "bg-slate-900",
    bar:        "bg-slate-900",
    pill:       "text-slate-700 bg-slate-100",
    cta:        "text-slate-800",
    border:     "border-slate-200",
    ring:       "hover:border-slate-400",
    onColor:    "text-slate-100",
    softBg:     "bg-slate-100",
    btnInverse: "bg-white text-slate-900 hover:bg-slate-100",
  },
  pm: {
    bg:         "bg-indigo-700",
    bar:        "bg-indigo-700",
    pill:       "text-indigo-700 bg-indigo-100",
    cta:        "text-indigo-700",
    border:     "border-indigo-200",
    ring:       "hover:border-indigo-700",
    onColor:    "text-indigo-50",
    softBg:     "bg-indigo-50",
    btnInverse: "bg-white text-indigo-700 hover:bg-indigo-50",
  },
  shop: {
    bg:         "bg-orange-600",
    bar:        "bg-orange-600",
    pill:       "text-orange-700 bg-orange-100",
    cta:        "text-orange-700",
    border:     "border-orange-200",
    ring:       "hover:border-orange-600",
    onColor:    "text-orange-50",
    softBg:     "bg-orange-50",
    btnInverse: "bg-white text-orange-700 hover:bg-orange-50",
    // Hero card historically shipped at orange-700 (a darker, more
    // dominant variant). Preserve for zero-visual-change.
    heroBg:         "bg-orange-700",
    heroBtnInverse: "bg-white text-orange-700 hover:bg-orange-50",
  },
  hr: {
    bg:         "bg-purple-700",
    bar:        "bg-purple-700",
    pill:       "text-purple-700 bg-purple-100",
    cta:        "text-purple-700",
    border:     "border-purple-200",
    ring:       "hover:border-purple-700",
    onColor:    "text-purple-50",
    softBg:     "bg-purple-50",
    btnInverse: "bg-white text-purple-700 hover:bg-purple-50",
  },
  safety: {
    bg:         "bg-cyan-700",
    bar:        "bg-cyan-700",
    pill:       "text-cyan-700 bg-cyan-100",
    cta:        "text-cyan-700",
    border:     "border-cyan-200",
    ring:       "hover:border-cyan-700",
    onColor:    "text-cyan-50",
    softBg:     "bg-cyan-50",
    btnInverse: "bg-white text-cyan-700 hover:bg-cyan-50",
  },
  dispatch: {
    // NOTE: portal-system.css uses amber-700 for the Dispatch portal,
    // but the Hub landing tile shipped with orange-600 from day one.
    // To preserve the existing Hub visual we keep orange here. The
    // amber variant is exposed below as `dispatchAmber` for callers
    // that explicitly want the portal-system color.
    bg:         "bg-orange-600",
    bar:        "bg-orange-600",
    pill:       "text-orange-700 bg-orange-100",
    cta:        "text-orange-700",
    border:     "border-orange-200",
    ring:       "hover:border-orange-600",
    onColor:    "text-orange-50",
    softBg:     "bg-orange-50",
    btnInverse: "bg-white text-orange-700 hover:bg-orange-50",
  },
  dispatchAmber: {
    bg:         "bg-amber-600",
    bar:        "bg-amber-600",
    pill:       "text-amber-700 bg-amber-100",
    cta:        "text-amber-700",
    border:     "border-amber-200",
    ring:       "hover:border-amber-600",
    onColor:    "text-amber-50",
    softBg:     "bg-amber-50",
    btnInverse: "bg-white text-amber-700 hover:bg-amber-50",
  },
  training: {
    bg:         "bg-indigo-700",
    bar:        "bg-indigo-700",
    pill:       "text-indigo-700 bg-indigo-100",
    cta:        "text-indigo-700",
    border:     "border-indigo-200",
    ring:       "hover:border-indigo-700",
    onColor:    "text-indigo-50",
    softBg:     "bg-indigo-50",
    btnInverse: "bg-white text-indigo-700 hover:bg-indigo-50",
  },
  leadership: {
    bg:         "bg-slate-700",
    bar:        "bg-slate-700",
    pill:       "text-slate-700 bg-slate-100",
    cta:        "text-slate-800",
    border:     "border-slate-200",
    ring:       "hover:border-slate-400",
    onColor:    "text-slate-100",
    softBg:     "bg-slate-100",
    btnInverse: "bg-white text-slate-900 hover:bg-slate-100",
  },
};

// Fallback used when an unknown portal kind is passed.
const FALLBACK = PORTAL_PALETTE.admin;

/**
 * Resolve a portal kind (`"admin"`, `"hr"`, etc.) to its palette.
 * Unknown kinds fall back to admin so callers never crash.
 */
export function paletteFor(kind) {
  return PORTAL_PALETTE[kind] || FALLBACK;
}

/**
 * paletteFor(kind) with hero-variant fallback: hero* slots take
 * precedence on the inverse-color WelcomeBackHero; tile callers
 * keep using bg/onColor/btnInverse directly.
 */
export function heroPaletteFor(kind) {
  const p = paletteFor(kind);
  return {
    bg:         p.heroBg         || p.bg,
    onColor:    p.heroOnColor    || p.onColor,
    btnInverse: p.heroBtnInverse || p.btnInverse,
  };
}

/**
 * Pick a single slot off a palette in one call:
 *   paletteSlot("hr", "bg")          // → "bg-purple-700"
 */
export function paletteSlot(kind, slot) {
  return paletteFor(kind)[slot];
}

/**
 * SectionTile.jsx exposes an accent prop with non-portal-specific
 * names ("red", "cyan", "indigo", etc.). When a Hub wants a Tile in
 * the same color as a portal, this helper maps portal-kind → the
 * matching SectionTile accent key, keeping the visual contract stable.
 */
export const PORTAL_TO_TILE_ACCENT = {
  admin:      "slate",
  pm:         "indigo",
  shop:       "orange",
  hr:         "purple",
  safety:     "cyan",
  dispatch:   "amber",
  training:   "indigo",
  leadership: "slate",
};

export function tileAccentFor(kind) {
  return PORTAL_TO_TILE_ACCENT[kind] || "slate";
}
