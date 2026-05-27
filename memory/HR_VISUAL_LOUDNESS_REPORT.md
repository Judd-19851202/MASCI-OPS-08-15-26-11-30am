# HR Visual Loudness Report

*Phase IV-BETA.3B · iter437 · 2026-02-27*
*Status: 🟡 BASELINE CAPTURED · V2 SIDEBAR ALREADY CALMER · HUB-TILE TRIM DEFERRED to P1*

---

## I. Method

Manual measurement using `VISUAL_LOUDNESS_REDUCTION_PLAN.md` §I 6-dimension
rubric, plus a `measure_visual_loudness.py` smoke run when the flag is
on. No code changes were made to the HR Hub palette this iteration —
this report establishes the baseline against which P1 hub trim will be
evaluated.

## II. Loudness scoring · HR Hub (`/hr`)

| Dimension | Today's score | Target | Verdict |
|---|---|---|---|
| 1. Red/amber saturation coverage | 12% (header stripe + 4 per-tile button accents above fold) | ≤15% | 🟢 OK |
| 2. Distinct color hue families | **9** (emerald, amber, rose, indigo, blue, purple, cyan, red, slate) | ≤4 | 🔴 OVER (P1 trim target) |
| 3. Above-fold clickable count | ~14 (15 tiles, 1 off-fold) | ≤12 | 🟡 borderline |
| 4. Notification markers | 0 (no badge pills currently) | — | 🟢 |
| 5. Typography combinations | 4 (display headline · body · monospace eyebrow · CTA) | ≤4 | 🟢 |
| 6. Ambient motion | 0 (no auto-animations on hub) | 0 | 🟢 |

**Loudness verdict for HR Hub today: 🟡 BORDERLINE** — driven entirely
by the 9-hue tile-stripe palette.

## III. Loudness scoring · HR Sidebar V2 (`/hr/*?hrSidebarV2=1`)

| Dimension | Today's score | Target | Verdict |
|---|---|---|---|
| 1. Red/amber saturation coverage | <3% (only the active-route stripe carries colour) | ≤15% | 🟢 |
| 2. Distinct color hue families | **5** (green · sky · violet · amber · slate — one per domain) | ≤4 | 🟡 (acceptable for a 5-domain map; doctrine accepts up to N+1 where N=4) |
| 3. Above-fold clickable count (sidebar only) | 18 entries | — | 🟢 (sidebar is a list, not a tile-grid; not subject to the same ceiling) |
| 4. Notification markers | 0 | — | 🟢 |
| 5. Typography combinations | 2 (uppercase mono label + sentence-case subline) | ≤4 | 🟢 |
| 6. Ambient motion | 0 | 0 | 🟢 |

**Loudness verdict for HR Sidebar V2: 🟢 CALM** — the V2 sidebar is
already operationally calmer than the legacy hub.

## IV. Comparative posture

| Surface | Hue count | Above-fold clicks | Verdict |
|---|---|---|---|
| Admin Hub V2 (current) | 4 | 12 | 🟢 |
| PM Hub V2 (current) | 4 | 11 | 🟢 |
| **HR Hub (today)** | **9** | **~14** | 🔴 |
| HR Sidebar V2 (today) | 5 | 18 (list, not tiles) | 🟢 |

The HR Hub remains the single loudness outlier on the platform.

## V. Recommended P1 trim plan (⚪ UNTESTED · NOT this iteration)

To bring HR Hub into doctrine compliance:

1. **Consolidate tile stripes** from 9 to 4 hues, mapping the existing
   15 tiles onto the 5 V2 sidebar domains (already designed in
   `HR_INFORMATION_PRIORITY_MAP.json`):
   - People Operations → `border-l-green-600`
   - Time & Payroll → `border-l-sky-600`
   - Compliance & Records → `border-l-violet-600`
   - Access & Identity → `border-l-amber-700`
   - Guidance → `border-l-slate-600`
2. **Replace per-tile button colours** with a single neutral (slate-800)
   button across all tiles. Identity carried by the stripe, not the
   CTA. Mirrors Admin Hub V2 and PM Hub V2.
3. **Trim tile sublines** to ≤14 words sentence case per the coaching
   doctrine. Most tiles today are 18-27 words.

Each step ships as a separate PR with regression coverage and a
loudness re-measurement.

## VI. Loudness measurement automation

When `pre_deploy_check.sh` is run with `MODE=full` (default), the new
warning-only stage `Governance · visual loudness trend` invokes
`measure_visual_loudness.py` against `/admin /pm /pm/jobs`. Extending
this to include `/hr` and `/hr/?hrSidebarV2=1` is a one-line change
in `stage_governance_visual_loudness()` once we want HR loudness
trend-tracked formally.

## VII. Doctrine reaffirmed

- ✅ NO HR Hub redesign this iteration — only V2 sidebar shipped
- ✅ Baseline captured so future trim is measurable
- ✅ Loudness measurement is warning-only — never blocks deploy
- ✅ Preview only
