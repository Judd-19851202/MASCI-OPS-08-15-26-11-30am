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
//   hubLinkHover:   (e.g., "hover:text-purple-300"),
// }
//
// Add a portal by extending PORTAL_PALETTE — every Hub consumer
// picks it up automatically.
//
// ─── Known drifts (iter144, documented for future reconciliation) ─
// * ShopHub header uses amber-500 / amber-700 / amber-300 (preserved
//   in hub*) while the canonical Shop tile palette is orange-600/700.
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
    hubHeaderBar:  "border-red-700",
    hubKicker:     "text-red-700",
    hubLinkHover:  "hover:text-red-300",
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
    // ShopHub header shipped with amber accents — see drift note.
    hubHeaderBar:  "border-amber-500",
    hubKicker:     "text-amber-700",
    hubLinkHover:  "hover:text-amber-300",
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
    hubLinkHover:  "hover:text-purple-300",
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
    hubHeaderBar:  "border-cyan-700",
    hubKicker:     "text-cyan-700",
    hubLinkHover:  "hover:text-cyan-300",
  },
  dispatch: {
    // iter144 — Reconciled to amber-700 family. Previously the Hub
    // tile shipped at orange-600 while portal-system.css and the
    // DispatchShell used amber-700; that drift is now eliminated.
    // The Hub Dispatch tile shifts from orange-600 → amber-600 as
    // a deliberate consistency fix per Phase 1 SOT mandate.
    bg:         "bg-amber-600",
    bar:        "bg-amber-600",
    pill:       "text-amber-700 bg-amber-100",
    cta:        "text-amber-700",
    border:     "border-amber-200",
    ring:       "hover:border-amber-600",
    onColor:    "text-amber-50",
    softBg:     "bg-amber-50",
    btnInverse: "bg-white text-amber-700 hover:bg-amber-50",
    // DispatchHub header historically shipped at orange-600 — drift
    // documented in the file header.
    hubHeaderBar:  "border-orange-600",
    hubKicker:     "text-orange-700",
    hubLinkHover:  "hover:text-orange-300",
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
    hubLinkHover:  "hover:text-indigo-300",
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
    // FieldLeadershipHub intentionally uses brand red (matches the
    // admin / brand red — leadership is a brand-aligned surface).
    hubHeaderBar:  "border-red-700",
    hubKicker:     "text-red-700",
    hubLinkHover:  "hover:text-red-300",
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
