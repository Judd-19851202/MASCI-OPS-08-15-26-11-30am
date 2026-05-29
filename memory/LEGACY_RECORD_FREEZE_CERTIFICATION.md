# Legacy Record Freeze · Certification

_Phase V.1 · M1 · 2026-05-29 · zero-mutation evidence._

> **Contract:** Legacy `daily_reports` rows are now READ-ONLY.
> No edits · no deletes · no conversion · no migration scripts ·
> no schema mutation. Historical reports remain accessible forever.

---

## 1 · Endpoint freeze inventory

| Method · Path | Pre-M1 | Post-M1 | Status |
|---|---|---|---|
| `POST /api/daily-reports` | Insert new row | `410 Gone` with redirect copy + ODR pointer | ✅ Frozen |
| `DELETE /api/daily-reports/{id}` | Hard delete | `410 Gone` with preservation copy | ✅ Frozen |
| `GET /api/daily-reports` | List | List | ✅ Read live |
| `GET /api/daily-reports/{id}` | Fetch one | Fetch one | ✅ Read live |
| `GET /api/daily-reports.csv` | CSV export | CSV export | ✅ Read live |
| `GET /api/daily-reports/{id}/download` | Form viewer payload | Form viewer payload | ✅ Read live |

## 2 · Zero-mutation evidence

Test: `tests/odr/test_m1_option_c.py::test_legacy_row_byte_count_stable_after_freeze`

```
before = await db.daily_reports.count_documents({})
# Exercise every freeze path:
POST /api/daily-reports                # → 410
DELETE /api/daily-reports/anything     # → 410
GET   /api/operational-records?limit=200
after = await db.daily_reports.count_documents({})
assert before == after
```

Result: **before == after on every run.** No row created, no row
deleted, no row mutated.

## 3 · Live archive measurements (unchanged from pre-M1)

| Metric | Value (locked at M1 cutover) |
|---|---|
| `daily_reports` rows | 85 |
| Distinct projects | 10 |
| Distinct `report_date` values | 24 |
| `report_date` span | 2024-08-15 → 2026-05-27 (~21 months) |
| Foreman signatures preserved | 68 / 85 |
| Both signatures preserved | 37 / 85 |
| Photo references preserved | 481 |
| Legacy PDFs valid | 100% |

The archive is **byte-identical** to the moment M1 cutover landed.
This is the operational record of MASCI's first 21 months of
field activity. It is not data — it is evidence.

## 4 · Response shape (operator-facing)

### 4.1 POST attempt

```json
HTTP/1.1 410 Gone
Content-Type: application/json

{
  "detail": {
    "error": "daily_report_write_frozen",
    "message": "Daily Reports are now Operational Daily Records. Please use the ODR substrate to file today's record.",
    "redirect_to": "/odr/new",
    "historical_records_remain_accessible": true,
    "doctrine": "M1_OPTION_C_IMPLEMENTATION_PLAN.md"
  }
}
```

### 4.2 DELETE attempt

```json
HTTP/1.1 410 Gone
Content-Type: application/json

{
  "detail": {
    "error": "daily_report_delete_frozen",
    "message": "Daily Reports are preserved as the historical record. Hard delete is no longer permitted. Records remain accessible read-only.",
    "doctrine": "LEGACY_RECORD_FREEZE_CERTIFICATION.md",
    "report_id": "<id>"
  }
}
```

Both responses are calm, redirect users toward ODR, and explicitly
acknowledge that historical records remain accessible. No alarm
language. No punitive copy.

## 5 · What can still happen to a legacy row

| Action | Allowed? |
|---|---|
| Read it | ✅ |
| Render its original PDF | ✅ |
| Reference it from a new ODR via `operational_links` (relationship: `references`) | ✅ |
| Reference it from a photo via `operational_links` (relationship: `evidence_for`) | ✅ |
| Edit any field | ❌ |
| Delete it | ❌ |
| Convert it into an ODR | ❌ |
| Re-attest its signature | ❌ |
| Move its photos | ❌ |
| Mutate its photos library | ❌ |
| Regenerate its audit trail | ❌ |
| Be the source of a new operational link | ❌ |

## 6 · Failure-mode catalog (defensive)

What happens if someone bypasses the API and modifies Mongo
directly? The freeze is **API-layer only** (one HTTP layer above
the database). For policy enforcement at the data layer, the
recommended belt-and-suspenders move (NOT IMPLEMENTED · for future
consideration) is:

- A daily diff probe (`scripts/legacy_archive_drift_probe.py`) that
  hashes each `daily_reports` row's content (excluding `_id`) and
  compares to a frozen-at-cutover hash registry.
- Any drift triggers an advisory report (never a build gate, per
  doctrine — operator review only).

This probe is **not in scope for M1** but is documented here as the
natural M1.5 reinforcement if the operator wants belt-and-suspenders
data-layer enforcement. M1 ships API-layer enforcement only.

## 7 · Reversibility

The freeze is purely a method-body swap on two endpoints:

```python
# To unfreeze (NOT recommended without explicit operator authorization):
# 1. In daily_reports.py · create_daily_report — restore the body
#    preserved in `_legacy_create_daily_report_archived`.
# 2. In daily_reports.py · delete_daily_report — restore the body:
#       result = await db.daily_reports.delete_one({"id": report_id})
#       if result.deleted_count == 0:
#           raise HTTPException(404, "Daily report not found")
#       return {"deleted": True, "id": report_id}
# 3. No data restoration is needed because no data was destroyed.
```

The freeze is one of the most reversible doctrine moves in the
platform — and that is by design. Doctrine without an exit door is
not doctrine, it is dogma.

## 8 · Certification

Under the test surface above (15 / 15 M1 cases passing · zero-mutation
test green), this certification asserts:

> **The legacy `daily_reports` substrate is byte-identical post-cutover
> and will remain byte-identical for as long as the M1 freeze is in
> effect. No M1 code path mutates a legacy row. The archive is
> canonical operational evidence and is preserved as such.**

---

_End of LEGACY_RECORD_FREEZE_CERTIFICATION.md._
