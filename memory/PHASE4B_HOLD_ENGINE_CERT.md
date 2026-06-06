# PHASE 4B — HOLD ENGINE CERTIFICATION

**Phase:** 4B · Hold Engine
**Date:** 2026-02
**Verdict:** 🟢 **PASS**

## Architecture
Single `operational_status` enum extended with `Safety Hold`, `Certification Hold`, `Maintenance Hold` (renamed from Repair). `trench_safety_holds` is **history/audit only** — `operational_status` remains the authoritative state field.

## Priority resolver
```
Safety Hold (100) > Certification Hold (90) > Maintenance Hold (80)
  > Inspection Hold (70) > In Transport (20) > Assigned (10) > Available (0)
```
Implementation: `routes/trench_safety/_helpers.py::resolve_operational_status`. Every write that opens or clears a hold calls `apply_resolved_status(db, asset_id, actor)` which recomputes from open holds and persists via the single mirror path.

## Endpoints
- `GET  /api/trench-safety/assets/{id}/holds` (active_only filter supported)
- `POST /api/trench-safety/assets/{id}/holds` (idempotent open by `(asset_id, kind)`)
- `POST /api/trench-safety/holds/{hold_id}/clear`

## Migration
`seed.py` idempotently rewrites any legacy `operational_status="Repair"` rows (in both `trench_safety_assets` and `equipment_master`) to `"Maintenance Hold"` on every boot. Safe to run repeatedly.

## Tests (all PASS)
- `test_no_assets_carry_legacy_repair_status`
- `test_daily_fail_minor_inspection_hold_only`
- `test_daily_fail_major_creates_repair_stub_and_maintenance_hold`
- `test_daily_fail_critical_creates_safety_hold`
- `test_monthly_pass_clears_inspection_hold`
- `test_monthly_pass_does_not_clear_safety_hold`
- `test_open_and_clear_safety_hold_manually`
- `test_hold_priority_resolver`

## Conclusion
🟢 The hold engine has a single source of truth, idempotent transitions, deterministic priority resolution, and full audit. **NO duplicate status systems exist.**
