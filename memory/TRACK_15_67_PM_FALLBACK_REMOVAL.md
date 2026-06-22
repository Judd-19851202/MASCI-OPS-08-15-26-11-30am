# TRACK 15.67 · Phase 3 · PM Fallback Removal

_Status: ✅ SHIPPED · 2026-06-22_

## Goal
Eliminate the hard-coded 6-PM dictionary in `pm_routing.py` and route
every unresolved PM event to `ADMIN_DEAD_LETTER_TO` with a full audit
trail, so a non-MASCI tenant never silently inherits MASCI office
addresses.

## Changes (`backend/pm_routing.py`)

### `PM_TABLE` — now env-resolved
- Old: hard-coded `{"David Jewett": …, "Chris Wright": …, "Ramon Rodriguez": …, "Jaymn Judd": …}`.
- New: `_resolve_pm_table()` reads `PM_SEED_DIRECTORY` env (format
  `Name|email,Name|email,…`). MASCI defaults returned only when env
  unset AND `tenant_context.is_masci()`. Non-MASCI tenants get an
  empty dict and a `WARNING` log line.

### `ALWAYS_CC` — now env-resolved
- Old: `["jaymn.judd@mascigc.com", "safety@mascigc.com"]`.
- New: `_resolve_always_cc()` reads `COMPLIANCE_ALWAYS_CC` env. MASCI
  default returned only when env unset AND tenant is MASCI.

### `recipients_for_record_async` — dead-letter on unresolved PM
- Old (operational kinds): `to = ["jaymn.judd@mascigc.com"]` when no
  PM resolved.
- Old (compliance kinds): `to = cc[:]; cc = []` (collapsed `ALWAYS_CC`
  into `to`).
- New: `to = await _dead_letter_recipients(db)` — resolves the active
  tenant's `ADMIN_DEAD_LETTER_TO` route doc. Falls back to env
  `ADMIN_DEAD_LETTER_EMAIL` only on MASCI tenant.

### Audit + admin notification
New helper `_audit_dead_letter(db, kind, record, reason)` writes:
1. A `email_routing_audit_v2` row with `route_key="ADMIN_DEAD_LETTER_TO"`,
   `calling_module="pm_routing_dead_letter"`, `status="dry_run"`.
2. A `platform_audit` row with `event="pm_unresolved_dead_letter"` and
   the project number / name for the operator to investigate.

### Sync legacy `recipients_for_record`
- Old: returned `["jaymn.judd@mascigc.com"]` for operational kinds.
- New: returns the tenant-scoped `ALWAYS_CC` (empty for non-MASCI).

## Proof
Second-tenant simulation:

```
pm_table_empty_for_non_masci         PASS  (len=0)
always_cc_empty_for_non_masci        PASS  (len=0)
pm_unresolved_routes_to_dead_letter  PASS  (to=['ops@demo-co.example'])
```

MASCI parity: **19/19** — production MASCI PM routing unchanged.

## 7-workflow verification
| Workflow | Behaviour |
|---|---|
| Site Inspections | ✅ Primary PM + co-PMs + ALWAYS_CC (compliance) |
| Safety Meetings | ✅ Primary PM + co-PMs + ALWAYS_CC (compliance) |
| JHAs | ✅ Primary PM + co-PMs + ALWAYS_CC (compliance) |
| Daily Reports | ✅ Primary PM + co-PMs only (PM-only) |
| Incidents | ✅ Primary PM + co-PMs + ALWAYS_CC (compliance) |
| QAQC | ✅ Routed via standard `pm_routing` path |
| Equipment Pre-Op | ✅ Primary PM + co-PMs only (PM-only) |

For each, an unresolved PM now routes to `ADMIN_DEAD_LETTER_TO` (not
a MASCI office address) AND writes an audit row.
