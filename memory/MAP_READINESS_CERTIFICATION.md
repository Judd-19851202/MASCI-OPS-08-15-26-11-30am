# FORGEDOPS · TRUST SPRINT · T4 · MAP READINESS CERTIFICATION

> ⚠️ **PREVIEW ENVIRONMENT** — Audit run against `masci_safety_preview`. Contract behavior is environment-agnostic; counts are preview fixtures.

**Date:** 2026-02-10
**Authorization:** OMEGA — Trust Sprint T4.
**Verdict:** 🟢 **PASS** — `/api/operations-map/contract` is map-ready, honest in every trust state, never synthesizes location, and stamps the environment on every response.

---

## 1 · Endpoint under audit

`GET /api/operations-map/contract`
- Filters: `scope`, `project_number`, `asset_kind`, `asset_family`, `status`, `attention_only`, `limit`.
- Composes Asset Spine + Dispatch Lifecycle + Motive + Shop (fleet_defects + equipment_master.status) + Safety (incidents) + PM project metadata.
- Auth: any portal token (admin, PM, dispatch, shop, safety).
- Environment: stamped on the envelope (`response.environment` = `preview` | `production`).

---

## 2 · Required-field presence (sampled 25-row tests)

| Field | Required? | Present on every row? | Notes |
|---|---|---|---|
| `asset_id` | ✅ | ✅ | from Asset Spine |
| `operational_state` | ✅ | ✅ | `oos` / `in_shop` / `active_haul` / `moving` / `idling` / `available` / `no_telematics` / `assigned` |
| `location_source` | ✅ | ✅ | `motive` / `motive_stale` / `asset_spine_label` / `none` |
| `last_location_time` | ✅ | ✅ (or `null`) | null is honest when no telemetry exists |
| `lat` | ✅ | ✅ (or `null`) | null in preview because Motive isn't connected |
| `lon` | ✅ | ✅ (or `null`) | null in preview |
| `project_number` | ✅ | ✅ (or `null`) | null is honest for assets w/o assignment |
| `assigned_dispatch_id` | ✅ | ✅ (or `null`) | from active assignment join |
| `environment` (envelope) | ✅ | ✅ | `preview` (in this run) |

All required fields are present on every row. Where data does not exist, the field is `null` AND a trust state explains why — **no field is fabricated**.

Verified by tests:
- `test_row_has_identity_bucket`
- `test_row_has_location_bucket_and_trust`
- `test_row_assignment_bucket`
- `test_row_operational_state_bucket`
- `test_row_telematics_bucket`
- `test_row_fleetwatcher_and_maintainx_pending`
- `test_row_attention_bucket_with_route_pending`
- `test_row_trust_bucket`

---

## 3 · "No fake location" gate

Verified by `test_no_fake_lat_lon`:

> When `location_trust_state ∈ {no_gps, no_location, asset_spine_only}` the row's `lat` MUST be `null` AND `lon` MUST be `null`.

Result: **PASS** — for every row in preview where Motive has no telemetry (which is currently every row), `lat`/`lon` are `null` and the trust state is honest.

The contract:
- **Never** uses Asset Spine `current_location` (a string label like "Yard A") as lat/lon.
- **Never** interpolates from neighboring assets.
- **Never** guesses from project geocoding (no project geocoding exists today; if it did, the source would be stamped as `geocoded` with `location_confidence=low`).
- **Never** carries a stale Motive lat/lon into the contract without flagging `last_known_location`.
- **Never** uses demo coordinates.

---

## 4 · Trust states verified

Allowed set (per directive):
```
live_location · last_known_location · no_location · no_gps · not_mapped ·
motive_only · asset_spine_only · fleetwatcher_pending · maintainx_pending ·
no_assignment · no_project · unknown_state · needs_mapping · oos · in_shop ·
failed_dvir · maintenance_hold · active_haul · idle · moving · offline
```

Verified by `test_row_has_location_bucket_and_trust` — every observed `location_trust_state` value is a member of the allowed set.

FleetWatcher slots return `fleetwatcher_status="not_connected"` and every dependent field (`ticket_number`, `material`, `plant`, `source_location`, `destination_location`, `tons`, `load_status`, `cycle_time_minutes`) is `null`. Same pattern for MaintainX (`work_order_id`, `maintenance_status`, `estimated_return`, `repair_priority`).

---

## 5 · Cross-environment leak protection

| Check | Behavior |
|---|---|
| Preview asset appearing in production response | ❌ Cannot — production pod's `DB_NAME` ≠ `masci_safety_preview` |
| Production asset appearing in preview response | ❌ Cannot — preview pod cannot reach production DB namespace |
| `?project_number=ZZ-NONEXISTENT-99999` | ✅ Returns `{counts.total_rows: 0, rows: []}` — verified by `test_filter_project_number` |
| Empty-scope PM (no assigned projects) hitting `?scope=pm` | ✅ Returns empty envelope — code path `_empty_envelope()` exercised |

---

## 6 · Edge-case row coverage (preview-sampled)

Confirmed by spot-checking the live preview response:

| Edge case | Row shape | Trust signal |
|---|---|---|
| Unknown location (no telemetry, no label) | `lat=null · lon=null · location_label=null` | `trust_state=no_location` · `gps_status=no_gps` |
| Missing GPS (motive_id present, no event) | `lat=null · lon=null` | `trust_state=no_gps` |
| Missing assignment | `assigned_dispatch_id=null · project_number=null` | `dispatch_state=no_assignment` · `availability_state=available` |
| Out-of-service asset | `shop_state=oos` | `operational_state=oos` · attention `severity=high` |
| Asset in shop (defects open) | `shop_state=open_defect` · `defect_count>0` | `operational_state=in_shop` · attention `severity=high` or `medium` |
| Unmapped (no motive_truck_id, family=fleet) | `gps_status=no_gps` · `missing_fields=[motive_truck_id]` | attention `Map Asset → /admin/asset-spine` |

All edge cases honestly classified. **No row was silently re-synthesized to look "live" when it wasn't.**

---

## 7 · Performance smoke

`test_contract_returns_under_10s_for_1k_rows` — preview response with `limit=1000` returns in well under the 10s budget on shared preview infra.

No N+1 queries: all joins (assignments, motive events, defects, incidents, project meta) are bulk-loaded once before the row builder runs.

---

## 8 · PASS / FAIL

🟢 **PASS** — endpoint is map-ready, honest, environment-stamped, and resilient to every edge case requested.

🟡 **Live `lat`/`lon` data does not exist in preview** (Motive is not connected). This is the correct behavior for preview, not a defect. When Motive (or FleetWatcher) activates in production, the same code path will surface real coordinates immediately — no schema change required.

---

## 9 · Deliverable

- This certification: `/app/memory/MAP_READINESS_CERTIFICATION.md`
- Endpoint code: `/app/backend/routes/operations_map_contract.py`
- Test suite: `/app/backend/tests/test_operations_map_contract_phase_5a.py` (~30 cases)
