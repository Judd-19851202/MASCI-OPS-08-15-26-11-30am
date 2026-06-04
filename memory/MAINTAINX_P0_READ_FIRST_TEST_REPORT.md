# MAINTAINX P0 · READ-FIRST TEST REPORT

**Date:** 2026-06-04 18:30 UTC
**Sprint:** OMEGA P0-A/P0-B — Read-First MaintainX Asset Integration
**Test file:** `backend/tests/test_maintainx_p0_read_first.py`

---

## 1 · Run command

```bash
cd /app/backend && python -m pytest tests/test_maintainx_p0_read_first.py -v
```

---

## 2 · Latest run result

```
============================= test session starts ==============================
platform linux -- Python 3.11.15, pytest-9.0.3, pluggy-1.6.0
collecting ... collected 13 items

tests/test_maintainx_p0_read_first.py::test_missing_api_key_test_connection PASSED [  7%]
tests/test_maintainx_p0_read_first.py::test_missing_api_key_assert_raises PASSED [ 15%]
tests/test_maintainx_p0_read_first.py::test_invalid_key_returns_401_classified PASSED [ 23%]
tests/test_maintainx_p0_read_first.py::test_successful_connection_mock PASSED [ 30%]
tests/test_maintainx_p0_read_first.py::test_asset_list_pagination_mock PASSED [ 38%]
tests/test_maintainx_p0_read_first.py::test_asset_list_max_pages_cap PASSED [ 46%]
tests/test_maintainx_p0_read_first.py::test_rate_limit_surfaces_retry_after PASSED [ 53%]
tests/test_maintainx_p0_read_first.py::test_duplicate_unit_number_flagged PASSED [ 61%]
tests/test_maintainx_p0_read_first.py::test_duplicate_risk_blocks_same_unit PASSED [ 69%]
tests/test_maintainx_p0_read_first.py::test_dryrun_no_writes_when_save_false PASSED [ 76%]
tests/test_maintainx_p0_read_first.py::test_dryrun_only_writes_to_dryrun_reports_when_save_true PASSED [ 84%]
tests/test_maintainx_p0_read_first.py::test_client_write_methods_raise PASSED [ 92%]
tests/test_maintainx_p0_read_first.py::test_api_key_masked_everywhere PASSED [100%]

============================== 13 passed in 0.16s ==============================
```

**13 / 13 PASS**

---

## 3 · Coverage matrix

| # | Required test (per directive) | Test name | Status |
| --- | --- | --- | --- |
| 1 | Missing API key | `test_missing_api_key_test_connection` + `test_missing_api_key_assert_raises` | PASS |
| 2 | Invalid API key | `test_invalid_key_returns_401_classified` | PASS |
| 3 | Successful connection mock | `test_successful_connection_mock` | PASS |
| 4 | Asset list mock | `test_asset_list_pagination_mock` | PASS |
| 5 | Pagination mock | `test_asset_list_pagination_mock` + `test_asset_list_max_pages_cap` | PASS |
| 6 | Rate limit handling | `test_rate_limit_surfaces_retry_after` | PASS |
| 7 | Duplicate detection | `test_duplicate_unit_number_flagged` + `test_duplicate_risk_blocks_same_unit` | PASS |
| 8 | Dry-run produces no writes | `test_dryrun_no_writes_when_save_false` | PASS |
| 9 | Write disabled prevents mutation | `test_client_write_methods_raise` | PASS |
| 10 | No MASCI equipment mutation | `test_dryrun_no_writes_when_save_false` (counters verified `equipment_master.insert_calls == 0`, `update_calls == 0`) | PASS |
| 11 | No MaintainX mutation | `test_client_write_methods_raise` — every write method raises `MaintainxWriteDisabled` | PASS |

---

## 4 · Mocking strategy

- `httpx.MockTransport` is used for upstream-response control: tests inject 200 / 401 / 429 deterministically without ever calling MaintainX.
- A tiny in-test `_DB` class exposes the same surface the pipeline expects (`find`, `find_one`, `insert_one`, `update_one`, `delete_one`) and counts every call so we can prove "writes_performed = 0" at the storage layer.
- Where the pipeline must do real iteration through `MaintainxClient.iter_assets`, we monkey-patch the method to yield a known list — keeping the integration-test deterministic.

This means: **no test exercise made a single outbound HTTP call** to any real MaintainX host.

---

## 5 · Negative assertions explicitly verified

| Assertion | Source test |
| --- | --- |
| `equipment_master.insert_calls == 0` after dry-run | `test_dryrun_no_writes_when_save_false` |
| `equipment_master.update_calls == 0` after dry-run | same |
| `asset_mappings.insert_calls == 0` after dry-run | same |
| `asset_mappings.update_calls == 0` after dry-run | same |
| `maintainx_dryrun_reports.insert_calls == 0` when `save_report=False` | same |
| `maintainx_dryrun_reports.insert_calls == 1` when `save_report=True` | `test_dryrun_only_writes_to_dryrun_reports_when_save_true` |
| `create_asset() / update_asset() / delete_asset()` raise `MaintainxWriteDisabled` even with `MAINTAINX_WRITE_ENABLED=true` | `test_client_write_methods_raise` |
| API key never appears in `public_view()` output | `test_api_key_masked_everywhere` |

---

## 6 · Verdict

```
P0 READ-FIRST TEST SUITE  :  13/13 PASS  ·  ZERO WRITES DEMONSTRATED
```

The pipeline is unit-test-certified to produce no writes to MaintainX, no writes to `equipment_master`, no writes to `asset_mappings`, and no writes to any operational collection. The only optional write (`maintainx_dryrun_reports`) is gated by an explicit `save_report=True` flag, asserted by test.
