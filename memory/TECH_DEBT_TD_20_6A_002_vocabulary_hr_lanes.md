# TD-20.6A-002 · `test_vocabulary_hr_sees_all_lanes` — one-page report

**Filed under Track 20.6A · Technical Debt & Failure Discovery Amendment.**

## Header

| Field | Value |
|---|---|
| **Debt ID** | TD-20.6A-002 |
| **Title** | `test_vocabulary_hr_sees_all_lanes` uses strict-equality set assertion that broke when Track 19.59 additively added the `vendor` lane |
| **Class** | **C — Existing Technical Debt** (introduced by Track 19.59; not caused by Track 19.61) |
| **Owner** | Safety-Records subsystem team |
| **Priority** | P3 (test-only; no production impact) |
| **Status** | OPEN |
| **Proposed target track** | 20.6B (Test Hardening) |
| **Discovered during** | Track 19.61 regression sweep (2026-08-02) |

## What failed

`backend/tests/test_track_19_21_e2e_live.py::test_vocabulary_hr_sees_all_lanes`
asserts:

```python
assert set(body.get("allowed_lanes_for_actor") or []) == {
    "hr", "safety", "asset", "corporate_import"
}
```

The `/api/employee-records/vocabulary` endpoint now legitimately returns
`{"hr", "safety", "asset", "corporate_import", "vendor"}` because Track
19.59 added `vendor` as a fifth first-class ownership lane. The
strict-equality assertion no longer holds.

## Why did it fail

The test uses `set(...) == {...}` (strict equality) instead of
`{expected...} <= set(...)` (superset containment).

Additive backend evolution (adding a new lane / entity kind / product)
is a first-class design pattern of this platform — additive changes
must not break the test harness. Strict-equality assertions on
open-ended sets are a lint-worthy anti-pattern here.

## When was it introduced

Two tracks combined:

1. **Track 19.21 (2026-04-XX)** wrote the test with strict-equality
   against the original four-lane set (`hr`, `safety`, `asset`,
   `corporate_import`).
2. **Track 19.59 (2026-06-XX)** additively introduced the `vendor`
   lane. The 19.59 lock test was correctly updated to include
   `vendor`, but the live-e2e test was NOT touched.

Result: since 19.59 there has been a latent mismatch, invisible in
the default regression harness because the live-e2e test module
requires `REACT_APP_BACKEND_URL` which is absent in the standard
preview env.

## Which track introduced it

- **Test file itself:** Track 19.21.
- **Regression:** Track 19.59 (the additive `vendor` lane).

## Why was it still present

The live-e2e module only runs in a fully-configured e2e runner (backend
URL env + real portal tokens + live server). It is not part of the
default `pytest` run in preview. The 19.59 certification did not
enumerate live-e2e assertions, so the drift was invisible until Track
19.61 broadened the regression sweep.

Also — 19.60 added the vendor thread promotion, and 19.61 added the
`asset` entity_kind, but neither triggered this test either because
the lane set was already the correct 5-element superset by then.

## Production impact

**None (production-safe).**

- Every production consumer of `/api/employee-records/vocabulary` uses
  the response as a data-driven dropdown / filter — they iterate the
  returned array; they do not assert a fixed cardinality.
- The vendor lane is a real, certified, production feature (Track
  19.59). Returning it is correct behavior.
- The test is stale; the endpoint is right.

## Should it have been fixed during Track 19.61?

**Appropriate to defer.** Track 19.61 was strictly a Universal Thread
promotion; fixing a test-only strict-equality assertion introduced by
Track 19.59 would have been out-of-scope. That said, the equivalent
19.59 lock test in `test_track_19_59_vendor_lane_historical_records.py`
WAS updated during Track 19.61 (the `asset` entity_kind was additively
appended, and the assertion switched from `==` to `<=`) — because that
one WAS in the standard regression harness and blocked green. The
live-e2e test was correctly left for a dedicated test-hardening pass.

## Why is it safe

- Zero production behavior change.
- No customer data exposed / hidden / mis-scoped.
- Existing product consumers of the endpoint are additive-tolerant.
- Failure is confined to a non-default test module.

## Permanent fix

Rewrite the assertion as:

```python
allowed = set(body.get("allowed_lanes_for_actor") or [])
required = {"hr", "safety", "asset", "corporate_import"}
assert required <= allowed, f"HR must see the original four lanes; got: {allowed}"
```

That is the additive-safe superset check the platform doctrine
requires. Apply the same pattern to any other strict-equality set
assertion in the live-e2e module (survey the whole file when landing
Track 20.6B).

## When will it be fixed

**Track 20.6B** (Test Hardening). Priority P3.

## Verification when fixed

- `pytest backend/tests/test_track_19_21_e2e_live.py::test_vocabulary_hr_sees_all_lanes -v`
  returns green with the current (5-lane) vocabulary response.
- Adding a future sixth lane (e.g. a `contractor` lane) does not
  re-break the assertion.
