# WP-18C8 Regression and Test Report

Date: 2026-08-07
Result: PASS

## Final regression evidence

### Backend

- `pytest /app/backend/tests/test_wp18c8_earned_value_engine.py -q` → `11 passed in 13.72s`
- `deep_testing_backend_v2` final hardening pass → `19 / 19` checks passed
- PM unauthenticated earned-value access returned `401`
- PM/Admin earned-value JSON and CSV export endpoints returned `200`

### Frontend / browser runtime

- `mcp_screenshot_tool` smoke check on preview root: PASS
- `testing_agent` report `/app/test_reports/iteration_158.json`: PASS
- `auto_frontend_testing_agent`: PASS across PM earned value, Executive earned value, and PM Budget Review
- First-load auto-load behavior passed on PM/Admin earned-value pages without manual Refresh
- Responsive sweep passed at `390 / 430 / 768 / 1024 / 1440`

## Resolved regression during final hardening

- PM Budget Review previously spent ~`11.5s` in repeated foundation/index setup.
- Root cause was repeated per-request foundation work in `project_controls_authority` and `project_budget_authority`.
- Final repair cached one-time foundation setup per DB and removed the repeated hot-path cost.

## Final pass set referenced by closeout

- `/app/test_reports/iteration_158.json`
- `/app/test_reports/pytest/pytest_wp18c8_iter158.xml`
- `/app/backend_test_wp18c8_final_hardening.py`
- `/app/backend_test_wp18c8_final_hardening_results.json`
- `/app/backend/tests/test_wp18c8_earned_value_engine.py`

## Final regression result

- Unresolved C8 blockers: `0`
- Truth defects: `0`
- Unjustified test gaps/skips: `0`
- Operator-language defects: `0`

No open C8 regression remained at closeout.