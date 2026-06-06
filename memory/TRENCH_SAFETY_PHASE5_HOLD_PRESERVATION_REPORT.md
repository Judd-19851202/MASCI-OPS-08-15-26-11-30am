# PHASE 5 — HOLD PRESERVATION REPORT

## Mandate
> Do NOT allow movement logic to silently clear holds. An asset on Safety/Certification/Maintenance/Inspection Hold may be physically moved, but it must NEVER be displayed as usable.

## Implementation
Every bridge function:
1. Calls `list_open_holds(asset_id)` first.
2. Sets `has_hold = bool(open_holds)`.
3. Writes **bookkeeping fields only** (location, transfer id, timestamps) if `has_hold`.
4. Conditionally writes `operational_status` only when `not has_hold`.
5. Calls `apply_resolved_status(asset_id, actor)` to re-run the Phase 4B priority resolver.

The Phase 4B resolver enforces:
```
Safety Hold (100) > Certification Hold (90) > Maintenance Hold (80)
   > Inspection Hold (70) > In Transport (20) > Assigned (10) > Available (0)
```
Therefore even if the asset is moved physically, `operational_status` always shows the highest-priority active hold.

## Field experience
| Scenario | What field crew sees on the QR landing |
|----------|----------------------------------------|
| TB-06 on Inspection Hold, transferred Palm Coast Yard → NSB Airport | Status `Inspection Hold` · Location `NSB Airport` · DO-NOT-USE banner |
| TB-04 on Safety Hold, transferred | Status `Safety Hold` · DO-NOT-USE banner (red) |
| Retired asset | bridge writes no status changes; emits `trench_safety_transport_blocked_retired` audit; QR still says Retired |

## Tests
| Test | Outcome |
|------|---------|
| `test_inspection_hold_preserved_through_full_transport_cycle` | ✅ |
| `test_safety_hold_preserved_through_transport` | ✅ |
| `test_cancel_restores_status` | ✅ (verifies clean reset when no hold) |

## Compliance
✅ Hold preservation through every transport transition.
✅ Retired assets cannot be moved back to Available via transport.
✅ Public QR field view continues to show DO-NOT-USE banners across all hold kinds.
