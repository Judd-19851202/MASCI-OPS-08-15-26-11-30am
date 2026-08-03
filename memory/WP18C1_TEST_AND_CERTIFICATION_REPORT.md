# WP18C1 Test and Certification Report

Date: 2026-08-03

## Backend verification

### Manual runtime verification

Verified live hierarchy endpoints through authenticated admin access:

- hierarchy overview
- nodes list / detail
- review queue
- resource assignments
- scope preview
- create / update / deactivate / archive cycle
- validation failures for bad input

### Automated backend tests

`pytest /app/backend/tests/test_wp18c1_hierarchy_foundation.py -q`

Result:

- `24 passed`
- `0 failed`

## Frontend / UX verification

Testing agent report: `/app/test_reports/iteration_110.json`

Verified:

- Organization Structure page load
- summary cards
- hierarchy list filtering
- detail panel updates
- review queue visibility
- assignments visibility
- scope preview loading
- add-dialog behavior
- row selection
- EN/ES labels
- responsive widths `390`, `430`, `768`, `1024`, `1440`
- admin login regression smoke
- governance navigation regression smoke

## Performance spot checks

Measured live preview timings (approximate repeated samples):

- overview: `1637–1672 ms`
- nodes: `1346–1386 ms`
- review queue: `1344–1346 ms`
- resource assignments: `1357–1378 ms`
- scope preview: `1358–1402 ms`

Result: acceptable for WP-18C1 foundation scale; no evidence of an immediate replacement-level performance defect.

## Defects found and fixed during WP-18C1

1. upsert conflict from `created_at` in `$set` + `$setOnInsert`
2. stale review-queue ObjectId serialization in API responses
3. unstable equipment binding identifiers causing drift across repeated backfills
4. live overview selecting archived legacy company rows instead of the active MASCI root
5. backend test auth fixture missing directory-token header for session-safe requests

## Certification result

WP-18C1 testing and certification evidence is complete and supports closeout.