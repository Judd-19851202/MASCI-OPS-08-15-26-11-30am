# WP-18C8 Regression and Test Report

Date: 2026-08-07
Result: PASS

## Backend runtime proof

- PM local API proof passed
- Executive/Admin local API proof passed
- PM unauthenticated earned-value access returned `401`
- PM and Executive CSV export endpoints returned `200` with `text/csv`
- Budget overview returned approved candidate linkage with `review_queue_open = 0`

## Frontend runtime proof

- Smoke check passed for PM earned-value route
- Smoke check passed for Executive earned-value route
- First-load auto-load retest passed without manual Refresh
- PM budget review responsive sweep passed at `390 / 430 / 768 / 1024 / 1440`
- ES toggle smoke check passed on the PM earned-value route

## Subagent / test-agent evidence

- `testing_agent` report: `/app/test_reports/iteration_156.json`
  - initial failure found: first-load route required refresh
  - repaired and re-verified
- `deep_testing_backend_v2`: PASS for WP-18C8 backend validation
- `auto_frontend_testing_agent`: PASS (`100%`) for PM/Admin C8 surfaces, seeded metrics, discoverability, and responsiveness

## Added automated regression coverage

- `backend/tests/test_wp18c8_earned_value_engine.py`

## Final regression result

- No open C8 regression remained at closeout.