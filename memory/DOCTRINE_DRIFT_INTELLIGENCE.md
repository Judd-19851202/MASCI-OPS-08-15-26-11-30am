# Doctrine Drift Intelligence

*Phase IV-BETA.4A · iter437 · 2026-02-27*
*Status: 🟢 SHIPPED · operator-readable drift summary · warning-only*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. What this is

`scripts/diff_doctrine_baseline.py` (≤145 LOC) diffs the working-tree
`HUB_VISUAL_BASELINE.json` against the last committed version and
prints a calm, 5–10 line operator-readable summary of what shifted
between deploys. Wired into `pre_deploy_check.sh` as a new
warning-only stage.

## II. Output contract (🟢 VERIFIED)

### Stable case
```
doctrine drift: every governed metric stable across portals.
```

### First run (no committed baseline yet)
```
doctrine drift: no committed baseline at `HEAD:memory/HUB_VISUAL_BASELINE.json` — first run.
```

### Drift detected (verified via simulated mutation)
```
doctrine drift summary · 1 portal(s) shifted
  · hr desktop loudness score (64.7 → 82.5) · DOCTRINE VIOLATION
  · hr desktop hue family count (2 → 5) · DOCTRINE VIOLATION
  · hr desktop badge density (14.7 → 30.0) · DOCTRINE VIOLATION
  · hr mobile hierarchy hash changed (f6ba352e → aaaaaaaa) · DOCTRINE VIOLATION
```

## III. Classification rules (🟢 VERIFIED)

| Metric | expected | suspicious | DOCTRINE VIOLATION |
|---|---|---|---|
| `loudness_score` | Δ ≤ 7.5 | Δ > 7.5 | absolute > 75 |
| `hue_family_count` | unchanged | Δ = 1..2 | Δ > 2 |
| `badge_density` | Δ ≤ 5pts | Δ > 5pts | ratio ≥ 2× or ≤ 0.5× |
| `emphasis_score` | Δ ≤ 5 | Δ > 5 | (no absolute ceiling yet — needs trend data) |
| `hierarchy_hash` | unchanged | (n/a — categorical) | any change |

Calibration philosophy: under-flag rather than over-flag. False
positives erode operator trust in the gate.

## IV. Operator workflow

1. Make a change.
2. Re-run `tests/pw_suite/test_visual_doctrine_baseline.py` (5 minutes).
   `HUB_VISUAL_BASELINE.json` is overwritten in-place.
3. Run `python3 scripts/diff_doctrine_baseline.py` (instant).
4. If output is "every governed metric stable", proceed.
5. If output flags a SUSPICIOUS or DOCTRINE VIOLATION, decide:
   - Intentional → annotate `_meta.intentional_changes[]` in the
     baseline JSON before committing.
   - Unintentional → fix the regression.
6. Commit the new baseline. The drift summary becomes the
   "what changed visually" comment in the commit body.

## V. Doctrine reaffirmed

- ✅ Output is ≤10 lines, calm operator wording
- ✅ Warning-only (script always exits 0)
- ✅ CI-compatible (stdout only; no side effects)
- ✅ No giant JSON dumps; per-metric per-portal per-viewport lines
- ✅ Wired into `pre_deploy_check.sh` as `stage_governance_doctrine_drift`
- ✅ ≤150 LOC (script is 145 LOC)
