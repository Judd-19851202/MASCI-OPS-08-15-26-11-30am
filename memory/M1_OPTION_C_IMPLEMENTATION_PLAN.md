# M1 · Option C · Implementation Plan & Closure

_Phase V.1 · 2026-05-29 · authorized closure of M1 under Option C._

> **Operator authorization (verbatim):** _"OPTION C APPROVED. Frozen
> Archive + Forward-Only ODR + Unified Read Experience. REJECTED:
> Option B Historical Conversion. No historical Daily Reports will be
> converted into ODR records. No signature re-attestation. No enum
> guessing. No historical record mutation. No historical truth
> rewriting."_

This document records what M1 actually shipped under that
authorization, and the explicit invariants that were preserved.

---

## 1 · Authorized scope (only these · nothing else)

| # | Move | Status |
|---|---|---|
| 1 | Daily Report write freeze | ✅ Shipped |
| 2 | Unified operational records projector | ✅ Shipped |
| 3 | Legacy record routing | ✅ Shipped |
| 4 | `operational_links` bridge (target-only) | ✅ Shipped |
| 5 | Archive visual indicators | ✅ Shipped |
| 6 | Read-only historical preservation | ✅ Verified (zero mutation) |

## 2 · What each move actually does

### 2.1 Daily Report write freeze (`/app/backend/routes/daily_reports.py`)

| Endpoint | Pre-M1 | Post-M1 |
|---|---|---|
| `POST /api/daily-reports` | Created a new daily_report row | **`410 Gone`** with redirect copy `"Daily Reports are now Operational Daily Records. Please use the ODR substrate to file today's record."` and `redirect_to: "/odr/new"` |
| `DELETE /api/daily-reports/{id}` | Hard-deleted the row | **`410 Gone`** with `"Daily Reports are preserved as the historical record. Hard delete is no longer permitted. Records remain accessible read-only."` |
| `GET /api/daily-reports` | Listed reports | **Unchanged** — historical archive remains queryable forever |
| `GET /api/daily-reports/{id}` | Single record fetch | **Unchanged** |
| `GET /api/daily-reports.csv` | CSV export | **Unchanged** |
| Project / superintendent / safety / public PDF read endpoints | Read-only | **Unchanged** |

The freeze uses HTTP `410 Gone` (not `403 Forbidden`) because the
intent is not "you can't do this" — it is "this resource has moved."
The redirect copy is calm and operational, never punitive.

### 2.2 Unified operational records projector (`/app/backend/routes/operational_records.py`)

New module · 100% read-only.

```
GET /api/operational-records
GET /api/operational-records/resolve/{doc_id}
```

- Merges ODR substrate + frozen `daily_reports` into a single
  normalized envelope (`OperationalRecord` Pydantic model).
- Each row carries `record_kind ∈ {odr, legacy_daily_report}` and
  `archive: bool`.
- Field shape is the **intersection** of both substrates. ODR-only
  fields (audience projection, amendment trail) are never injected
  into legacy rows.
- Sort: report_date desc · stable secondary by created_at.
- Filters: `kind`, `project_number`, `report_date`, `limit`.
- Counts honest: returned counts are computed from the post-merge
  truncated slice, not pre-merge totals.

### 2.3 Legacy record routing

```
GET /api/operational-records/resolve/{doc_id}
```

Classifies the doc_id by regex (`ODR-YYYY-NNNNN` vs `DR-YYYY-NNNNN`)
and returns the correct viewer route:

- `ODR-*` → `/odr/<id>` (ODR Detail viewer)
- `DR-*` → `/daily-reports/<id>` (legacy viewer)

Users never need to know which viewer to open.

### 2.4 `operational_links` bridge (target-only)

`/app/backend/routes/operational_links.py`:

- `legacy_daily_report` added to `ARTIFACT_TYPES` (line ~67).
- New constant `TARGET_ONLY_ARTIFACT_TYPES = {"legacy_daily_report"}`.
- `_validate_relationship` enforces: any link with
  `source_type ∈ TARGET_ONLY_ARTIFACT_TYPES` is rejected with
  HTTP 422 and a doctrine pointer to
  `OPERATIONAL_LINKS_BRIDGE_CERTIFICATION.md`.
- ODR rows (and any other source) may freely reference legacy rows.

### 2.5 Archive visual indicators (frontend)

- `/app/frontend/src/components/odr/ArchiveBadge.jsx` — single
  source of archive visual treatment (slate · uppercase · calm · no
  warning colors). Includes a sister `ArchiveExplainerCard` for the
  dashboard header.
- `/app/frontend/src/pages/operational_records/OperationalRecords.jsx` —
  unified dashboard. Search · project filter · kind filter (All / ODR /
  Archive). Each row links to its viewer route.
- `/app/frontend/src/lib/odrApi.js` — adds `listOperationalRecords()`
  + `resolveDocId()` thin clients.
- `App.js` route: `/operational-records`.

### 2.6 Read-only historical preservation

The pytest case `test_legacy_row_byte_count_stable_after_freeze`
proves the row count of `daily_reports` is stable across:
- a 410 POST attempt,
- a 410 DELETE attempt,
- repeated GETs against the unified projector.

No code path in M1 mutates the legacy substrate. The only mutation
permitted to `daily_reports` is the historic write/delete behavior
that has now been frozen (returns 410). The collection is otherwise
treated as read-only.

## 3 · What was explicitly NOT done (per directive)

| Prohibited action | Status |
|---|---|
| Convert legacy reports | ❌ NOT DONE |
| Rewrite signatures | ❌ NOT DONE |
| Remap signed content | ❌ NOT DONE |
| Infer missing enums | ❌ NOT DONE |
| Alter historical PDFs | ❌ NOT DONE |
| Move historical photos | ❌ NOT DONE |
| Regenerate historical audit trails | ❌ NOT DONE |
| Create historical ODR records | ❌ NOT DONE |
| Migration script | ❌ NOT WRITTEN |
| Dual-write surface | ❌ NOT BUILT |

**Zero lines of code mutate the legacy substrate.** Verified by
explicit row-count test.

## 4 · Tests shipped (`/app/backend/tests/odr/test_m1_option_c.py`)

15 cases · all green · 4.6 s runtime.

| # | Test | Verifies |
|---|---|---|
| 1 | `test_daily_report_post_returns_410` | Cutover invariant: POST always 410 |
| 2 | `test_daily_report_delete_returns_410` | Hard delete forbidden |
| 3 | `test_daily_report_get_list_still_works` | Read paths live |
| 4 | `test_daily_report_csv_export_still_works` | CSV export live |
| 5 | `test_operational_records_unified_list` | Both substrates in one merged list |
| 6 | `test_operational_records_kind_filter_legacy` | `kind=legacy_daily_report` filter |
| 7 | `test_operational_records_kind_filter_odr` | `kind=odr` filter |
| 8 | `test_operational_records_invalid_kind_422` | Invalid kind rejected |
| 9 | `test_resolve_doc_id_legacy` | DR-* routes to legacy viewer |
| 10 | `test_resolve_doc_id_odr` | ODR-* routes to ODR viewer |
| 11 | `test_resolve_doc_id_unknown_format_422` | Unknown format rejected |
| 12 | `test_resolve_doc_id_well_formed_but_missing_404` | 404 on absent record |
| 13 | `test_link_legacy_as_target_allowed` | ODR → legacy_daily_report (references) allowed |
| 14 | `test_link_legacy_as_source_blocked_422` | legacy_daily_report → anything blocked |
| 15 | `test_legacy_row_byte_count_stable_after_freeze` | **Zero-mutation invariant** |

## 5 · Cumulative test surface · 67 pytest · 0 fails

| Suite | Result |
|---|---|
| M0.1 substrate | 🟢 12 / 12 |
| M0.2 + M0.2A engines | 🟢 24 / 24 |
| M0.3 operator surfaces | 🟢 7 / 7 |
| M0.4 photo embedding | 🟢 9 / 9 |
| **M1 Option C (this wave)** | 🟢 **15 / 15** |
| Public link continuity probe `--gate` | 🟢 0 fail · 0 warn |
| Bilingual probe `--gate` | 🟢 0 fail |

## 6 · Stop condition (per directive)

🛑 **HALTED at end of M1 closure.**

- ❌ NO pilot rollout begun
- ❌ NO RFI / Schedule / P6 work
- ❌ NO new architecture or governance layers added
- ❌ NO production deploy beyond preview cutover
- ✅ Awaiting operator authorization for the next wave (pilot or M2).

## 7 · Reversibility

If M1 ever needs to be rolled back, it is a 4-line revert:

- Restore the original `create_daily_report` body in `daily_reports.py`
  (the original implementation is preserved in
  `_legacy_create_daily_report_archived` for reference).
- Restore the original `delete_daily_report` body.
- Remove `legacy_daily_report` from `ARTIFACT_TYPES` and
  `TARGET_ONLY_ARTIFACT_TYPES`.
- Drop the `/api/operational-records` route registration in `server.py`.

The unified projector is purely additive; removing it does not
affect any other surface.

---

_End of M1_OPTION_C_IMPLEMENTATION_PLAN.md._
