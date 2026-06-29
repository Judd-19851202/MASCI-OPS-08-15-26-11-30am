# Transportation Fleet Adoption · Rollback Procedure

Track 19.02A makes every bulk adoption fully reversible. Rollback is a
single API call and touches **only** the overlays produced by the named
batch — never `equipment_master`, `equipment_units`, maintenance,
documents, Motive, assignments, or other Transportation overlays.

## Endpoint

```
POST /api/admin/transportation/fleet/adoption-bulk/{batch_id}/rollback
Headers: X-Admin-Token: <admin-token>
```

## Behaviour

1. Loads every `transport_trucks` row tagged with
   `bulk_adoption_batch_id = {batch_id}`.
2. Removes those overlay documents.
3. Removes the corresponding `transport_eligibility_state` rows
   (`target_type="truck"`, `target_id in [removed ids]`).
4. Emits an `audit_events` row of kind
   `transport_bulk_adoption_rolled_back` with `entity_id={batch_id}`
   capturing actor / count / request metadata.
5. Returns `{success, batch_id, removed, removed_overlay_ids}`.

## Safety guarantees

* `equipment_master` is **never** touched.
* `equipment_units` is **never** touched.
* Maintenance, Motive, GPS, Documents, Daily Inspections, Driver
  Assignments — **never** touched.
* Leased / owner-operator rows (those without `equipment_id`) are
  **never** removed — they have no `bulk_adoption_batch_id`.
* Single-row adoptions performed via
  `POST /equipment/{id}/adopt` are **never** removed — they have no
  `bulk_adoption_batch_id` either.

## Operator command (curl)

```bash
TOKEN=$(curl -s -X POST "$API/api/auth/multi-login" \
  -H "Content-Type: application/json" \
  -d '{"email":"ops-admin@mascigc.com","password":"…"}' \
  | jq -r '.portal_tokens.admin')

curl -s -X POST \
  "$API/api/admin/transportation/fleet/adoption-bulk/{batch_id}/rollback" \
  -H "X-Admin-Token: $TOKEN" | jq .
```

## Idempotency

Calling rollback on a `batch_id` that has already been rolled back
returns `{success: true, removed: 0, message: "no overlays match this
batch_id"}` — never raises. Verified by
`test_rollback_unknown_batch_id_is_idempotent`.

## Audit trail example

After a successful bulk adoption + rollback:

```
audit_events:
  kind=transport_bulk_adoption_completed   entity_id=<batch_id>  (1 row)
  kind=transport_asset_adopt               entity_id=<truck_id>  (N rows)
  kind=transport_bulk_adoption_rolled_back entity_id=<batch_id>  (1 row)
```

Every event carries `actor`, `ts`, `route`, `ip`, `ua`, `tenant`, and
the relevant change payload.
