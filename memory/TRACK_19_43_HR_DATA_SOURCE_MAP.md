# TRACK 19.43 · HR Intelligence · Data Source Map

| Signal | Collection | Query | Fallback |
|---|---|---|---|
| Active employees | `db.employees` (fallback `employee_records`) | `{"active": True}` | 0 |
| New hires (7d) | `db.employee_lifecycle_events` | `{"event_type": "hired", "occurred_at": {"$gte": iso_7d_ago}}` | 0 |
| Exits (7d) | `db.employee_lifecycle_events` | `{"event_type": {"$in": ["terminated", "resigned"]}, "occurred_at": {"$gte": iso_7d_ago}}` | 0 |
| Expired qualifications | `db.driver_qualifications` | `{"expires_at": {"$lt": now}}` | 0 |
| Expiring in 30d | `db.driver_qualifications` | `{"expires_at": {"$lte": +30d, "$gte": now}}` | 0 |
| Training activities (7d) | `db.training_hits` | `{"created_at": {"$gte": iso_7d_ago}}` | 0 |
| Orientations active | `db.employee_lifecycle_events` | `{"event_type": "orientation_started", "status": "in_progress"}` | 0 |
| Top-5 expired quals | `db.driver_qualifications` | `{"expires_at": {"$lt": now}}, .limit(5)` | empty |

## Field consumption on Top-5 rows

- `employee_name` (fallback `employee_id`)
- `cert_type`
- `expires_at`

## Note

`driver_qualifications` is used as the canonical training/certification collection (per Track 19.00 audit). Future track may split into `employee_qualifications` if HR wants a scope broader than driver-restricted certs.
