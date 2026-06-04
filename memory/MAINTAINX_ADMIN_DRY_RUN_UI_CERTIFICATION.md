# MAINTAINX · ADMIN DRY-RUN UI CERTIFICATION

**Date:** 2026-06-04 18:50 UTC
**Sprint:** OMEGA — MaintainX Admin Integration Center
**Scope:** Certify the in-browser dry-run flow against the 12 validation requirements in the OMEGA directive.

---

## 1 · The dry-run flow

1. Admin navigates to `/admin/integrations`.
2. Selects the **MaintainX · Read-First** tab.
3. Reads the **Configuration** card — confirms API key presence, base URL, kill-switch states.
4. Optionally clicks **Test Connection** — receives a structured pass/fail.
5. Clicks **Run Dry-Run** (no save) OR **Run + Save Report** (one append-only write to `maintainx_dryrun_reports`).
6. Reviews the 11-cell counter grid + the green "Writes performed during this run" panel showing all-zero counters across the operational collections.
7. Latest saved reports are listed below for audit history.

No other action is possible on this screen. No create / update / delete buttons exist.

---

## 2 · Validation matrix (12 requirements)

| # | Requirement | Verdict | Evidence |
| --- | --- | --- | --- |
| 1 | Full API key never appears in frontend | PASS | Live HTML scrubbed — `LEAKS_FOUND = []`; the only key-related field shown is `api_key_masked` returned by backend, which is `••••••••1234` form |
| 2 | Full API key never appears in logs | PASS | Backend only logs `mask_key(api_key)`; route logs never include the bearer; tests `test_api_key_masked_everywhere` verifies the rule at the `public_view()` boundary |
| 3 | Missing key state displays cleanly | PASS | Live: `KEY_STATUS = 'No — set MAINTAINX_API_KEY in env'`; XCircle icon; safety status pill renders amber "API key not configured" message |
| 4 | Test connection handles missing key | PASS | Live: `TEST_RESULT = 'Failed · missing_api_key' / 'MAINTAINX_API_KEY not set'`; structured pill rendered (not raw error JSON) |
| 5 | Test connection handles invalid key | PASS (mocked) | Backend unit test `test_invalid_key_returns_401_classified` returns `{ok:false, code:"unauthorized", status:401}` which the UI already renders via the `mx-p0-test-result` pill |
| 6 | Dry-run works with no writes | PASS | Live: `WRITES = 'MaintainX: 0 · equipment_master: 0 · asset_mappings: 0 · fleet_defects: 0'`; the green "Writes performed" panel surfaces this directly to the admin |
| 7 | Write flags remain false | PASS | Live: `WRITE_FLAG = 'FALSE — SAFE'`, `SYNC_FLAG = 'FALSE — SAFE'` (both rendered with emerald pills; would flip red/amber if changed) |
| 8 | No MaintainX writes occur | PASS | `writes_performed.maintainx == 0` after dry-run; backend client's `create/update/delete_asset` raise `MaintainxWriteDisabled` (unit-tested) |
| 9 | No MASCI equipment writes occur | PASS | `writes_performed.equipment_master == 0`; backend dry-run pipeline only calls `find()` against `equipment_master`; unit-tested in `test_dryrun_no_writes_when_save_false` |
| 10 | Admin-only access enforced | PASS | All four backend routes use `Depends(require_admin)`; the tab itself is mounted inside `<AdminShell>` which sits behind the `/admin/*` gate in `App.js` |
| 11 | Existing MaintainX backend tests still pass | PASS | `python -m pytest tests/test_maintainx_p0_read_first.py -q` → **13 passed in 0.29s** |
| 12 | UI renders cleanly | PASS | Screenshot at `/tmp/mx_p0.png` shows a clean tab inside the existing Admin Integration Center; no console errors; tab content selectors confirmed (`mx-p0-root`, `mx-p0-safety-banner`, all card test-ids present) |

---

## 3 · data-testid surface (for QA)

| Test-id | Element |
| --- | --- |
| `ic-tab-maintainx-p0` | New tab trigger |
| `mx-p0-root` | Tab content root |
| `mx-p0-safety-banner` | "Writes are disabled" banner |
| `mx-p0-config-card`, `mx-p0-config-refresh` | Configuration card + refresh button |
| `mx-p0-key-status`, `mx-p0-key-masked`, `mx-p0-base-url` | Config rows |
| `mx-p0-sync-flag`, `mx-p0-write-flag`, `mx-p0-env-safety` | Flag pills + env safety rollup |
| `mx-p0-test-card`, `mx-p0-test-btn`, `mx-p0-test-result` | Test Connection card |
| `mx-p0-dryrun-card`, `mx-p0-dryrun-btn`, `mx-p0-dryrun-save-btn` | Dry-Run controls |
| `mx-p0-dryrun-result`, `mx-p0-counter-{key}`, `mx-p0-writes-verified`, `mx-p0-run-id` | Dry-Run result panel |
| `mx-p0-reports-card`, `mx-p0-reports-refresh`, `mx-p0-reports-list`, `mx-p0-reports-empty`, `mx-p0-report-row-{id}` | Saved Reports card |

---

## 4 · Verdict — Admin Dry-Run UI

```
ADMIN DRY-RUN UI  :  CERTIFIED

  All 12 validation requirements                  : PASS
  Live preview functional                         : PASS
  Existing backend tests still green (13/13)      : PASS
  No secret data in DOM                           : VERIFIED
  No write paths exposed                          : VERIFIED
  data-testid coverage for QA                     : COMPLETE
```
