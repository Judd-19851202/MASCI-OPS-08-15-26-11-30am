PRE-DEPLOYMENT TEST RESULTS
===========================

DATE: 2026-02-15

────────────────────────────────────────────────────────────────────────────
COMMAND TABLE
────────────────────────────────────────────────────────────────────────────
| Suite                                      | Command                                                                                                                                | Pass | Fail | Skip | Runtime | Blocker |
|--------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------|------|------|------|---------|---------|
| Track 18 family regression                 | `cd /app/backend && python -m pytest tests/test_track_18_* -q --tb=line`                                                                | 778  | 0    | 1    | ~33s    | No      |
| Track 16 + 17 + 18 combined                | `cd /app/backend && python -m pytest tests/test_track_16_* tests/test_track_17_* tests/test_track_18_* --ignore=tests/test_track_16_06_live_smoke.py -q` | 1429 | 0    | 1    | ~164s   | No      |
| Track 18.12B lock                          | `cd /app/backend && python -m pytest tests/test_track_18_12b_transportation_dispatcher_functionality.py -q`                            | 47   | 0    | 0    | <1s     | No      |
| Track 18.12C lock                          | `cd /app/backend && python -m pytest tests/test_track_18_12c_transportation_role_permissions.py -q`                                    | 43   | 0    | 0    | <1s     | No      |
| Track 18.12C live API                       | `REACT_APP_BACKEND_URL=$URL python -m pytest tests/test_track_18_12c_live_api.py -q` (live)                                            | 41   | 0    | 2    | ~210s   | No (2 skips are cold-start preview-gateway 502s on admin intelligence — documented non-blocker) |
| Pre-deployment release-safety              | `cd /app/backend && python -m pytest tests/test_pre_deployment_release_safety.py -q`                                                    | 53   | 0    | 0    | <1s     | No      |
| Deployment gate (per-track files)          | `python /app/scripts/deployment_gate.py`                                                                                                | n/a  | n/a  | n/a  | n/a     | RUN AT DEPLOY |
| ESLint frontend                            | `cd /app/frontend && yarn lint` (CRA built-in)                                                                                          | pass | 1 (pre-existing _orientation.jsx `react/no-unstable-nested-components`) | 0 | <30s | No |

────────────────────────────────────────────────────────────────────────────
FAILURES
────────────────────────────────────────────────────────────────────────────
None functional. All failure-class assertions across Track 18 family
are GREEN. The 2 skips in the live-API suite are the documented
admin-only Intelligence cold-start aggregations exceeding the preview
gateway timeout (item #1 of `PRE_DEPLOYMENT_RELEASE_FREEZE.md`).

────────────────────────────────────────────────────────────────────────────
KNOWN FLAKES
────────────────────────────────────────────────────────────────────────────
- `test_track_15_93_zero_touch_bootstrap` (and Track 15.76 / 15.79e):
  occasionally fails on heavy concurrent full-suite runs; passes solo
  in <2s. Documented across multiple prior tracks. Not a release
  blocker. Retry solo if it bites the deploy gate.

────────────────────────────────────────────────────────────────────────────
LINTERS
────────────────────────────────────────────────────────────────────────────
| Linter                                  | Status | Notes                                                          |
|-----------------------------------------|--------|----------------------------------------------------------------|
| Design-system R1–R8 (Track 18.03/04/11) | PASS   | All eight rules green; R8 calibrated by Track 18.11.            |
| Governance boundary (Track 18.10)       | PASS   | No operational logic in /pages/admin/, no admin chrome in TxOps. |
| Track 18.09A friction lint               | PASS   | No prohibited tokens in operational copy.                       |
| ESLint                                   | PASS*  | One pre-existing `react/no-unstable-nested-components` warning. |

────────────────────────────────────────────────────────────────────────────
SOLO RETRY RESULTS (KNOWN FLAKES)
────────────────────────────────────────────────────────────────────────────
- `tests/test_track_18_12c_live_api.py` solo: 12/12 pass for
  dispatch-can-access-ops-guard; 7/7 pass for admin-strict-rejects-
  dispatch. Slow admin intel skips correctly when preview gateway
  short-circuits at 502.

────────────────────────────────────────────────────────────────────────────
OVERALL TEST STATUS
────────────────────────────────────────────────────────────────────────────
✅ GREEN — no functional failure. Two documented skips on admin
intelligence cold-start (preview-only artefact, non-blocker).
