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
//   // Hub-header surface slots (iter144). The sub-hub pages each
//   // ship a dark header bar with a thick colored bottom border, a
//   // kicker pill, and white nav links that lighten on hover. These
//   // historically used per-portal Tailwind literals — now centralized.
//   // hubHeaderBar:  border-b-4 color used under the dark header
//   // hubKicker:     text color for the small "PORTAL · …" kicker
//   // hubLinkHover:  text-color used by `hover:text-…` on nav links
//   hubHeaderBar:   (e.g., "border-purple-700"),
//   hubKicker:      (e.g., "text-purple-700"),
//   hubKickerStatic:(e.g., "text-purple-300"),
//   hubLinkHover:   (e.g., "hover:text-purple-300"),
// }
//
// Add a portal by extending PORTAL_PALETTE — every Hub consumer
// picks it up automatically.
//
// ─── Known drifts (iter144, documented for future reconciliation) ─
// * PmHub tile-CTA uses amber-600 hover + amber-700 text while the
//   canonical PM palette is indigo. PmHub TILES array is per-tile,
//   not portal-keyed, so it's left literal.
// * FieldLeadershipHub uses red-700 — this matches the brand red and
//   the leadership portal is intentionally brand-colored. No drift.

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
    hubHeaderBar:  "border-slate-700",
    hubKicker:     "text-slate-700",
    hubKickerStatic: "text-slate-300",
    hubLinkHover:  "hover:text-slate-300",
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
    hubHeaderBar:  "border-indigo-700",
    hubKicker:     "text-indigo-700",
    hubKickerStatic: "text-indigo-300",
    hubLinkHover:  "hover:text-indigo-300",
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
    hubHeaderBar:  "border-orange-600",
    hubKicker:     "text-orange-700",
    hubKickerStatic: "text-orange-300",
    hubLinkHover:  "hover:text-orange-300",
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
    hubHeaderBar:  "border-purple-700",
    hubKicker:     "text-purple-700",
    hubKickerStatic: "text-purple-300",
    hubLinkHover:  "hover:text-purple-300",
  },
  safety: {
    bg:         "bg-rose-700",
    bar:        "bg-rose-700",
    pill:       "text-rose-700 bg-rose-100",
    cta:        "text-rose-700",
    border:     "border-rose-200",
    ring:       "hover:border-rose-700",
    onColor:    "text-rose-50",
    softBg:     "bg-rose-50",
    btnInverse: "bg-white text-rose-700 hover:bg-rose-50",
    hubHeaderBar:  "border-rose-700",
    hubKicker:     "text-rose-700",
    hubKickerStatic: "text-rose-300",
    hubLinkHover:  "hover:text-rose-300",
  },
  dispatch: {
    bg:         "bg-sky-700",
    bar:        "bg-sky-700",
    pill:       "text-sky-700 bg-sky-100",
    cta:        "text-sky-700",
    border:     "border-sky-200",
    ring:       "hover:border-sky-700",
    onColor:    "text-sky-50",
    softBg:     "bg-sky-50",
    btnInverse: "bg-white text-sky-700 hover:bg-sky-50",
    hubHeaderBar:  "border-sky-700",
    hubKicker:     "text-sky-700",
    hubKickerStatic: "text-sky-300",
    hubLinkHover:  "hover:text-sky-300",
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
    hubHeaderBar:  "border-indigo-700",
    hubKicker:     "text-indigo-700",
    hubKickerStatic: "text-indigo-300",
    hubLinkHover:  "hover:text-indigo-300",
  },
  leadership: {
    bg:         "bg-stone-700",
    bar:        "bg-stone-700",
    pill:       "text-stone-700 bg-stone-100",
    cta:        "text-stone-800",
    border:     "border-stone-200",
    ring:       "hover:border-stone-500",
    onColor:    "text-stone-100",
    softBg:     "bg-stone-100",
    btnInverse: "bg-white text-stone-800 hover:bg-stone-100",
    hubHeaderBar:  "border-stone-700",
    hubKicker:     "text-stone-700",
    hubKickerStatic: "text-stone-300",
    hubLinkHover:  "hover:text-stone-300",
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
  admin:      "admin",
  pm:         "pm",
  shop:       "shop",
  hr:         "hr",
  safety:     "safety",
  dispatch:   "dispatch",
  training:   "training",
  leadership: "leadership",
};

export function tileAccentFor(kind) {
  return PORTAL_TO_TILE_ACCENT[kind] || "slate";
}
