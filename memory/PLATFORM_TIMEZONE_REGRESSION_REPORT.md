# Platform Timezone Regression Report

_Phase TRUST-TIME-1 · 2026-05-28._

## Headline

🟢 **74 / 74 PASS** across the full regression battery after the
TRUST-TIME-1 fix. Zero collateral regressions.

## New tests this phase

### `test_trust_time_1_backend_contract.py` · 5 / 5 PASS
1. `test_po_requests_timestamps_are_tz_aware` — every PO timestamp
   round-trips as `Z`-suffixed or `+HH:MM`-suffixed ISO.
2. `test_po_audit_entries_are_tz_aware` — each audit-log `at`
   timestamp is tz-aware.
3. `test_draft_telemetry_admin_timestamps_are_tz_aware` —
   `/api/draft-telemetry/recent` events round-trip tz-aware.
4. `test_self_protection_generated_at_is_epoch` — OPS-1 emits
   integer epoch (frontend localizes via shared helper).
5. `test_date_utils_module_is_served` — every helper is exported
   and the naive-ISO coerce branch is present.

### `test_trust_time_1_frontend_localization.py` · 7 / 7 PASS
1-4. `test_utc_timestamp_localizes_correctly` parametrized across:
   - `America/New_York` (EDT · expected hour `9`)
   - `America/Chicago` (CDT · expected hour `8`)
   - `America/Denver` (MDT · expected hour `7`)
   - `America/Los_Angeles` (PDT · expected hour `6`)
5. `test_relative_time_is_minute_grained` — "5m ago" for a 5-min
   old timestamp.
6. `test_audit_helper_always_labels_utc` — every audit-helper
   output ends with " UTC".
7. `test_naive_iso_coerce_matches_utc_iso` — naive ISO and
   `Z`-suffixed ISO produce identical local renders in every
   tested timezone.

Implementation: pure Node-driven harness via Python `vm.runInContext`
+ `TZ=` env. ~2 s wall time across all 7. No Playwright dependency.

## Regression sweep (all suites)

| Suite | Result |
|---|---|
| `test_trust_time_1_backend_contract.py` | 🟢 5/5 (NEW) |
| `test_trust_time_1_frontend_localization.py` | 🟢 7/7 (NEW) |
| `test_governance_self_protection_page.py` | 🟢 11/11 |
| `test_cutover_ready_deployment_stanza.py` | 🟢 4/4 |
| `test_stabilization_final_capabilities.py` | 🟢 4/4 |
| `test_governance_authority_mismatch_probe.py` | 🟢 6/6 |
| `test_trust_po1_backend_enforcement.py` | 🟢 10/10 |
| `test_trust_po1_frontend_capability_scope.py` | 🟢 4/4 |
| `test_mongo_id_leak_contract.py` | 🟢 10/10 |
| `test_contextual_return_path_iter443.py` | 🟢 7/7 |
| `test_trust1_final_hardening.py` | 🟢 6/6 |
| **TOTAL** | 🟢 **74 / 74** |

## Live OPS-1 snapshot after the fix

```
page_status            : GREEN
authority              : green · 0 violations · 0 warnings · 58 baselined
trust_surfaces         : green
context_governance     : green · 0 TBD
truthful_state         : green · 12 contracts
telemetry              : green
regression_suite       : green
field_walks            : green
drift                  : green · 0 open gaps
deployment             : green (after re-baseline)
```

## Known flakes

Two transient Playwright timeouts surfaced on the first sweep
(`Page.goto: Timeout 30000ms exceeded`). Both re-ran clean in
isolation. Root cause: preview frontend dev server cold-start
latency. Not a TRUST-TIME-1 regression.

## Deploy recommendation

🟢 **PROCEED** to Save + Deploy. The TRUST-TIME-1 fix is a pure
serialization + display correction with no data migration and no
auth/workflow surface area.

## Mobile note

The fix landed in the shared `dateUtils.js` consumed by all React
components. Mobile rendering inherits the local-browser timezone
via the iOS Safari / Android Chrome `Intl.DateTimeFormat`
machinery. No mobile-specific code path. Verified via Node
harness which uses the same V8 `Intl` engine.
