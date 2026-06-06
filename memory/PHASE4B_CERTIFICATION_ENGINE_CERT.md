# PHASE 4B — CERTIFICATION ENGINE CERTIFICATION

**Phase:** 4B · Certification Engine
**Date:** 2026-02
**Verdict:** 🟢 **PASS**

## Architecture
- `db.trench_safety_certifications` — net-new collection.
- Per-asset `requires_certification: bool` flag (default `false`). Fleet is NOT auto-locked (operator-locked decision).
- `recompute_certification_hold(db, asset_id)` runs after every add / update / revoke and on `PUT /assets/{id}` when `requires_certification` changes. It opens or clears the `Certification Hold` via the single hold engine path.
- An expired Active cert is auto-flipped to `status=Expired` during recompute so the derived status is correct.

## Statuses
`Active | Expired | Superseded | Revoked` (collection level)
`OK | Due Soon | Expired | Missing | Not Required` (derived for the asset)

## Kinds
`Manufacturer | Annual Inspection | Engineering Letter | Repair Certification | Special`

## Endpoints
- `GET   /api/trench-safety/assets/{id}/certifications` (status filter)
- `POST  /api/trench-safety/assets/{id}/certifications`
- `PATCH /api/trench-safety/certifications/{cert_id}`
- `POST  /api/trench-safety/certifications/{cert_id}/revoke`

## Tests (all PASS)
- `test_add_cert_within_due_soon_window` (asset enters Certification Hold on expired-only cert)
- `test_add_active_cert_clears_certification_hold`
- `test_disabling_requires_certification_clears_hold`
- `test_fleet_not_auto_locked_on_day_one` (TB-01…TB-07 stay clear of Certification Hold at rest)

## Conclusion
🟢 Certifications flow through a single recompute path; the fleet is not artificially locked; the certification status derivation auto-corrects expired Active rows. **NO duplicate certification systems exist.**
