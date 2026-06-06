# TRENCH SAFETY · OPERATIONAL READINESS AUDIT — LIFECYCLE

**Mode:** VERIFY ONLY · evidence from existing pytest suite (no new tests, no writes)
**Date:** 2026-02
**Verdict:** 🟢 PASS

## Full lifecycle proof — existing tests cover every state transition

| Lifecycle step | Covered by | Result |
|----------------|------------|--------|
| Available → Assigned (via Phase 4A) | `test_assign_propagates_superintendent_foreman_to_asset_and_deployment` | ✅ |
| Available → Assigned (via Phase 5 dispatch receive) | `test_receive_to_project_updates_status_and_project` | ✅ |
| Assigned → In Transport | `test_in_transit_marks_trench_asset_in_transport` | ✅ |
| In Transport → Delivered (project) | `test_receive_to_project_updates_status_and_project` | ✅ |
| In Transport → Delivered (yard) | `test_receive_to_yard_clears_project_and_marks_available` | ✅ |
| Inspection Fail → Inspection Hold | `test_daily_fail_minor_inspection_hold_only` | ✅ |
| Returned → Available | `test_return_clears_current_project_fields` | ✅ |
| In Transport cancel → restored | `test_cancel_restores_status` | ✅ |

## Hold priority resolver — proof points

| Hold tier | Beats lower tiers | Evidence |
|-----------|-------------------|----------|
| Safety Hold | beats Cert / Maint / Inspection / Transport / Assigned / Available | `test_hold_priority_resolver`, `test_safety_hold_preserved_through_transport` |
| Certification Hold | beats Maint / Inspection / Transport / Assigned / Available | `test_add_cert_within_due_soon_window`, `test_hold_priority_resolver` |
| Maintenance Hold | beats Inspection / Transport / Assigned / Available | `test_daily_fail_major_creates_repair_stub_and_maintenance_hold` |
| Inspection Hold | beats Transport / Assigned / Available | `test_daily_fail_minor_inspection_hold_only`, `test_inspection_hold_preserved_through_full_transport_cycle` |

## Hold preservation across movement
- `test_inspection_hold_preserved_through_full_transport_cycle` — Inspection Hold survives in-transit AND receive.
- `test_safety_hold_preserved_through_transport` — Safety Hold survives both transitions; public QR still shows Safety Hold.

## Retired asset guard
Implemented in `_helpers.resolve_operational_status` (early return if `Retired`) AND the transport bridge guard. Retired assets cannot become Available via movement.

## Pytest snapshot
```
74 / 74 PASS  (Phase 2: 28 · 4A: 16 · 4B: 20 · 5: 10)  ── 2m44s on the live preview backend
```

## Verdict
🟢 **PASS — full lifecycle, hold-priority resolver, and hold preservation certified.**
