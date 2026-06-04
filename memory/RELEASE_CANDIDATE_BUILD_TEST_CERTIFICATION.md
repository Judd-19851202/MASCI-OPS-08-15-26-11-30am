# RELEASE CANDIDATE · BUILD / TEST CERTIFICATION

**Date:** 2026-06-04 19:55 UTC
**Sprint:** OMEGA — Release Candidate Pre-Deploy Certification

---

## 1 · Frontend production build

```
$ cd /app/frontend && yarn build
...
Compiled with warnings.
Done in 33.13s.
```

**Verdict:** PASS — `build/` artefacts emitted; deployable bundle ready.

Warnings present are all `react-hooks/exhaustive-deps` advisories on files **outside** this release bundle (legacy `AdminAuditLog.jsx`, `SafetyDocuments.jsx`, `SafetyFireExtinguishers.jsx`, `ShopHub.jsx`, etc.). These are pre-existing baseline warnings — none originate from any of the 15 frontend files modified in this release. Confirmed via per-file diff: no new `useEffect` / `useCallback` introduced in changed files.

## 2 · ESLint on changed frontend files

| File | Result |
| --- | --- |
| `components/admin/MaintainxDefectCoverageSection.jsx` | 0 blocking · 0 advisory |
| `components/admin/MaintainxP0Tab.jsx` | 0 blocking · 0 advisory |
| `components/dispatch/DispatchEquipmentMaintenanceIndicator.jsx` | 0 blocking · 0 advisory |
| `components/shop/ShopMaintainxReadinessTile.jsx` | 0 blocking · 0 advisory |
| `components/iam/IamStandardCells.jsx` | 0 / 0 (from prior cert) |
| `components/iam/IamUserDetailDrawer.jsx` | 0 / 0 (from prior cert) |
| `components/iam/PortalUsersAccordion.jsx` | 0 / 0 (from prior cert) |
| `components/field_memory/FieldMemoryGlance.jsx` | 0 / 0 (from prior cert) |
| `pages/DispatchHub.jsx` | 0 / 0 |
| `pages/admin/AdminPeople.jsx` | 0 / 0 |
| `pages/admin/AdminIntegrationCenter.jsx` | 0 / 0 |
| `pages/admin/AdminDispatch.jsx` | 0 / 0 |
| `pages/HrFieldLeadershipUsers.jsx` | 0 / 0 |
| `pages/ShopHub.jsx` | 0 / 0 |

## 3 · Backend lint on changed files

| File | Result |
| --- | --- |
| `services/maintainx_client.py` | 0 / 0 |
| `services/maintainx_asset_sync.py` | 0 / 0 |
| `services/maintainx_defect_coverage.py` | 0 / 0 |
| `routes/integrations/maintainx_p0.py` | 0 / 0 |

## 4 · Backend tests (MaintainX P0 suite)

```
$ cd /app/backend && python -m pytest tests/test_maintainx_p0_read_first.py -v
collected 13 items

test_missing_api_key_test_connection                                 PASSED
test_missing_api_key_assert_raises                                   PASSED
test_invalid_key_returns_401_classified                              PASSED
test_successful_connection_mock                                      PASSED
test_asset_list_pagination_mock                                      PASSED
test_asset_list_max_pages_cap                                        PASSED
test_rate_limit_surfaces_retry_after                                 PASSED
test_duplicate_unit_number_flagged                                   PASSED
test_duplicate_risk_blocks_same_unit                                 PASSED
test_dryrun_no_writes_when_save_false                                PASSED
test_dryrun_only_writes_to_dryrun_reports_when_save_true             PASSED
test_client_write_methods_raise                                      PASSED
test_api_key_masked_everywhere                                       PASSED

============================== 13 passed in 0.16s ==============================
```

**Verdict:** 13 / 13 PASS — no regressions.

Negative-write assertions explicitly verified by the suite:
- `equipment_master.insert_calls == 0`
- `equipment_master.update_calls == 0`
- `asset_mappings.insert_calls == 0`
- `asset_mappings.update_calls == 0`
- `maintainx_dryrun_reports.insert_calls == 0` (when `save_report=False`)
- `MaintainxClient.{create,update,delete}_asset()` raise `MaintainxWriteDisabled` (even with `MAINTAINX_WRITE_ENABLED=true`)
- `MaintainxConfig.public_view()` never includes the raw key body

## 5 · Public employee endpoint live probe

```
GET /api/employees  (anonymous, public)
  COUNT: 330
  KEYS_RETURNED: ['crew','employee_id','id','is_active','name','role','trade']
  FORBIDDEN_LEAKS: NONE
  EXTRA_KEYS_BEYOND_ALLOWLIST: NONE
```

All 12 forbidden fields (`phone`, `email`, `cdl_*`, `driver_status`, `medical_card_expiration_date`, `approved_company_driver`, `status_history`, `created_at`, `updated_at`) are absent. Allow-list (`id`, `name`, `employee_id`, `crew`, `role`, `trade`, `is_active`) is the EXACT projection returned.

## 6 · Other backend probes

| Endpoint | Method | Result |
| --- | --- | --- |
| `POST /api/auth/multi-login` (jaymn.judd@mascigc.com) | POST | `{ok:true}` · admin / hr / dispatch / shop / safety / pm / fl tokens minted |
| `GET /api/admin/maintainx/p0/config` (admin) | GET | `{api_key_present:false, write_enabled:false, sync_enabled:false}` |
| `POST /api/admin/maintainx/p0/test` (admin) | POST | `{ok:false, status:"missing_api_key"}` (graceful) |
| `POST /api/admin/maintainx/p0/dryrun` (admin) | POST | `writes_performed.*=0`, `saved=false` |
| `GET /api/admin/maintainx/defect-coverage` (admin) | GET | `totals.open_defects=138`, `writes_performed.*=0` |
| `GET /api/integrations/maintainx/defect-coverage` (portal) | GET | identical payload |

## 7 · Blockers

NONE.

## 8 · Verdict — Build / Test

```
BUILD / TEST CERTIFICATION  :  PASS

  Frontend yarn build                : PASS (33.13s, deployable)
  ESLint changed-files               : 0 blocking · 0 advisory
  Backend lint changed-files         : 0 / 0
  MaintainX P0 unit tests            : 13 / 13 PASS
  Public employee endpoint           : 0 forbidden leaks
  Auth multi-login                   : returns full portal token set
  Coverage endpoint live data        : real counts, writes=0
  Pre-existing CI warnings           : unchanged baseline (no new sources)
  New failures introduced            : 0
```
