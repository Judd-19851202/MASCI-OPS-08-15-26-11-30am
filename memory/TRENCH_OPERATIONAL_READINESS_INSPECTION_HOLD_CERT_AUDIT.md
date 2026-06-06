# TRENCH SAFETY · OPERATIONAL READINESS AUDIT — INSPECTION / HOLD / CERTIFICATION

**Mode:** VERIFY ONLY
**Date:** 2026-02
**Verdict:** 🟢 PASS

## Inspection types — all wired

`routes/trench_safety/_models.py::INSPECTION_TYPES` =
- Daily Visual ✅
- Monthly Competent Person ✅
- Annual Review ✅
- Special Inspection ✅
- Damage Inspection ✅
- Return Inspection ✅

Endpoint: `POST /api/trench-safety/assets/{id}/inspections` (safety_or_admin auth).

## Severity matrix — operator-locked behavior

| Result | Severity | Holds opened | Repair stub | Alert kind | Evidence test |
|--------|----------|--------------|-------------|------------|----------------|
| Pass | * | — (Monthly/Annual Pass clears Inspection Hold) | — | hold_cleared | `test_daily_pass_no_hold`, `test_monthly_pass_clears_inspection_hold` |
| Fail | None / Minor | Inspection Hold | — | failed_inspection | `test_daily_fail_minor_inspection_hold_only` |
| Fail | Major | Inspection Hold + Maintenance Hold | ✅ Open `repair_recommendation` | failed_inspection | `test_daily_fail_major_creates_repair_stub_and_maintenance_hold` |
| Fail | Critical | Safety Hold + Inspection Hold + Maintenance Hold | ✅ Open | critical_damage | `test_daily_fail_critical_creates_safety_hold` |

## Pass-clears-hold rule — preserved

Confirmed in `inspections.py`: a Pass result on **Monthly Competent Person** OR **Annual Review** with `competent_person_confirmed=true` calls `clear_hold(kind="Inspection Hold")`. Daily Visual Pass does NOT clear an Inspection Hold (correct per directive).

Evidence: `test_monthly_pass_clears_inspection_hold` ✅, `test_monthly_pass_does_not_clear_safety_hold` ✅ (Safety Hold survives a monthly pass).

## Certification model

`db.trench_safety_certifications`:
- Kinds: Manufacturer / Annual Inspection / Engineering Letter / Repair Certification / Special.
- Status: Active / Expired / Superseded / Revoked.
- Endpoints: list / add / patch / revoke — all require safety_or_admin.

## `requires_certification` per-asset flag — fleet not auto-locked

- Default `false`. TB-01…TB-07 ship with `requires_certification=false`.
- Verified live: `test_fleet_not_auto_locked_on_day_one` ✅ — no asset enters Certification Hold without an explicit flag.
- Toggling `requires_certification=true` on an asset with no active cert → opens Certification Hold (test `test_add_cert_within_due_soon_window`).
- Adding a fresh non-expired cert → clears Certification Hold (`test_add_active_cert_clears_certification_hold`).
- Toggling flag back to `false` → clears Certification Hold (`test_disabling_requires_certification_clears_hold`).

## Auto-correction
`recompute_certification_hold` sweeps any Active cert past its `expires_at` and flips its `status` to `Expired` before recomputing the derived asset state. Prevents false-positive "OK" certification status when an Active doc has gone stale.

## Verdict
🟢 **PASS — inspection, severity matrix, hold engine, and certification flow certified as operator-locked.**
