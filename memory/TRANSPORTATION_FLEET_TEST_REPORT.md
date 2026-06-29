# Transportation Fleet · Test Report (Track 19.02A)

## Result

**189 / 189 transportation tests passing.** Zero regressions to Tracks
18.x, 19.00, 19.01, 19.02.

## Track 19.02A test file

`/app/backend/tests/test_track_19_02a_fleet_adoption_hardening.py`
— 21 tests across six concern areas.

### 1 · Preview (read-only)

* `test_preview_is_read_only` — read-only assertion + projection
  unchanged afterwards.
* `test_preview_excludes_passenger_categories` — Pickup Trucks /
  Supervisor / Excavators are NOT in scope.
* `test_preview_anon_rejected` — 401/403 for anonymous.

### 2 · Bulk adoption

* `test_bulk_dry_run_writes_nothing` — dry-run reports `would_create`
  but creates zero overlays.
* `test_bulk_adoption_creates_and_is_idempotent` — re-running creates 0.
* `test_bulk_adoption_dispatch_rejected` — admin-only enforced.
* `test_bulk_adoption_anon_rejected` — 401/403 for anonymous.
* `test_bulk_adoption_no_duplicate_overlays` — uniqueness invariant
  on `equipment_id`.

### 3 · Rollback

* `test_rollback_removes_only_named_batch` — leased rows + projection
  state correct.
* `test_rollback_admin_only` — dispatch rejected.
* `test_rollback_invalid_batch_id` — 422 for too-short batch_id.
* `test_rollback_unknown_batch_id_is_idempotent` — `removed=0`.

### 4 · Overlay PATCH

* `test_overlay_patch_dispatch_can_edit_operational` — operational
  fields persist.
* `test_overlay_patch_protected_field_blocked` — VIN / make /
  engine_hours / category all 422 with `Enterprise…` message.
* `test_overlay_patch_invalid_classification` — enum guard.
* `test_overlay_patch_missing_overlay_404` — must adopt first.
* `test_overlay_patch_anon_rejected` — 401/403 for anonymous.
* `test_overlay_patch_silently_ignores_unknown_fields` — known keys
  applied, unknown keys silently dropped.

### 5 · Audit events

* `test_audit_events_emitted` — verifies all four audit kinds:
  * `transport_asset_adopt` (per overlay)
  * `transport_bulk_adoption_completed` (per batch)
  * `transport_overlay_update` (per PATCH)
  * `transport_bulk_adoption_rolled_back` (per rollback)

### 6 · Performance

* `test_preview_fast` — preview round-trip < 3s.
* `test_bulk_adoption_fast` — server `elapsed_ms` < 5000.

## Regression scope

```
tests/test_track_16_04_transportation_foundation.py          ──  pass
tests/test_track_18_12b_transportation_dispatcher_functionality.py ── pass
tests/test_track_18_12c_transportation_role_permissions.py   ──  pass
tests/test_track_19_00_transportation_driver_carrier_foundation.py ── pass
tests/test_track_19_01_transportation_academy.py             ──  pass
tests/test_track_19_02_transportation_fleet_projection.py    ──  pass
tests/test_track_19_02a_fleet_adoption_hardening.py          ──  pass
```

189 passing · 0 failures.

## Fixture hygiene

The Track 19.02A test fixture `_clean_before_after` removes every
overlay tagged with an `equipment_id` (i.e., MASCI-owned overlays)
before AND after each test. Leased / owner-operator overlays (no
`equipment_id`) are never touched — verified by
`test_rollback_removes_only_named_batch` which asserts
`leased_total >= 1` after rollback.

## Auth fixture retries

Module-scope token fixture wraps `multi-login` with up to 3 retries at
60s timeout to absorb transient preview-URL latency.
