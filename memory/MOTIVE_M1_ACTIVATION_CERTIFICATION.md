# M-1 Motive Activation — Certification

**Date:** 2026-06-08
**Sprint:** M-1 (Motive live-data activation)
**Status:** ✅ GREEN — live data flowing into MASCI schemas, signed webhooks routing, Integration Center UI hydrated.

---

## What changed (subtractive · OMEGA-compliant)

Two files touched, no new portals, no schema changes:

1. `/app/backend/services/motive_service.py`
   - Replaced placeholder `_write_sync_log` with the canonical schema
     (`integration_sync_logs` with `started_at` / `completed_at` /
     `records_*` / `status` ∈ {Success, Partial, Failed}) so the
     existing Integration Center sync-log table renders correctly.
   - After every sync, stamp `last_sync_at` /
     `last_successful_sync_at` / `last_failed_sync_at` on
     `integration_settings` so the overview tile and `/api/integrations/health`
     reflect reality.
   - Added `_asset_mapping_defaults()` and `_employee_mapping_defaults()`
     so newly-discovered Motive rows match the canonical schema
     produced by the CSV import path (`masci_*` placeholders +
     `maintainx` block + `active` / `mapping_confidence`). Existing
     rows backfilled in place via one-shot `update_many`.

2. `/app/backend/routes/integrations/wizard.py`
   - Made the existing-mapping lookup defensive
     (`mm.get("masci_equipment_id")` + filter empty) so legacy /
     auto-discovered docs don't crash the wizard preview endpoint.
     No behaviour change for mapped rows.

No frontend changes. No new endpoints. No new collections.

---

## Live verification — preview env

| Step | Endpoint | Result |
| --- | --- | --- |
| Connectivity | `POST /api/admin/integrations/motive/test` | `ok=true · status=live · vehicle_locations probe returned 1 row` |
| Sync vehicles + asset gateway | `POST /api/admin/integrations/motive/sync-assets` | 190 updated · 0 errors |
| Sync drivers | `POST /api/admin/integrations/motive/sync-users` | 65 updated · 0 errors |
| Sync geofences | `POST /api/admin/integrations/motive/sync-geofences` | 67 updated · 0 errors |
| Sync events (GPS backfill) | `POST /api/admin/integrations/motive/sync-events` | 90 created · 0 errors |
| Health card hydrate | `GET /api/integrations/health` | `asset_mappings_total=191 · employee_mappings_total=65` |
| Webhook signed | `POST /api/integrations/motive/webhook` (HMAC valid) | `stored=true · event_kind=vehicle_gps · vehicle_id=1438259` |
| Webhook bad sig | `POST /api/integrations/motive/webhook` (bad HMAC) | `HTTP 401 · Invalid webhook signature` |

Sync log rows (`integration_sync_logs`, freshly written):
```
sync_events          Success    C=90  U=0   F=0  by=admin
sync_geofences       Success    C=0   U=67  F=0  by=admin
sync_users           Success    C=0   U=65  F=0  by=admin
sync_assets          Success    C=0   U=190 F=0  by=admin
```

---

## Regression suite

| Suite | Result |
| --- | --- |
| `test_integrations_iter122.py` | ✅ pass |
| `test_iter123_mappings_wizard.py` | ✅ pass (was failing with `KeyError: 'masci_equipment_id'` before wizard.py defensive fix + backfill) |
| `test_integration_health_iter142.py` | ✅ pass |
| `test_iter132_final.py` | ✅ pass |
| `test_dispatch_d1_activation.py` | ✅ pass |
| `test_dispatch_d2_sms_magic_link.py` | ✅ pass |
| `test_iter251_fleet_ops_foundation.py` | ✅ pass |

Pre-existing failures (NOT caused by M-1, confirmed by stash-and-retest;
deferred per OMEGA):
- `test_iter286_driver_qualification_foundation::test_section_keys_present_with_expected_kinds`
- `test_iter286_driver_qualification_foundation::test_all_dq_tips_use_hr_or_admin_scope_only`
- `test_trench_safety_phase2::test_dashboard_seed_data` (stale fixture)

---

## Credentials (preview · `integration_settings` row, operator-managed)

- `provider=motive` · `status=Connected` · `enabled=true`
- `api_key_value` ends in `5fe6` (full key: `56239d0d-3c26-4cef-8d15-3e56ec685fe6`)
- `webhook_secret_value` ends in `c106` (full secret: `004350ccc20b4851b20ca7f5b0bfc106`)
- Webhook URL path: `/api/integrations/motive/webhook`
- Signature header: `X-Motive-Signature` — HMAC-SHA256 hex of the raw body using the webhook secret.

Operator can rotate either secret from `/admin/integrations` → Motive tile → PATCH; nothing else touches the value.

---

## Out of scope (deferred per OMEGA)

- **M-2** Webhook event-type router → Dispatch transitions
- **M-3** Geocode `jobs_master` + plant/yard addresses
- **Phase 4** Production post-deploy verification
- `test_trench_safety_phase2::test_dashboard_seed_data` cleanup
- iter286 DQ scope tests
