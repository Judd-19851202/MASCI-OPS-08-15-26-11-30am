# Timeline Loudness Probe — Certification

**Phase V-Prelude · Wave 1.1A**
**Status:** 🟢 **CERTIFIED · preview env**
**Date:** 2026-05-28

---

## Probe identity

| Field | Value |
|---|---|
| Script | `scripts/timeline_calmness_probe.py` |
| Trendline | `memory/TIMELINE_LOUDNESS_TRENDLINE.json` |
| Detail reports | `test_reports/timeline_calmness_<iter>.json` |
| Deploy gate hook | `scripts/pre_deploy_check.sh` — `stage_timeline_calmness_telemetry` |
| Scope | `/pm/projects/:projectNumber` (sidecar visible state) |
| Mode | warning-first · severe-regression blocking |
| Operator surface | NONE (passive governance only) |

## Heuristic targets

| Dimension | Doctrine target | Gate floor (5× target) |
|---|---|---|
| `accent_class_ratio` | ≤ 0.18 | > 0.90 |
| `badge_density_per_1k_px2` | ≤ 1.0e-4 | > 5.0e-4 |
| `red_usage` | ≤ 2 hits | > 10 hits |
| `hierarchy_compression` | ≤ 5 pairs | > 25 pairs |
| `vertical_density` | ≤ 12 rows above fold | > 60 rows above fold |
| `chronology_dup_ratio` | ≤ 0.20 | > 1.00 |

Score formula: `sum(max(0, (value - target) / target))` for every
dimension. **Lower = calmer.** Score 0 = every dimension at-or-under
its target.

## Current baseline

```
iteration:            wave-1-1a-final
score (lower=calmer): 0.0
viewports_measured:   3 (mobile · ipad · desktop)
gate_breaches:        []
accent_class_ratio:   0.0
badge_density:        0.0
red_usage:            0
hierarchy:            4 (under 5)
chronology_dup_ratio: 0.0
```

## Doctrine guarantees

| Rule | Enforcement |
|---|---|
| Passive only | Probe makes **no POST / PATCH / DELETE** to any backend route. Pytest verifies. |
| Operator-invisible | Probe writes only to `/app/memory/` and `/app/test_reports/`. Surfaces nothing. |
| Append-only trendline | Pytest reads the file before + after to assert monotonic growth. |
| Sub-3-minute runtime | Playwright sweep × 3 viewports completes in ~25 s in practice. |
| Sub-second `_score()` | Synchronous pure function · no I/O · no Playwright dependency. |
| Severe-regression-only blocker | Only > 5× target on any dimension blocks deploy. Routine drift surfaces as warning. |
| TRUST-TIME-1 | Every trendline timestamp is Z-suffixed UTC ISO. |

## Regression coverage

`backend/tests/test_timeline_calmness_probe.py`:
- `test_probe_runs_clean_and_produces_score` — end-to-end exec; asserts
  exit 0 and score ≤ 1.0 against the live preview pod.
- `test_trendline_file_is_json_list_and_append_only` — runs the probe
  twice with different iterations to verify append behaviour.
- `test_live_trendline_history_is_well_formed` — validates the live
  trendline file's shape on every PR.

🟢 3/3 green.

## What the probe is NOT

- ❌ A vanity score for operators.
- ❌ A leaderboard for "calmest deploy".
- ❌ A trigger for notifications or alerts.
- ❌ A replacement for the existing `measure_visual_loudness.py`
  portal-wide instrument (they coexist — this one is scoped to the
  sidecar, that one to the portals).

---

— certified by E1 · 2026-05-28
