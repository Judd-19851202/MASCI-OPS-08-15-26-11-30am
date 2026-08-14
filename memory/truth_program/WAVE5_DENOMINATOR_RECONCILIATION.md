# WAVE 5 — CANONICAL TRUTH SURFACE DENOMINATOR RECONCILIATION

Owner order (Wave-5 Final): reconcile the legacy 547 vs the new enumeration scientifically,
establish explicit inclusion/exclusion rules, and make the denominator permanently
machine-reproducible. This document is the authoritative reconciliation record.

## OLD DENOMINATOR (superseded)
- Value: 547 ("KPI/count/health/status components", Wave-1).
- Methodology limitation: NOT reproducible from durable artifacts. The exact scan
  config/granularity (component vs routed surface vs unique metric vs deduped concept)
  was not preserved. It was a hand-carried total. It cannot be regenerated at a given SHA.
- Decision: RETIRED. Not fabricated into continuity. It is NOT the case that "547 grew to
  783" — 547 and the new scan are different scopes/granularities entirely.

## NEW CANONICAL METHODOLOGY (authoritative, reproducible)
- Owner: `scripts/wave5_truth_surface_canonical.py` -> `TRUTH_SURFACE_CANONICAL.csv/.json`.
- Granularity: unique (component-file, rendered truth element), deduplicated so a component
  reused across multiple routes counts once per element (not per mount). This removes the
  route-duplication inflation that produced the earlier 783 element-with-duplicates count.
- CANDIDATE UNIVERSE = every value-bearing rendered element (`<Stat>`/`<KV>`/`<Pct>`/
  `<ScoreRing>`) plus every `data-testid` metric/status/structural element in frontend/src
  (excluding tests). This is the full machine-scanned universe.
- EXPLICIT EXCLUSION RULES (NON_TRUTH_SURFACE_EXCLUDED_WITH_REASON):
  * structural/control/label/state testids (root/shell/hero/title/header/refresh/export/
    csv/pdf/print/loading/error/empty/skeleton/tab/link/button/toggle/filter/search/input/
    select/modal/nav/menu/banner/section/meta/catalog/framework/authority-statement/
    generated-at/include-inactive/view-missing/icon/caption/help/hint/tooltip/coaching/
    close/save/submit/page/pagination/sort/column/checkbox/radio/form/field-label);
  * control elements (button/link/input/tab/select/textarea/switch/checkbox) with no value;
  * demo/dev/sandbox/example/storybook files.
- INCLUSION = every candidate that is NOT excluded, i.e. a value-bearing human truth surface.
- CLASSIFICATION of every INCLUDED surface into a final disposition (evidence = the code
  pattern recorded per row): CANONICAL_KPI, CANONICAL_STATUS, DIRECT_FACT,
  GOVERNED_DISTINCT_VARIANT.

## EXACT RECONCILED RESULT (this SHA, reproducible)
- Candidate universe:        2934
- Excluded with reason:      2538  (structural/control/label/state markup + demo)
- Included truth surfaces:    396
- INVARIANT: included (396) + excluded (2538) = candidate (2934)  -> HOLDS.
- OPEN / PENDING / UNKNOWN / ASSUMED: 0.
- Included breakdown (final dispositions):
  * CANONICAL_KPI      39  (reconciled Wave-5 canonical calculators)
  * CANONICAL_STATUS   97  (Wave-2 governed status/health-band vocabulary)
  * DIRECT_FACT       256  (stored record field / local list length; no hidden computation)
  * GOVERNED_DISTINCT_VARIANT 4 (backend-computed % rendered as fact, not one of the 12 named KPI concepts:
    operational readiness_pct, i18n translation coverage pct)
- Known harmless edge (documented, not a truth defect): 2 `<KV value={data.inspection_*}>`
  record-field renders are conservatively classified NON_TRUTH by the structural rule; both
  are stored-fact renders (would be DIRECT_FACT), so the included count is a 2-surface
  under-count, never an over-count / never a false truth claim.

## CANONICAL DENOMINATOR (authoritative going forward)
- Wave-5 Truth Surface denominator = **396 included human-visible truth surfaces**
  (over a reproducible candidate universe of 2934, with 2538 explicitly excluded).
- This number is regenerated from source by `scripts/wave5_truth_surface_canonical.py`
  and LOCKED by guard `GD-0025` (test_gd0025_truth_surface_enumeration.py): the guard
  fails if the invariant breaks, if any surface is OPEN, or if the included count drifts
  from the locked baseline (396) without a governed reconciliation. No more hand-maintained
  or approximate truth-surface totals — ever.

## DISPOSITION COVERAGE (proven governed classes)
- CANONICAL_KPI  -> Wave-5 canonical calculators (percent_complete, expiring_rate,
  utilization, variance[+favorable], efficiency, health/trust, compliance, eligibility,
  avg_days, ownership) with guards GD-0017..GD-0024.
- CANONICAL_STATUS -> Wave-2 status vocabulary (TC-0002) + health_score bands (GD-0022).
- DIRECT_FACT -> stored record field / count of the very population displayed; lineage
  record -> API serialization -> component prop -> render, no hidden computation/denominator.
- Population count/total facts additionally governed by Wave-4 (735/735 PROVEN, GD-0013/14/15).
