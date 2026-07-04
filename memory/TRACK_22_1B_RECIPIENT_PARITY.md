# TRACK 22.1B · Recipient Parity Report

## Certification statement

Recipient resolution is 100% delegated to `pm_routing.recipients_for_record_async(db, record, kind)` and, for equipment-inspection, `shop_users.list_shop_users(db, only_active=True)` + `email_routing.get_value(db, "shop_manager_fallback")` + `pm_routing._dead_letter_recipients(db)`.

**None** of those modules were touched in Track 22.1B. **None** of the callers of those modules were touched (the caller lives inside `_dispatch_auto_email`, which is locked by SHA-256 bytecode fingerprint).

## Invariants preserved (proven by bytecode fingerprint + unchanged pm_routing module)

| Property | Preserved by |
|---|---|
| Recipient count | `pm_routing.recipients_for_record_async` (unchanged) |
| Recipient ordering | `dist["all"]` list-cast (unchanged) |
| Always-CC application | `pm_routing.ALWAYS_CC` (unchanged) |
| PM_ONLY_KINDS filter | `pm_routing.PM_ONLY_KINDS` (unchanged) |
| Compliance kinds | `pm_routing.COMPLIANCE_KINDS` (unchanged) |
| Portal rules | `pm_routing` (unchanged) |
| Disabled recipients | `pm_routing._dead_letter_recipients` + `shop_users.list_shop_users(only_active=True)` (unchanged) |
| Test recipients | `pm_routing` (unchanged) |
| Approval routing | `pm_routing` (unchanged) |
| Executive routing | `pm_routing` (unchanged) |
| PM routing | `pm_routing.recipients_for_record_async` (unchanged) |
| Safety routing | `pm_routing.recipients_for_record_async` (unchanged) |
| HR routing | `pm_routing.recipients_for_record_async` (unchanged) |
| Shop Manager override (`equipment-inspection`) | Same 30-line block inside `_dispatch_auto_email` (bytecode-locked) |
| Severe-incident CC fan-out | Same 10-line block inside `_dispatch_auto_email` (bytecode-locked) |
| Dead-letter fallback + `email_routing_v2.write_audit` for `PRE_OP_FAIL_FALLBACK` | Same 20-line block inside `_dispatch_auto_email` (bytecode-locked) |
| Case-insensitive dedupe (`x.lower() not in {y.lower() ...}`) | Same 2-line dedupe inside `_dispatch_auto_email` (bytecode-locked) |

## What CI enforces

- `test_dispatcher_bytecode_matches_fingerprint` — any edit to the recipient-resolution block inside `_dispatch_auto_email` changes the compiled bytecode and fails CI.
- `test_email_dispatch_module_exists_with_expected_symbols` — ensures the extracted helpers exist under the expected names.
- `test_runtime_snapshot_zero_drift` — proves dependency chain equality across all 1,440 routes; if any handler suddenly gained a `pm_routing.*` dependency (or lost one), the assertion fails.

## Verdict

🟢 **RECIPIENT PARITY CERTIFIED.** Every knob that affects recipient resolution lives outside this track's scope and was not touched. The dispatcher body that consumes them is locked at the bytecode level.
