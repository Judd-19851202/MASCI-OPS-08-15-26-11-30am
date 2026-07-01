# TRACK 19.11 MAIN · Equipment Pre-Op · Fail Cascade Protection Matrix

**Status:** ✅ GREEN · Every fail-cascade / safety gate / audit trail preserved.

The Track 19.11 MAIN modernization is a **frontend-only UX refactor**. Not a single fail-cascade / safety gate / notification route / PDF template / email template / audit event has been touched. This document is the explicit preservation matrix.

## Camera Obstruction Safety Gate (Track 19.09)

| Surface | Preserved |
|---|---|
| `data-testid="equipment-camera-gate"` container | ✅ |
| `camera-system-yes` / `camera-system-no` / `camera-system-unsure` testIds | ✅ |
| `camera-clear-yes` / `camera-clear-no` testIds | ✅ |
| `camera-obstruction-block` red panel | ✅ |
| `camera-obstruction-note` textarea | ✅ |
| Hard-block submit rule when `camera_system_present === "yes" && camera_obstructions_clear === "no"` | ✅ |
| Bilingual "Clear the obstruction before operating…" message | ✅ |
| Payload keys `camera_system_present`, `camera_obstructions_clear`, `camera_obstruction_note` | ✅ |

## Critical Fluid + Major Safety OOS Modal

| Surface | Preserved |
|---|---|
| `criticalFluidAlert` state | ✅ |
| `data-testid="critical-fluid-modal"` | ✅ |
| `data-testid="critical-fluid-acknowledge"` acknowledge button | ✅ |
| `CRITICAL_FLUID_ITEMS` set (24 items) | ✅ |
| `MAJOR_OUT_OF_SERVICE_ITEMS` set (~40 items) | ✅ |
| `isOutOfServiceItem(item)` classifier | ✅ |
| Fluid-vs-major variant messaging | ✅ |
| Submit-blocking on any OOS item marked FAIL | ✅ |
| Instant modal on FAIL tap for critical/major items | ✅ |
| Bilingual OOS strings (`Unit is OUT OF SERVICE`, `Stop — Critical Fluid Failure`, etc.) | ✅ |

## FAIL Description + Photo Gating

| Surface | Preserved |
|---|---|
| FAIL requires ≥10-char description | ✅ |
| FAIL requires attached photo | ✅ |
| Live `failGating` `useMemo` computes `needPhoto`, `needNote`, `blocked` | ✅ |
| Sticky Submit button disabled when `failGating.blocked === true` | ✅ |
| Descriptive helper text ("N FAIL needs description" / "N FAILs need photos") | ✅ |
| Bilingual strings for gating messages | ✅ |

## Submit → Payload → Route → Downstream

| Surface | Preserved |
|---|---|
| POST `/api/equipment-inspections` route | ✅ |
| Payload keys unchanged (project_name, project_number, location, inspection_date, inspection_time, operator_name, operator_id, equipment_type, equipment_unit, equipment_make, equipment_model, equipment_serial, hour_meter, odometer, checklist, fail_count, pass_count, na_count, deficiency_notes, corrective_actions, out_of_service, camera_*, photos, operator_signature, inspection_sections, submit_language) | ✅ |
| Bilingual translation-on-submit (`translateUserInput`) | ✅ |
| Bilingual sidecar (`persistBilingualSidecar`) | ✅ |
| Signature validation | ✅ |
| Success toast with FAIL count | ✅ |
| Public-mode navigation to `/thank-you` | ✅ |
| Admin-mode navigation to `/equipment/{id}` | ✅ |

## Track 19.08 Snapshot Lock

The audit-snapshot backstop (`SNAPSHOT_ROUTES_MIN = 900`, `SNAPSHOT_COLLECTIONS_MIN = 140`, `CRITICAL_BACKEND_ROUTES`) remains fully GREEN. Track 19.11 MAIN's 67 lock assertions include an explicit test asserting the snapshot constants are unchanged.

## Trust-Spine

The audit-event pipeline is a backend concern; Track 19.11 MAIN is 100% frontend. No audit event schema changed. No audit event emitter changed. Enforced by the "no new backend files touched" test in the Track 19.11 MAIN lock suite.

## Notifications / Emails / PDFs

Not touched. All three pipelines are backend concerns triggered by the successful POST that Track 19.11 MAIN preserves verbatim. The 19.08 snapshot lock guarantees routes still exist.

## Doctrine

**A modernization that weakens a fail-cascade is not a modernization; it is a regression.**

Track 19.11 MAIN is a UX modernization: less noise, clearer flow, richer help, better review-before-submit. Zero compromise on the safety gates that already save operators from harm.
