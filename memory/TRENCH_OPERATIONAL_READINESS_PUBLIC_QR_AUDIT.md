# TRENCH SAFETY · OPERATIONAL READINESS AUDIT — PUBLIC SAFETY TILE / QR FIELD VIEW

**Mode:** VERIFY ONLY
**Date:** 2026-02
**Verdict:** 🟡 **PASS with one minor advisory (P3 — non-blocking)**

## Public endpoints — live evidence

### `GET /api/trench-safety/public/overview` (no auth)
Returned shape:
```json
{
  "total_active_assets": 7,
  "counts_by_status": {"Available": 7, "Assigned": 0, "In Transport": 0, "Inspection Hold": 0, "Repair": 0},
  "counts_by_type":   {"Trench Box": 7, "End Panel": 0, "Spreader Bar": 0, "Hydraulic Shore": 0, "Slide Rail System": 0, "Trench Jack": 0, "Ladder": 0, "Accessory": 0}
}
```
- Counts only — **no asset IDs, no PII, no admin data leaked**. ✅
- 🟡 **ADVISORY:** `counts_by_status` retains the legacy `"Repair"` key and does NOT include the new Phase 4B hold kinds (`Maintenance Hold`, `Safety Hold`, `Certification Hold`). Assets in those states are simply not counted in the dashboard rollup — they still appear individually via QR lookup. Effect: dashboard headline counts may under-count holds. **Non-blocking** for Phase 6 (no security or safety implication). Recommended cleanup at next portal polish pass.

### `GET /api/trench-safety/public/assets/TB-07` (no auth)
Verified keys exposed (no admin / PII leaks):
- `asset_id`, `asset_type`, `size`, `color`, `condition`
- `operational_status`, `current_location`, `current_project_name`
- `last_inspection_at`, `next_inspection_due`, `certification_expires_at`
- `missing_serial_number`, `needs_review`, `tabulated_data_missing`
- `manufacturer`, `model`, `rated_depth_ft`, `rated_soil_type`
- `qr_url`

Confirmed **NOT exposed**: `updated_by`, `created_by`, `assigned_by`, `current_superintendent`, `current_foreman`, `notes`, `internal_*` fields. ✅

### `POST /api/trench-safety/public/damage-report`
Anonymous field damage reporting endpoint present (Phase 3.5).

### `GET /api/trench-safety/public/scan` (QR scan event recording)
Phase 3.5 endpoint present.

## Field-view DO-NOT-USE banner — extended coverage (Phase 4B)

`pages/trench_safety/TrenchSafetyQrLanding.jsx::HOLD_STATUSES`:
- Inspection Hold ✅
- Maintenance Hold ✅
- Certification Hold ✅
- Safety Hold ✅

Each maps to a status-specific message:
| Hold | Field-view banner |
|------|-------------------|
| Inspection Hold | "This asset is on Inspection Hold. A competent person must clear it before use." |
| Maintenance Hold | "This asset is under Maintenance. It is not available for the field." |
| Certification Hold | "This asset's required certification is missing or expired. DO NOT USE." |
| Safety Hold | "SAFETY HOLD — critical condition reported. DO NOT USE. Contact Safety immediately." |

Confirmed via test `test_public_lookup_reflects_new_hold_kinds`.

## Field-user decision support (six core questions)

| Question | Where answered |
|----------|----------------|
| What asset is this? | `asset_id`, `asset_type`, `size`, `color` |
| What size is it? | `size` |
| Is it safe to use? | `operational_status` + DO-NOT-USE banner |
| Is it on hold? | `operational_status ∈ HOLD_STATUSES` |
| Is tabulated data available? | `tabulated_data_missing` flag + tabulated data tile in QR landing |
| How do I report a problem? | "Report Issue" CTA → `POST /public/damage-report` |

## Spanish parity
All hold-related strings have Spanish entries (verified in `lib/i18n.js`). Field crew running Spanish locale sees the DO-NOT-USE banner translated. See SPANISH audit doc.

## Verdict
🟡 **PASS with one P3 advisory** — public surface is field-safe, no admin actions exposed, no PII leakage. The `counts_by_status` rollup needs an opportunistic refresh to count the new hold kinds — non-blocking for Phase 6 start.
