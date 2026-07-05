# DR-ROI-001D · Test Report

## Test files added / updated

- `tests/test_dr_roi_001d_photo_vision.py` — **12 tests** (feature-flag default off, envelope schema locked, evidence hash determinism + delta, upsert intel shape (default `requires_supervisor_confirmation=true`), accept + dismiss link, resolve question, route mount check, no writes to `job_photos` or `daily_reports`, vision adapter interface signature).
- `tests/test_dr_roi_001a_b_shell.py` — parity test updated to `1460 / 1464 / 1282` (additive delta locked).
- `tests/test_track_22_2_app_js_route_extraction.py` — same parity update.

## Total: **67 / 67 GREEN** across the DR-ROI-001 + ODS-001 + Gateway + this-track suites

```
$ python -m pytest tests/test_dr_roi_001d_photo_vision.py tests/test_ai_gateway.py \
    tests/test_ods_001_spine.py tests/test_dr_roi_001a_b_shell.py \
    tests/test_dr_roi_001c_ai_service.py tests/test_track_22_2_app_js_route_extraction.py -q
....................................................................... [100%]
67 passed in 5.09s
```

## Live e2e proof (curl · this session)

- `POST /api/dr-v2/drafts` with a photo → 200, report saved.
- `POST /api/dr-v2/photos/phX1/analyze` without image bytes → 200 with `ok:false, analysis_status:"unavailable"` (graceful — no invention, no crash).
- `GET /api/dr-v2/photos/phX1/intelligence?report_id=…` → 200 with the cached intel doc.

## What was NOT tested this session

- **Full live vision call with real image bytes.** The scaffold is in place and the graceful failure path is proven; a live call requires a valid image + an OpenAI vision entitlement on the emergent LLM key. The unit tests validate the adapter interface, envelope shape, and store transitions; the wire path is identical to the DR-V2 text path already proven live.
- **Cross-adapter failover for vision.** Interface reserved; failover in `Gateway.dispatch_vision()` matches text `dispatch()`; not yet exercised end-to-end.

## Regressions

None detected.
