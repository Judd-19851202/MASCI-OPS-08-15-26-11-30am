# Visual Consistency Audit — Phase IV-BETA

**Iteration:** iter437 · Phase IV-BETA · 2026-02
**Status:** 🟢 BASELINE MEASURED · CROSS-PORTAL DRIFT CATALOGED
**Grounded in:** Direct inspection of `AdminShell.jsx`, `PmShell.jsx`, `PmHub.jsx`, `PmSections.jsx` (this session) + `PM_PORTAL_CURRENT_STATE_AUDIT.md`
**Companion docs:** `VISUAL_LOUDNESS_REDUCTION_PLAN.md` · `COMPONENT_HIERARCHY_STANDARD.md`

This document captures the visual drift between portals as it exists today — pre-IV-BETA implementation. Every observation is sourced from inspected files. Reduction targets are measurable.

The intent is not aesthetic critique. The intent is **operator trust**: portal-to-portal visual drift forces operators to re-orient, which degrades decision quality.

---

## I. Cross-portal drift matrix

Direct comparison of the two portals inspected this session against the locked Phase IV-A doctrine.

### Sidebar active-state treatment

| Portal | Current treatment | Doctrine | Status |
|---|---|---|---|
| Admin legacy | `bg-red-700 text-white shadow-sm` | 2-px stripe + `bg-slate-800` | ❌ violation (legacy; V2 fixes) |
| Admin V2 (flag-on) | 2-px stripe + `bg-slate-800` | Aligned | ✅ |
| PM legacy | `bg-amber-600 text-white shadow-sm` | 2-px stripe + `bg-slate-800` | ❌ violation (PM V2 will fix) |

**Implication:** Both portals shipped with saturated full-color active states. Admin V2 has corrected this; PM must follow in IV-BETA.1.

### Header bottom-border treatment

| Portal | Current treatment | Doctrine | Status |
|---|---|---|---|
| Admin | `border-b-4 border-red-700` (4 px saturated) | 1 px slate-800 | ❌ violation |
| PM | `border-b-4 border-amber-600` (4 px saturated) | 1 px slate-800 | ❌ violation |

**Implication:** Both portals use 4-px saturated chrome — visually loud per `VISUAL_LOUDNESS_REDUCTION_PLAN.md` §III.3.

### Breadcrumb color treatment

| Portal | Current treatment | Doctrine | Status |
|---|---|---|---|
| Admin | `text-red-300` (saturated breadcrumb) | `text-slate-300` (calm neutral) | ❌ violation |
| PM | `text-amber-300` (saturated breadcrumb) | `text-slate-300` (calm neutral) | ❌ violation |

### Mobile drawer iOS scroll fix

| Portal | Current treatment | Doctrine | Status |
|---|---|---|---|
| Admin | Canonical scroll pattern applied (Phase IV-A.0) | Applied | ✅ |
| PM | `<SheetContent>` with no scroll wrapper, no flex-col, no `WebkitOverflowScrolling` | Applied | 🔴 P0 violation |

**Implication:** The iPhone Safari drawer scroll bug fixed in Admin still exists in PM. Replicates with any sidebar children > 9 (which IV-BETA.1 will introduce).

### Sidebar entry visual weight

| Portal | Entry count | Hierarchy tiers | Doctrine | Status |
|---|---|---|---|---|
| Admin legacy | 29 entries, flat | 1 tier (all equal) | Tier 1 domains + Tier 2 children | ❌ violation |
| Admin V2 | 6 domains + ~30 children (collapsed) | 2 tiers | 2-tier ladder | ✅ |
| PM legacy | 9 entries, flat | 1 tier (all equal) | 2-tier ladder | ❌ violation |

### Hub overview tile count

| Portal | Tile count above fold | Doctrine target | Status |
|---|---|---|---|
| Admin | 38 cards on initial render (per Phase IV-A audit) | ≤ 12 above fold | ❌ violation |
| PM | 15 tiles in 3-column grid + 6 stacked widgets above | ≤ 12 above fold | ❌ violation |

### Color hue count per surface (sidebar)

| Portal | Hue families | Doctrine target | Status |
|---|---|---|---|
| Admin sidebar | 5 (red, blue, amber, green, gray) | ≤ 3 | ❌ violation |
| PM sidebar | 2 (amber, slate) | ≤ 3 | ✅ |

### Color hue count per surface (Hub)

| Portal | Hue families | Doctrine target | Status |
|---|---|---|---|
| Admin landing | 4 hues | ≤ 3 | 🟡 |
| PM Hub | 7 hues (red, amber, redDeep, rose, indigo, emerald, slate) | ≤ 3 | ❌ violation |

### Hub badge / marker density

| Portal | Markers visible | Doctrine target | Status |
|---|---|---|---|
| Admin landing | 9 | ≤ 6 | ❌ violation |
| PM Hub | 8 (4 KPI tiles + 1 "Read-only · 180d scope" badge + 3 hue-coded icon blocks) | ≤ 6 | 🟡 close |

### Saturation surface coverage (sidebar)

| Portal | Approximate red/amber saturated area | Doctrine target | Status |
|---|---|---|---|
| Admin legacy sidebar | ~22% (red active state) | ≤ 4% | ❌ |
| Admin V2 sidebar | ~3% (2-px stripes only) | ≤ 4% | ✅ |
| PM legacy sidebar | ~18% (amber active state) | ≤ 4% | ❌ |

---

## II. Typography drift

| Surface | Admin | PM | Drift |
|---|---|---|---|
| Page H1 | `text-base sm:text-lg font-black` in chrome | `text-base sm:text-lg font-black` in chrome | ✅ aligned (both use `font-black` weight which is heavier than doctrine `font-semibold`) |
| Sidebar entry label | `text-sm font-bold` | `text-sm font-bold` | ✅ aligned (both use `font-bold` which is heavier than doctrine `font-medium`) |
| Sidebar entry subline | `text-[10px] uppercase tracking-wider font-mono opacity-70` | `text-[10px] uppercase tracking-wider font-mono opacity-70` | ❌ aligned but in violation — doctrine sublines are sentence-case slate-500 |
| Hub tile title | `text-base sm:text-lg font-black` | `text-base sm:text-lg font-black` | ✅ aligned, same weight inflation |
| Hub tile metric | `text-2xl font-black` | `text-2xl font-black` | ✅ aligned |

**Implication:** Both portals use heavier weights than doctrine prescribes (`font-bold`/`font-black` vs doctrine `font-medium`/`font-semibold`). This is a Phase IV-BETA.4 normalization target across both portals simultaneously.

---

## III. Spacing drift

Per `MOBILE_NAVIGATION_STANDARD.md` §VIII, mobile spacing is 75% of desktop in the same context.

| Surface | Admin | PM | Drift |
|---|---|---|---|
| Sidebar entry padding | `px-3 py-2.5` | `px-3 py-2.5` | ✅ aligned |
| Header padding | `px-3 sm:px-5 py-3` | `px-3 sm:px-5 py-3` | ✅ aligned |
| Tile grid gap | n/a (Admin landing is different shape) | `gap-3 sm:gap-4` | n/a |
| Inline section spacing | Variable | `mt-5` between most sections | 🟡 PM is consistent but the rhythm violates ≤ 16 px between Tier-4 siblings |

---

## IV. Loudness sources cataloged across both portals

Aggregating from `PM_PORTAL_CURRENT_STATE_AUDIT.md` §4 and `VISUAL_LOUDNESS_REDUCTION_PLAN.md` §II:

### High-impact (Phase IV-BETA.1 / IV-BETA.4 priority)

1. **Saturated chrome borders** (4-px portal accent in both portal headers)
2. **Saturated active-state backgrounds** (red-700 / amber-600 on the active nav row)
3. **Saturated breadcrumb text** (red-300 / amber-300)
4. **Flat sidebar with no hierarchy** (PM only · Admin V2 fixes for Admin)
5. **iOS Safari drawer scroll bug** (PM only · Admin already fixed)
6. **Hub tile color hue explosion** (PM has 7 hues; Admin landing has 4)

### Medium-impact (Phase IV-BETA.2 priority)

7. **Inline widget stack on PM Hub** (6+ widgets above the tile grid)
8. **15-tile grid on PM Hub** (above doctrine target)
9. **PM Crew Compliance card 2-px saturated border** (border-amber-600)
10. **"Welcome to the PM Portal" intro card** (marketing tone)
11. **Sidebar sublines as uppercase mono feature-lists** (both portals)
12. **Heavy font weights across both portals** (`font-bold`/`font-black`)

### Low-impact (Phase IV-BETA.3 / IV-BETA.5 priority)

13. **Inconsistent middle-dot vs bullet separators** in PM tile sublines
14. **PM Field Memory Glance position** (Tier 5 surface positioned above Tier 1 widgets)
15. **Hover shadow on PM tiles** (`hover:shadow-md` exceeds doctrine `shadow-sm` max)

---

## V. Reduction scorecard

Each row is one measurable reduction target. Numbers are pre-Phase-IV-BETA baselines.

| Dimension | Admin baseline | PM baseline | Target (both portals) |
|---|---|---|---|
| Saturated chrome surface % | 22% (legacy) / 3% (V2) | 18% | ≤ 4% |
| Hue families per surface (sidebar) | 5 (legacy) / 3 (V2) | 2 | ≤ 3 |
| Hue families per surface (overview) | 4 | 7 | ≤ 3 |
| Sidebar entries visible above fold | 29 (legacy) / 14 (V2) | 9 | ≤ 14 |
| Hub tiles above fold | 38 (legacy) | 15 + 6 widgets | ≤ 12 |
| Notification markers visible | 9 | 8 | ≤ 6 |
| Typography combinations per surface | 7–9 | 5–6 | ≤ 4 |
| Ambient motion elements | 3 (legacy) / 0 (V2) | 1 (Loader2 during load only) | ≤ 1 ambient |
| Modal occurrences per flow | 2+ | unmeasured (likely 1) | ≤ 1 |
| Border-color variants | 5+ (legacy) / 2 (V2) | 4 | 2 (slate + state) |

---

## VI. Cross-portal alignment after Phase IV-BETA (target end-state)

By the end of Phase IV-BETA (after IV-BETA.5), the following must be true:

- ✅ Admin V2 sidebar = default (legacy retired)
- ✅ PM V2 sidebar = default (legacy retired)
- ✅ Both portals' Hub overviews ≤ 12 surfaces above the fold
- ✅ Both portals use the iOS-fixed `<SheetContent>`
- ✅ Both portals' active-state = 2-px stripe + slate-800 (no saturated backgrounds)
- ✅ Both portals' chrome borders = 1 px slate-800 (no saturated portal-accent borders)
- ✅ Both portals' breadcrumb text = slate-300 (no saturated portal-accent text)
- ✅ Both portals' coaching sublines = sentence-case slate-500 (no uppercase mono feature-lists)
- ✅ Both portals' typography uses doctrine weights (`font-medium`/`font-semibold` defaults · `font-bold` only for emphasis within paragraphs)
- ✅ Both portals' Hub uses ≤ 3 hue families
- ✅ Both portals' overall loudness score (per Phase IV.A.4 measurement script) trends down monotonically across IV-BETA iterations

---

## VII. Cross-portal alignment for other 5 portals (HR · Dispatch · Safety · FL · Driver)

This audit covered Admin + PM in detail. The other 5 portals will be audited individually in their respective Phase IV-BETA sub-iterations:

| Portal | Audit + V2 sub-phase | Doctrine expected drift |
|---|---|---|
| HR | IV-BETA.2 | Purple/violet saturated chrome · likely follows PM pattern |
| Dispatch | IV-BETA.3 | Amber-coded chrome · 4–5 entry sidebar likely |
| Safety | IV-BETA.3 | Cyan-coded chrome · likely follows PM pattern |
| Field Leadership | IV-BETA.4 | Red-coded chrome · simpler nav, possibly bottom-nav for mobile |
| Driver | IV-BETA.4 | Slate-coded chrome · simplest portal · minimal nav |

Per `CROSS_PORTAL_CONSISTENCY_STANDARD.md` §II, each portal's domain stripe is preserved (HR blue, Dispatch amber, Safety orange, FL red, Driver slate) but the chrome saturation is eliminated identically to Admin and PM.

---

## VIII. The measurement gate (Phase IV-BETA.4)

The same `scripts/measure_visual_loudness.py` from Phase IV.A.4 extends to all portals. Snapshots are captured at 3 viewports × 7 portals × top-5 most-trafficked routes per portal = 105 snapshots per deploy.

The gate fails if:
- Any single surface's loudness score exceeds the portal-specific threshold.
- The portal-wide average regresses from the previous deploy.

The trendline is logged per-portal at `/app/memory/LOUDNESS_TRENDLINE.json`.

---

## IX. Operator-trust principles for cross-portal visual consistency

1. **The drawer looks the same everywhere.** Operator opens drawer in Admin or PM; muscle memory transfers.
2. **The active row looks the same everywhere.** Stripe + tint, never saturated background.
3. **The breadcrumb feels the same everywhere.** Slate text, no portal-specific tint.
4. **The Hub overview is calm everywhere.** ≤ 12 surfaces above the fold, ≤ 3 hue families.
5. **A surface's importance is visible everywhere.** Tier ladder + severity color drive the eye.

---

## Verdict

🟢 **VISUAL CONSISTENCY AUDIT COMPLETE.** Drift between Admin and PM is cataloged and measurable. Reduction targets are bound to phased sub-iterations. The cross-portal end-state is defined.

Implementation begins in IV-BETA.1 (PM Sidebar V2 + iOS scroll fix + Playwright regression).
