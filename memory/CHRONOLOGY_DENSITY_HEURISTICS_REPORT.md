# Chronology Density Heuristics — Report

**Phase V-Prelude · Wave 1.1A**
**Status:** 🟢 **HEURISTICS LIVE · preview env**
**Date:** 2026-05-28

---

## Purpose

Detect — at the API layer, before any rendering — when the operational
chronology is degrading into activity-stream chaos: duplicate
signatures, repeated low-value rows, redundant chronology spam, or
runaway row counts that signal the timeline is no longer scannable.

These heuristics surface inside the calmness probe's `chronology`
block AND in standalone fixtures. They are **diagnostic**, not
operator-facing.

## Heuristics

### 1. `row_count`
Total number of timeline rows returned for the project (`≤ 200` per
the Wave 1 backend cap). Mostly an informational floor — paired with
`truncated` to detect projects whose chronology exceeds the cap.

### 2. `chronology_dup_ratio`
Fraction of rows whose `(kind, id, relationship, subtitle)` signature
is repeated. **Target: ≤ 0.20.** A high duplicate ratio means the
same operational event is being surfaced multiple times — a sign the
substrate is being abused (e.g., link spam) or that the aggregator
has a contract bug.

### 3. `avg_row_signature_len`
Average length of `title + subtitle` per row. A drop over time means
operators are filing increasingly terse / cryptic rows; the timeline
becomes harder to scan.

### 4. `low_value_repeats`
Count of rows whose `subtitle` strips down to ≤ 1 non-separator token
(e.g., bare action verbs with no context). **High = activity-stream
drift.** Caught by the new `subtitle` tokenisation in
`_measure_chronology`.

### 5. `truncated`
Boolean — true when the project hit the 200-row cap. The probe
records it so the trendline can spot projects that need filtering
help (Wave 2 search territory).

## Behavioural matrix

| Scenario | row_count | dup_ratio | low_value | Action |
|---|---|---|---|---|
| Fresh project · 1 constraint | 1 | 0.00 | 0 | none |
| Active project · 10 events · distinct | 10 | 0.00 | 0 | none |
| Operator pings constraint 6× with no notes | 7 | high | high | review chronology copy |
| 3 identical links from same source | 3 | ≥ 0.66 | 0 | review linkage discipline |
| Project hits 200-row cap | 200 | varies | varies | consider scoping filter |

## Probe validation

`backend/tests/test_chronology_density_heuristics.py` validates the
heuristics end-to-end:

| Test | What it proves |
|---|---|
| `test_noisy_chronology_dup_ratio_rises` | 6 bare pings + 3 dup links pushes `chronology_dup_ratio` ≥ 0.10 |
| `test_low_value_bare_rows_counted` | bare-action chronology surfaces in `low_value_repeats` ≥ 4 |
| `test_clean_project_stays_calm` | a single rich-text constraint scores 0.0 on both metrics |
| `test_score_function_aggregates_breaches` | synthetic 6× target input produces a breach for every dimension |

🟢 4/4 green.

## What the heuristics are NOT

- ❌ A search / filter mechanism for operators.
- ❌ A reason to delete or hide rows from the timeline.
- ❌ A justification to add toast/notification "spam detected" copy
  anywhere in the UI.
- ❌ An admin dashboard surface.

They exist solely as a **diagnostic ribbon on the trendline**.

---

## Open questions for the observation window

- Should `low_value_repeats` weight toward the calmness score, or
  stay diagnostic? **Current answer:** stay diagnostic; weight only
  the visual loudness dimensions until the operator has feedback.
- Is the 0.20 dup-ratio target right? **Current answer:** start at
  0.20 and tune after one cycle of real chronology data lands.

— issued by E1 · 2026-05-28
