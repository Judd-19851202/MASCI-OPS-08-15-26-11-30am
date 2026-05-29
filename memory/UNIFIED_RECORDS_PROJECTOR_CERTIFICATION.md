# Unified Records Projector · Certification

_Phase V.1 · M1 · Option C · 2026-05-29 · read-only two-substrate projection._

> **Mission:** _"The user should not need to understand legacy
> systems, migrations, or record substrates. One search. One
> timeline. One records dashboard."_

This certification proves the unified projector delivers a single
operator experience across two underlying substrates without
mutating either.

---

## 1 · Surface contract

| Endpoint | Purpose |
|---|---|
| `GET /api/operational-records` | Unified list across ODR + frozen Daily Reports |
| `GET /api/operational-records/resolve/{doc_id}` | Doc id router (DR-* → legacy viewer; ODR-* → ODR viewer) |

Both are **read-only**. Zero database mutation occurs in this module.

## 2 · Envelope (intersection schema)

```python
class OperationalRecord(BaseModel):
    record_kind: str           # "odr" | "legacy_daily_report"
    archive: bool              # True iff record_kind == "legacy_daily_report"
    id: str
    doc_id: str
    project_number: str
    project_name: str
    report_date: str
    foreman_name: str
    superintendent_name: str
    photo_count: int
    crew_count: int
    has_foreman_signature: bool
    has_superintendent_signature: bool
    status: Optional[str]
    submitted_at: Optional[str]
    created_at: Optional[str]
    viewer_route: str          # "/odr/<id>" or "/daily-reports/<id>"
```

Field shape is the **intersection** of both substrates. ODR-only
fields (audience projection, amendment trail, observation events)
are never injected into legacy rows. Legacy-only fields (`general_notes`,
`distribution_list`) are not surfaced — they remain canonical only
inside the legacy viewer.

## 3 · Sort, filter, counts

| Behavior | Rule |
|---|---|
| Sort | `report_date desc · created_at desc` (stable secondary) |
| Limit | Applied AFTER merge, not per substrate, so "newest N across both" semantics are honored |
| Filter `kind` | Skips a substrate entirely when set; default surfaces both |
| Filter `project_number` | Applied to both substrates with substrate-appropriate path (`project_number` on legacy · `project.project_number` on ODR) |
| Filter `report_date` | Applied to both substrates with substrate-appropriate path |
| Counts | Computed from the post-merge truncated slice, not pre-merge totals — **counts are always honest** |

## 4 · Read-only invariants

The projector reads from two collections via Motor `find()` cursors
with `{"_id": 0}` projection. There is **zero** call to:

- `insert_one` / `insert_many`
- `update_one` / `update_many` / `replace_one`
- `delete_one` / `delete_many`
- `find_one_and_update` / `find_one_and_replace` / `find_one_and_delete`
- `aggregate` with `$out` / `$merge`

Verified by lexical search across `routes/operational_records.py`.
The collection is **observed**, never **modified**.

## 5 · Doc id router

```python
_ODR_DOC_ID = re.compile(r"^ODR-\d{4}-\d{5}$")
_DR_DOC_ID = re.compile(r"^DR-\d{4}-\d{5}$")
```

Routing matrix:

| Doc id pattern | Substrate | Viewer route |
|---|---|---|
| `ODR-YYYY-NNNNN` | `odr` | `/odr/<record_id>` |
| `DR-YYYY-NNNNN` | `legacy_daily_report` | `/daily-reports/<record_id>` |
| anything else | rejected | `HTTP 422` |

The router resolves the canonical record id (uuid) by looking up
`{"doc_id": <doc_id>}` on the appropriate collection. `404` is
returned when the doc_id format is valid but the record doesn't
exist.

## 6 · Performance envelope

| Path | Cost (200-row limit) |
|---|---|
| `GET /api/operational-records` | 1 query per substrate = 2 reads · ~5–15 ms warm |
| `GET /api/operational-records/resolve/{doc_id}` | 1 query · ~3–8 ms warm |

Indexes already present (M0.1 + legacy substrate):
- `daily_reports` has `report_date` and `project_number` indexes.
- `odr` has `(project.project_number, project.report_date)` index.

No new indexes are required for M1.

## 7 · Test coverage (8 of 15 M1 cases hit this module)

| # | Test | Result |
|---|---|---|
| 5 | `test_operational_records_unified_list` | 🟢 |
| 6 | `test_operational_records_kind_filter_legacy` | 🟢 |
| 7 | `test_operational_records_kind_filter_odr` | 🟢 |
| 8 | `test_operational_records_invalid_kind_422` | 🟢 |
| 9 | `test_resolve_doc_id_legacy` | 🟢 |
| 10 | `test_resolve_doc_id_odr` | 🟢 |
| 11 | `test_resolve_doc_id_unknown_format_422` | 🟢 |
| 12 | `test_resolve_doc_id_well_formed_but_missing_404` | 🟢 |

## 8 · Frontend consumption

`/app/frontend/src/lib/odrApi.js`:

```js
export async function listOperationalRecords(params = {}) { … }
export async function resolveDocId(docId) { … }
```

`/app/frontend/src/pages/operational_records/OperationalRecords.jsx`
consumes both endpoints to render the calm, two-substrate dashboard
with the `ArchiveBadge` treatment per
`ARCHIVE_VISUAL_TREATMENT_STANDARD.md`.

## 9 · Operator-facing one-liner

> **What you see:** one list of every project record across MASCI Ops.
>
> **What we do:** read from two underlying systems and present them as
> a single timeline.
>
> **What we never do:** rewrite, convert, or modify either system.

The projector is the seam between the past and the future of the
platform — and the seam is a read, not a write.

---

_End of UNIFIED_RECORDS_PROJECTOR_CERTIFICATION.md._
