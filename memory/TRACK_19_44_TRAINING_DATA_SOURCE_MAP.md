# TRACK 19.44 · Training Intelligence · Data Source Map

| Signal | Collection | Query | Fallback |
|---|---|---|---|
| Active employees | `db.employees` (fallback `employee_records`) | `{"active": True}` | 0 |
| Completions (7d) | `db.safety_training_records` (fallback `training_track_records`) | `{"completed_at": {"$gte": iso_7d_ago}}` | 0 |
| Total training records | `db.safety_training_records` | `{}` | 0 |
| Expired certifications | `db.driver_qualifications` | `{"expires_at": {"$lt": now}}` | 0 |
| Expiring 30d | `db.driver_qualifications` | `{"expires_at": {"$lte": +30d, "$gte": now}}` | 0 |
| Expiring 60d | `db.driver_qualifications` | `{"expires_at": {"$lte": +60d, "$gte": now}}` | 0 |
| Meetings (7d) | `db.safety_meetings` (fallback `meetings`) | `{"held_at": {"$gte": iso_7d_ago}}` | 0 |
| Missing records | `db.training_track_records` | `{"status": {"$in": ["missing", "pending"]}}` | 0 |
| Pending approval | `db.training_track_records` | `{"status": "pending_approval"}` | 0 |
| Top-5 expired certs | `db.driver_qualifications` | `{"expires_at": {"$lt": now}}, .limit(5)` | empty |

## Fields consumed on Top-5

- `employee_name` (fallback `employee_id`)
- `cert_type`
- `expires_at`

## Deferred

- Attendance rosters (per meeting) — future track.
- Recognition/awards — future track.
- Employee 360 integration — future track.
