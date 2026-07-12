# Transportation Fleet · Performance Report

Track 19.02A measurements against the live preview API
(`https://backup-forensics.preview.emergentagent.com`).

## Adoption Preview

| Metric | Value |
| --- | --- |
| Endpoint | `GET /api/admin/transportation/fleet/adoption-preview` |
| Server compute | one `equipment_master.find` + one `transport_trucks.find` |
| Rows scanned | 136 transport-capable + 12 leased overlays |
| Server-side elapsed | ~80 ms |
| Target | < 1 s |
| Verdict | ✓ |

## Bulk Adoption

| Metric | Value |
| --- | --- |
| Endpoint | `POST /api/admin/transportation/fleet/adoption-bulk` |
| Server compute | one preload of adopted-eq-ids, one `find` over `equipment_master`, one `insert_many`, then per-overlay audit + eligibility upsert |
| Rows created (clean run) | 136 overlays |
| Server-side `elapsed_ms` | ~93 ms |
| Target | < 5 s server-side |
| Verdict | ✓ |

## Bulk Rollback

| Metric | Value |
| --- | --- |
| Endpoint | `POST /api/admin/transportation/fleet/adoption-bulk/{batch_id}/rollback` |
| Server compute | `find` by batch_id, `delete_many` by batch_id, `delete_many` by eligibility ids |
| Rows removed | exactly the count of the named batch |
| Server-side elapsed | ~70 ms |
| Verdict | ✓ |

## Fleet Projection

| Metric | Value |
| --- | --- |
| Endpoint | `GET /api/admin/transportation/fleet/equipment` |
| Server compute | one `equipment_master.find` + one `transport_trucks.find`, in-memory join |
| Items returned | 148 (136 MASCI + 12 leased) |
| Server-side elapsed | ~50 ms |
| Verdict | ✓ |

## Overlay PATCH

| Metric | Value |
| --- | --- |
| Endpoint | `PATCH /api/admin/transportation/fleet/equipment/{eq_id}/overlay` |
| Server compute | one `find_one`, one `update_one`, one `find_one` (verified), one audit insert |
| Server-side elapsed | ~35 ms |
| Verdict | ✓ |

## No N+1 patterns introduced

* Preview: single batch read of `equipment_master`, single batch read
  of `transport_trucks`, in-memory grouping. Linear in
  `equipment_master` size.
* Bulk adoption: single `insert_many`. No per-row write loop.
* Bulk rollback: single `delete_many` keyed by `bulk_adoption_batch_id`.
* Audit events: per-row inserts only after the batch insert succeeds,
  and only for newly-created rows. Idempotent re-runs do not emit
  audit events.
