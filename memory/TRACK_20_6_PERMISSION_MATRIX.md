# TRACK 20.6 · Permission Matrix — Fire Protection

**Doctrine:** The Fire Protection promotion is a **view layer**
extension of the Asset Thread. It grants no new access. Safety keeps
inspection ownership. HR/Admin keeps historical-records ownership.
Admin keeps master ownership.

Role tokens used below (matching prior 20.x tracks):
**HR/Admin · Admin · Executive · Shop · Fleet · Dispatch · Trans ·
Transportation · Safety · PM · Field · Public.**

| Section / Data | HR/Admin | Admin | Executive | Shop | Fleet | Dispatch | Trans | Transportation | Safety | PM | Field | Public |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Extinguisher identity (unit_id / type / size / location) | R | R | R | R | R | R | R | R | R/W | R | R (own vehicle) | — |
| Assignment to parent asset (`equipment_master_id`) | R | R | R | R | R | R | R | R | R/W | R | R (own) | — |
| Location kind / value | R | R | R | R | R | R | R | R | R/W | R | R (own) | — |
| Last inspection date | R | R | R | R | R | R | R | R | R/W | R | R (own) | — |
| Next-due date | R | R | R | R | R | R | R | R | R/W | R | R (own) | — |
| Pass/fail status | R | R | R | R | R | R | R | R | R/W | R | R (own) | — |
| Inspection history | R | R | R | R | R | R | R | R | R/W | R | R (own) | — |
| Recharge / hydrostatic history (Phase A: HR historical lane) | R/W | R | R | R | R | R | R | R | R | R | R (own) | — |
| Attachments (photos · certs) | R | R | R | R | R | R | R | R | R/W | R | R (own) | — |
| Corrective Actions linked (`fire_ext` link type) | R | R | R | R | R | R | R | R | R/W | R | R (own) | — |
| Operational signal `fire_ext.fail` | R | R | R | R | R | R | R | R | R/W (emit) | R | R (own) | — |
| Digest KPI `fire_extinguishers_overdue` | R | R | R | R | R | R | R | R | R/W (Safety digest) | R | — | — |
| Asset Thread render (Phase A read-side) | R | R | R | R | R | R | R | R | R (via Safety Portal preferred) | R | R (own) | — |

Legend: **R** = read · **R/W** = create/update in own lane · **—** = no
access.

## What Phase A DOES NOT change

- **Safety** remains the sole author of extinguisher inspections and
  identity in Phase A. Zero widening.
- **Admin** does NOT gain write access to `db.fire_extinguishers` in
  Phase A — the Safety Portal remains authoritative.
- **PM · Field · Superintendent** remain read-only, scoped to own
  crew's vehicles / trailers / projects, as they already are.
- **Executive** remains read-only.
- **Transportation** remains read-only. Note: some DOT trucks have
  federally required extinguishers — Transportation should be able to
  see (existing right) but not author (existing restriction).
- **Public** has zero access.

## What Phase B WOULD adjust (recorded for continuity — NOT Phase A)

- **Admin** would gain the ability to author the extinguisher's
  canonical `equipment_master` row (identity only) once migration
  lands. Safety would still own the inspection.
- Two-writer model: Admin (identity) + Safety (inspection). Same as
  every other asset in the platform.

## Cross-lane guards enforced on the Historical Records extension

- Fire-specific record_types (`hydrostatic_test_certificate`,
  `recharge_service_record`, `fire_ext_annual_service`,
  `fire_ext_manufacturer_doc`, `fire_ext_retirement_record`) live only
  under `entity_kind="asset"` and `ownership_lane="asset"`.
- HR / Admin approvers for the `asset` lane are unchanged (Track 19.61
  set: `{asset_admin, hr, admin}`).
- Safety cannot author historical records (existing rule).

## Verdict

**No permission widening.** Phase A promotes only the render / read
surface. Phase B (later) reallocates identity authorship between Admin
and Safety with matching guards, but that is NOT part of Track 19.62.
