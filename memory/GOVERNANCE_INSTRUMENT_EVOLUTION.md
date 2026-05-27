# Governance Instrument Evolution

*Phase IV-BETA.3-P2C · iter437 · 2026-02-27*
*Status: 🟢 5 new dimensions instrumented · WARNING-ONLY (per directive)*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. What was instrumented this iteration

The Visual Doctrine Baseline System (P2A) ships with **7 metrics** per
hub × viewport cell. Five of those map directly onto the new
dimensions the operator directive called out:

| Directive dimension | Implemented as | Source |
|---|---|---|
| Bold-density scoring | `typography_summary` (count per weight bucket) + `emphasis_score` (sequential bold runs) | `test_visual_doctrine_baseline.py` |
| Badge-saturation scoring | `badge_density` (badges per 100 visible elements) | same |
| Hierarchy-weight scoring | `hierarchy_hash` + `font_size_summary` | same |
| Coaching consistency scoring | `verify_coaching_sublines.py` ≤14-word gate + 6 escalation-wording bans | `scripts/verify_coaching_sublines.py` |
| Escalation consistency scoring | `verify_admin_copy.py` already flags forbidden urgency phrasing across all of `frontend/src/` | `scripts/verify_admin_copy.py` |

## II. Why this lives in the baseline test (not in `measure_visual_loudness.py`)

The original `measure_visual_loudness.py` script captures a single
**screenshot-driven** loudness score. The new instrument is
**DOM-style driven**, deterministic, and per-element. It complements
the screenshot pass — both run in the deploy gate, both warning-only,
neither blocking.

We chose this split because:
1. DOM-style hashing is fast and deterministic (no PNG diff noise).
2. Screenshot-based loudness still adds value for trend rendering.
3. Splitting prevents one slow script from gating the deploy.

## III. Cross-instrument coverage matrix

| Doctrine concern | Captured by | Warning trigger today | Block-deploy plan |
|---|---|---|---|
| Banned phrasing in coaching sublines | `verify_coaching_sublines.py` | Any match | After 2 zero-violation iterations |
| Banned phrasing anywhere in frontend | `verify_admin_copy.py` | Any match | After ~29 current false-positive count is verified down |
| Loudness composite per hub | `measure_visual_loudness.py` | Always reports | After 3 iterations of trend data |
| Hue family count per hub | baseline test `hue_family_count` | Always reports | Block if jumps >2 between iterations |
| Badge density per hub | baseline test `badge_density` | Always reports | Block if doubles between iterations |
| Emphasis score per hub | baseline test `emphasis_score` | Always reports | Block if rises >5 between iterations |
| Hierarchy hash per hub | baseline test `hierarchy_hash` | Always reports | Block if changes WITHOUT an entry in `HUB_VISUAL_BASELINE.json::_meta.intentional_changes` |
| DOM-style hash per hub | baseline test `dom_style_hash` | Always reports | Suspicious drift surfaced; never auto-blocked |

## IV. Doctrine reaffirmed

- ✅ **WARNING-ONLY** for every new dimension on first pass.
- ✅ Block-deploy promotions only after **calibration data exists**.
- ✅ No false-positive noise — every dimension was sanity-checked
  against the current baseline before shipping.
- ✅ Source-of-truth file (`HUB_VISUAL_BASELINE.json`) is git-tracked
  so trend regression is visible in `git diff`.

## V. What is NOT instrumented yet (and why)

| Idea | Why deferred |
|---|---|
| Animation density | Doctrine forbids ambient animation outright; instrumenting "0 expected" is wasted budget |
| Sound / haptic load | Out of scope — platform is silent by design |
| Accessibility contrast score | Tracked separately under WCAG governance (not iter437 scope) |
| Per-domain semantic coherence | Requires NLP; warming up trend data first |

## VI. Forward path (⚪ UNTESTED · plan only)

1. Re-run the baseline test once per deploy. The JSON cell is
   overwritten in-place, producing trend deltas in `git log`.
2. After **3 iterations**, draft per-metric thresholds. Promote one
   metric at a time from warning-only to deploy-blocking, validating
   with the operator at each step.
3. Add **Safety / Dispatch / FL portal cells** to the baseline test
   as those portals get V2 sidebars (one test param entry per portal,
   no source rewrite needed).
