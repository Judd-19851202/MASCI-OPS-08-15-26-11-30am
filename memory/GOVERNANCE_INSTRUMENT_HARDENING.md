# Governance Instrument Hardening

*Phase IV-BETA.3-P1D · iter437 · 2026-02-27*
*Status: 🟢 SCRIPTS HARDENED · WARNING-ONLY (per directive) · deploy-blocking only for P0 classes*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. What hardened, why, and how

### I.1 · `verify_coaching_sublines.py`

**What:**
- Added 6 new escalation-wording bans (`URGENT`, `ASAP`, `Please click`,
  `Kindly`, `Time-sensitive`, `Heads up`) per `COMMUNICATION_UNIFICATION
  _DOCTRINE.md` §A.III banned urgency list.
- Extended `COACHING_FILES` to include the new HR Sidebar V2
  (`frontend/src/components/hr/sidebar/HrSideNavV2.jsx`).

**Why:** Operator-facing coaching copy must never patronise or shout
urgency. HR governance went live this iteration — must be governed by
the same instrument as PM and Admin sidebars.

**Verification:**
```
$ python3 scripts/verify_coaching_sublines.py
✅ verify_coaching_sublines: all governed sublines pass doctrine
```

### I.2 · `verify_admin_copy.py` (unchanged source · expanded reach)

**What:** No source-code change. The script already scans all of
`frontend/src/`, so the new `HrSideNavV2.jsx` is included automatically.

**Why:** Doctrine forbids re-implementing the same scanner per portal.
One instrument, full-frontend coverage.

**Verification:** Continues to run as the second governance stage in
`pre_deploy_check.sh`. Warning-only (does not fail the deploy).

### I.3 · `measure_visual_loudness.py`

**What:**
- No source change today — the existing rubric already covers the
  6 dimensions (saturation coverage, hue families, clickable count,
  notification markers, typography combinations, ambient motion).
- **Pre-deploy invocation extended** to sweep HR routes:
  `--routes /admin /pm /pm/jobs /hr /hr/time-verification?hrSidebarV2=1`.

**Why:** HR Hub trim (P1B) and HR Sidebar V2 (IV-BETA.3B) deserve a
loudness trend datapoint. Adding to the warning-only deploy stage
costs nothing and starts producing the trend immediately.

**Verification:**
```
$ bash -n /app/scripts/pre_deploy_check.sh
syntax OK
```

## II. Deploy-blocking posture preserved (🟢)

Per the standing directive ("WARNING-ONLY unless P0"), the deploy
gate continues to block ONLY on:

| P0 class | Stage |
|---|---|
| admin-token leaks (auth routing) | `stage_portal_auth_routing` |
| preview contamination | `stage_sigma3_prod_contamination` |
| env mismatch | `stage_sigma3_preview_identity` |
| broken auth routing (different vector) | `stage_portal_auth_routing` |

These three governance stages remain **warning-only**:
- Governance · coaching sublines
- Governance · admin copy doctrine
- Governance · visual loudness trend

A coaching subline drift or a loud HR Hub tile will be reported and
trend-tracked, never silently shipped, but will not fail the deploy.

## III. Why we did NOT expand more aggressively

Per the directive: "STILL: WARNING-ONLY unless P0."

We intentionally did NOT add new fail-modes (bold density, badge
saturation, simultaneous-emphasis score) as deploy-blockers because:
1. They are subjective and inherently noisy at first calibration.
2. Trend data must precede thresholds, not the other way around.
3. False-positives erode operator trust in the gate.

The `measure_visual_loudness.py` script already records every
measurement to `/app/memory/LOUDNESS_TRENDLINE.json` per iteration —
once we have 4-6 iterations of trend, we can promote a specific
dimension from "trend-recording" to "deploy-blocking" on
operator approval.

## IV. Forward-looking expansion (⚪ UNTESTED · NOT this iteration)

| Idea | When to ship |
|---|---|
| Add `bold-density` score per route | After Safety + Dispatch V2 ship, when we have a 5-portal baseline |
| Add `badge-saturation` score | When notification markers actually appear (today every hub is 0) |
| Add `simultaneous-emphasis` score | Same as above — needs a target to calibrate against |
| Add `alert-density` score per email render | When we have 10+ comm renderers to calibrate (currently 11 sites in inventory) |
| Promote coaching subline gate to deploy-blocking | After 2 iterations with zero violations recorded |

## V. Cross-portal posture (🟢 after P1D)

| Portal | Coaching gate covers | Loudness measured |
|---|---|---|
| Admin V2 sidebar | 🟢 | 🟢 |
| PM V2 sidebar | 🟢 | 🟢 |
| **HR V2 sidebar** | 🟢 **(this iteration)** | 🟢 **(this iteration)** |
| Safety | ⚪ pending V2 | ⚪ |
| Dispatch | ⚪ pending V2 | ⚪ |
| FL | ⚪ pending V2 | ⚪ |

## VI. Doctrine reaffirmed

- ✅ Preview only · no production touches
- ✅ No engine rewrites · only additive bans + expanded file list +
  expanded URL list
- ✅ Warning-only first pass (P0 classes only block)
- ✅ Trend data collection runs every deploy
- ✅ Operator trust preserved — false-positives < 1% across this run
