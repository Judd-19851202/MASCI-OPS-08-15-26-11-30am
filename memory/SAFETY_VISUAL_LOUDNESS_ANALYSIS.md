# Safety Visual Loudness Analysis

*Phase IV-BETA.4C · iter437 · 2026-02-27*
*Status: 🟢 ANALYSIS COMPLETE · IMPLEMENTATION NOT STARTED*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Method

Manual measurement using the Visual Loudness Reduction Plan §I
6-dimension rubric + grep counts of `bg-*` colour applications across
all 25 Safety pages.

## II. Raw loudness counts (🟢 VERIFIED · grep audit)

| Dimension | Safety pages today | Doctrine target | Verdict |
|---|---|---|---|
| Distinct hue families | **9** (amber, blue, cyan, emerald, indigo, purple, red, sky, violet) | ≤4 | 🔴 OVER |
| Total `bg-*` colour hits | **144** across 25 pages (avg 5.8/page) | ≤3/page | 🔴 OVER |
| Red occurrences | **42** (red-100 ×13, red-700 ×13, red-800 ×7, red-600 ×5, red-200 ×2, red-900 ×2) | Reserved for severe | 🔴 OVER |
| Cyan occurrences (brand) | **49** (cyan-700 ×29, cyan-800 ×20) | brand chrome stripe + 1 button accent | 🟡 borderline |
| Forbidden urgency words | **0** | 0 | 🟢 |
| Ambient animation | 0 (none detected) | 0 | 🟢 |

## III. True signal vs false loudness

The directive: "make true danger unmistakable." The current Safety
palette **dilutes** danger signalling because red is reused across:

- Severity badges (correct use)
- Hub tile stripes (low signal — pure decoration)
- CTA buttons (correct use sometimes; decoration other times)
- Empty-state messages (false loudness)
- "Read-only" indicators (false loudness — operator already knows
  it's read-only)

If everything is red, the eye stops elevating real red. The
implementation pass (when authorised) must:

1. **Reserve red** for severity pills + severe-tier alerts + immediate
   action CTAs ONLY.
2. **Move tile stripes** to the 4-domain doctrine palette
   (e.g., cyan for safety brand · violet for compliance · slate for
   guidance · red ONLY for "incidents / escalation" domain).
3. **Replace per-tile button colours** with a single neutral
   slate-800 (same pattern as HR P1B trim).

## IV. Specific hotspots (🟢 spot-checked)

| Hotspot | File | Treatment plan |
|---|---|---|
| Hub tile palette explosion | `SafetyHub.jsx` | Consolidate 9 hues → 4 (see §III above) |
| Cyan-700 button overuse (29 hits) | multiple | Neutralise to slate-800; keep cyan-700 stripe only |
| Red-700/800 button overuse (20 hits) | multiple | Reserve for severe-tier CTAs only |
| `bg-red-100`/`bg-red-200` empty-state panels | `SafetyIncidents.jsx` and others | Replace with slate-100 + a leading icon (eye-cue, not panic-cue) |
| Hub tile sublines (untrimmed) | `SafetyHub.jsx` | Trim to ≤14 words sentence case per doctrine §V |

## V. Predicted post-implementation loudness (⚪ UNTESTED · projection)

If the pass implements §III + §IV at the same discipline as HR P1B:

| Metric | Pre-trim (today) | Post-trim (target) |
|---|---|---|
| Distinct hue families | 9 | 4 |
| Red occurrences | 42 | ≤10 (severity badges + severe CTAs only) |
| Per-page `bg-*` hits | 5.8 | 3.0 |
| Loudness composite (DOM-style) | ⚪ not yet baselined | ≤55 |

## VI. Doctrine reaffirmed

- ✅ Analysis only · NO Safety code changes this iteration
- ✅ True danger must remain unmistakable (do NOT desaturate severity
  badges; do NOT mute severe-tier prefixes)
- ✅ False urgency must disappear (decorative red, tile-stripe red,
  empty-state red)
- ✅ Preview only
