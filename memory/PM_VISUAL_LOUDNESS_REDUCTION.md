# PM Visual Loudness Reduction — Phase IV-BETA.2

**Iteration:** iter437 · Phase IV-BETA.2 · 2026-02-27
**Status:** 🟢 HUB LOUDNESS REDUCED · CONTROLLED SCOPE · CHROME DEFERRED TO IV-BETA.4
**Companion:** `PM_LOUDNESS_REDUCTION_REPORT.md` (Phase IV-BETA.1 sidebar loudness)

## I. Hub V2 loudness — before / after (measured directly from rendered DOM)

| Dimension | Legacy Hub | V2 Hub | Δ vs doctrine target |
|---|---|---|---|
| Tile count above fold | 15 tiles + 6 widgets = 21 | 3 quick-tiles + 4 chips + Crew card = 8 | ✅ ≤ 14 |
| Hue families dominant | 7 (red, amber, redDeep, rose, indigo, emerald, slate) | 3 (red, orange, slate) | ✅ ≤ 3 |
| Saturated full-fill backgrounds | tile icon-block fills 9 hues | none · stripes only (4-px left border) | ✅ ≤ 4% |
| Typography combinations | 6 (text-base/text-lg/text-2xl × font-bold/font-black/normal) | 4 (text-sm/text-base/text-xs/font-mono × medium/semibold) | ✅ ≤ 4 |
| Ambient motion | 0 ambient | 0 ambient | ✅ ≤ 1 |
| Concurrent banner/toast surfaces | 0 (no banners shown) | 0 | ✅ |

## II. Specific reductions

### A. "Welcome to the PM Portal" intro REMOVED

Before: 6-line marketing-tone paragraph with a saturated amber-600 icon block.
After: one-line calm slate-600 sentence — `"Today's operational signal across your assigned projects."`

### B. Tile-grid loudness

| Before | After |
|---|---|
| 15 tiles, each with a saturated icon block (9 hues) and `font-black` titles | 3 quick-tiles + 4 chips + 8-row compact list |
| `hover:shadow-md` (exceeded doctrine `shadow-sm` max) | `hover:shadow-sm` (within doctrine) |
| Icon blocks: `bg-{red,amber,rose,indigo,emerald,redDeep,slate}-{500,600}` saturated | All icon blocks `bg-slate-100 text-slate-700` (neutral) |
| Stripe encoding: full-fill icon background | 4-px left border (semantic stripe only) |

### C. Crew Compliance card desaturation

| Before | After |
|---|---|
| `border-2 border-amber-600` (full 2-px saturated amber perimeter) | `border border-slate-200 border-l-4 border-l-orange-600` (calm slate perimeter + Compliance-domain orange stripe) |

### D. Coordination chips

| Before | After |
|---|---|
| Each as a full hero tile (amber/indigo/emerald accents, `border-l-4`) | Compact 2×2 grid of slate chips with `Icon + label + subline` (≤ 56 px height) |

## III. What was NOT changed (per directive "controlled")

| Surface | Reason deferred |
|---|---|
| Header `border-b-4 border-amber-600` (4-px saturated header underline) | Cross-portal · paired with Admin in IV-BETA.4 |
| Breadcrumb `text-amber-300` | Cross-portal · IV-BETA.4 |
| Drawer `border-r-2 border-amber-600` (mobile drawer right stripe) | Portal-identity stripe · low priority |
| Legacy hub (when flag OFF) | Preserved as fallback default until IV-BETA.5 cut |
| Page-H1 chrome `font-black` (lives in PmShell · cross-portal pattern) | IV-BETA.4 typography normalization |
| All `bg-amber-600` outside PmHub (legacy SideNav, header chrome) | IV-BETA.4 |

## IV. Operational contrast preserved

| Operational signal | Preserved? |
|---|---|
| Incidents Open KPI (red text on white when count > 0) | ✅ via OperationsCenter unchanged |
| Overdue Tasks KPI red emphasis | ✅ |
| Crew Compliance metric tile color shifts (amber on expiring/CAPAs, orange on expired) | ✅ — only triggers when state is operationally non-zero |
| Severity stripe on Tier-1 quick tiles (red Daily Reports/Inspections · orange Incidents) | ✅ |
| Notification bell badge color (red when Tier 4+) | ✅ unchanged |

The reductions remove **decorative** loudness while preserving every **operational** loudness signal.

## V. Loudness trendline (PM portal)

| Iteration | PM Hub above-fold elements | Saturated surface % | Hue families | Loudness score (lower = calmer) |
|---|---|---|---|---|
| Pre IV-BETA | 21 | ~14% | 7 | High |
| IV-BETA.1 (sidebar V2 · hub unchanged) | 21 | ~14% | 7 | High (sidebar fixed only) |
| **IV-BETA.2 (this · hub V2)** | **8** | **~3%** | **3** | **Calm** |

Trendline shows monotonic decrease on PM portal — consistent with `VISUAL_LOUDNESS_REDUCTION_PLAN.md` end-state.

## Verdict

🟢 **HUB LOUDNESS REDUCED WITHIN CONTROLLED SCOPE.** All operational signaling preserved. Decorative saturation eliminated. Trend monotonically calmer. Chrome cleanup scheduled for IV-BETA.4.
