# PRODUCTION ASSET METADATA POLICY

**Date**: 2026-02-12 · **Mode**: closure

---

## POLICY

Production asset metadata MUST fall into one of these four states:

1. **VERIFIED_INVENTORY** — imported from MASCI master inventory CSV/Excel with operator audit trail.
2. **VERIFIED_TABULATED_DATA** — manufacturer + model + rated values cross-referenced with vendor tabulated-data sheet (PE-stamped or manufacturer-published).
3. **ADMIN_ENTERED** — entered through the admin UI with operator identity + timestamp + reason.
4. **NEEDS_VERIFICATION** — explicitly marked as unverified (production rule engine still operates; UI surfaces the unverified state to Safety).

**Production must never display unverified values as verified.**

---

## CURRENT SCHEMA — FIELDS ALREADY PRESENT (verified in `db.trench_safety_assets`)

The current schema already supports the required tracking surface. No new fields strictly required.

| Field | Purpose | Already on documents? |
|---|---|---|
| `metadata_backfilled_from` | Provenance tag for backfilled rows (e.g. `"FV-7.1A"`) | ✅ |
| `metadata_backfilled_at` | UTC ISO timestamp of backfill | ✅ |
| `manufacturer` | Carries transparent placeholder `"MASCI Field Inventory · pending tabulated-data verification"` when not verified | ✅ |
| `needs_review` | Boolean — flagged on unknown-size assets | ✅ |
| `needs_review_reason` | Free-text reason | ✅ |
| `updated_at` · `updated_by` | Audit on edit | ✅ via admin endpoint |

### Mapping to the 4 policy states

| State | How a record is recognised |
|---|---|
| **VERIFIED_INVENTORY** | `metadata_backfilled_from` is absent AND `manufacturer` is non-placeholder AND `needs_review != true` |
| **VERIFIED_TABULATED_DATA** | manufacturer + model + `rated_depth_ft` all present AND `metadata_backfilled_from` is absent OR explicitly cleared by operator |
| **ADMIN_ENTERED** | `updated_by` set AND admin endpoint audit entry exists |
| **NEEDS_VERIFICATION** | `metadata_backfilled_from == "FV-7.1A"` OR `needs_review == true` OR `manufacturer` contains `"pending tabulated-data verification"` |

---

## PRODUCTION INVARIANTS

1. **No FV-7.1A backfill on production by default.** Enforced by guard in `/app/backend/scripts/fv7_1a_asset_metadata_backfill.py` (see SEED_PROTECTION_CERTIFICATION.md).
2. **If a production asset is in `NEEDS_VERIFICATION` state, the UI must show it as such.** Existing UI surfaces (`ExcavationOversight.jsx`, `PublicExcavationForm.jsx`) display the manufacturer string verbatim — so the `"pending tabulated-data verification"` label is already visible.
3. **Rule engine still fires on `NEEDS_VERIFICATION` assets** so safety is never silently degraded. Verified — the FV-7 deterministic flag engine ignores verification status and reads only `rated_depth_ft`, `dimensions`, etc.

---

## PRODUCTION DATA-IMPORT PATH (no code change required · operator playbook)

| Asset class | Required production source | Operator action |
|---|---|---|
| Trench Boxes (7 real units · TB-01..TB-07) | `routes/trench_safety/seed.py::_SEED_ASSETS` | Already real. Operator should verify `rated_depth_ft` against actual manufacturer data and overwrite via admin endpoint before going live. |
| Road Plates | none in seed code · operator import only | Operator imports real plate inventory via admin endpoint or CSV (production import path). NO road plates ship from seed. |
| Employees | `/app/backend/data/employees_seed.json` | Already real MASCI roster. Operator may overwrite per-row. |
| Projects · Jobs | `projects.py` + `jobs_master.json` | Already real. |
| Competent Persons | none in seed · admin endpoint `PUT /api/admin/employees/{id}/cp-designation` | Operator designates real CPs after first boot. |

---

## VERDICT

# **PASS**

* Production policy defined and enforceable with EXISTING schema (no new fields required).
* `NEEDS_VERIFICATION` state is mechanically detectable via existing `metadata_backfilled_from` + manufacturer string + `needs_review` fields.
* Production cannot accidentally inherit preview's transparent placeholder labels: the backfill script is now guarded (refuses to run on production without explicit operator override).
* Real MASCI inventory ships from boot seeds; placeholder rows do not.
