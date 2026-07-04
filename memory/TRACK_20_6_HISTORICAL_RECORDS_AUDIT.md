# TRACK 20.6 · Historical Records Audit — Fire Protection

**Question:** Does the existing `entity_kind="asset"` lane (Track 19.61)
support fire-specific paper without modification?

**Answer:** **Almost.** The lane's plumbing (identity fields, cross-lane
guards, approval workflow, upload / approve / audit) is 100% reusable.
The only Phase A extension is **additive record_type slugs** for fire
paper.

## What Track 19.61 already ships

- `ENTITY_KINDS = ("employee", "vendor", "asset")` with cross-lane
  guards.
- `CreateRecordBody.asset_id / asset_unit_number / asset_display_name`.
- `list_records` filters `entity_kind=asset`, `asset_id`,
  `asset_unit_number`.
- Approval branch requiring asset identity + `record_type`.
- Existing asset-lane `record_type` catalog (12 slugs · Track 19.61):
  `warranty` · `purchase_agreement` · `bill_of_sale` ·
  `title_registration` · `insurance_policy` · `calibration_certificate` ·
  `operator_manual` · `spec_sheet` · `historical_inspection_report` ·
  `historical_maintenance_record` · `asset_photo` ·
  `other_asset_document`.

## What's missing for fire protection

The generic slugs above cover 80% of fire paper (e.g. a warranty card
or manufacturer manual fits under `warranty` / `operator_manual`). Five
additional fire-specific slugs are needed for clean classification and
future OCR routing:

| New record_type slug | What it holds |
|---|---|
| `hydrostatic_test_certificate` | Periodic (5-yr / 12-yr) hydro-test certificates for pressurized cylinders. |
| `recharge_service_record` | Post-use or annual recharge service tickets. |
| `fire_ext_annual_service` | Annual professional inspection tag / cert. |
| `fire_ext_manufacturer_doc` | Manufacturer spec / recall notice / bulletin. |
| `fire_ext_retirement_record` | End-of-life record (destroyed / condemned / returned to vendor). |

All are **additive** to `LANE_RECORD_TYPES["asset"]`. Same rules as
Track 19.61: `entity_kind="asset"`, `ownership_lane="asset"`,
approver set unchanged (`{asset_admin, hr, admin}`).

## Zero-Drift accounting

- No new collection.
- No new lane.
- No new approver.
- No new intake route.
- Existing intake UI (`HistoricalRecordsIntake.jsx`) already renders
  whatever `LANE_RECORD_TYPES` returns — a UI refresh isn't required,
  only that the record_type dropdown will show the new slugs.
- Existing approval queue (`HistoricalRecordsQueue.jsx`) is likewise
  data-driven.
- Backwards-compatible: every existing record without these new slugs
  continues to work.

## Sequencing note (why Phase A ships this, not later)

Historical Records is the single place where **legacy paper** lives on
the platform. Fire protection has enormous legacy-paper volume
(hydrostatic certificates, annual service tags, manufacturer bulletins).
Waiting to add these slugs until Phase B would mean HR/Admin cannot
file fire paper properly for the interim — they'd fall back to
`other_asset_document`, losing the ability to filter and route.

Phase A ships the taxonomy AND the historical record_types together.

## What's NOT added

- No email trigger on upload / approval.
- No new OCR classifier — reuses the existing intake pipeline.
- No new PDF renderer.
- No mobile-specific intake.
- No public-form intake.

## Verdict

**The `entity_kind="asset"` lane needs one additive extension** — five
new record_type slugs — to fully support fire-protection historical
paper. Nothing else changes.
