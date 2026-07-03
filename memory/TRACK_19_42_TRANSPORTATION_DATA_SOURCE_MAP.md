# TRACK 19.42 · Transportation Intelligence · Data Source Map

Every query the aggregator issues, with a fallback statement for
environments where the collection does not exist yet.

| # | Signal | Collection | Query | Fallback |
|---|---|---|---|---|
| 1 | DVIRs submitted last 7d | `db.dvir` | `{"submitted_at": {"$gte": iso_7d_ago}}` | 0 |
| 2 | DVIRs with open defects | `db.dvir` | `{"has_open_defects": True}` | 0 |
| 3 | DVIR total | `db.dvir` | `{}` | 0 |
| 4 | Active driver qualifications | `db.driver_qualifications` | `{"status": {"$in": ["active", "current"]}}` | 0 |
| 5 | Expiring within 30 days | `db.driver_qualifications` | `{"expires_at": {"$lte": +30d, "$gte": now}}` | 0 |
| 6 | Already expired | `db.driver_qualifications` | `{"expires_at": {"$lt": now}}` | 0 |
| 7 | OOS units | `db.equipment_units` | `{"status": {"$in": ["OOS", "Down", "Out of Service"]}}` | 0 |
| 8 | Fleet total | `db.equipment_units` | `{}` | 0 |
| 9 | Vehicles assigned | `db.vehicle_assignments` | `{"active": True}` | 0 |
| 10 | Vehicle accidents last 7d | `db.incident_cases` | `{"incident_type": "vehicle_accident", "submitted_at": {"$gte": iso_7d_ago}}` | 0 |
| 11 | Transportation action backlog | `db.transport_action_items` | `{"status": {"$in": ["open", "in_progress"]}}` | 0 |
| 12 | Top-5 OOS units (Top 5 Items table) | `db.equipment_units` | `{"status": OOS-set}`, `.limit(5)` | empty |

## Fields consumed on `equipment_units` (Top-5 table)

- `unit_number`
- `make`
- `model`
- `status`
- `oos_since`

Missing fields render as `""` (empty string) — never fake values.

## Missing sources · deferred

| Source | Reason | Future track |
|---|---|---|
| **Motive integration** (real-time events) | Requires MOTIVE_EVENT_INTELLIGENCE_MATRIX_AUDIT.md cross-link + de-dupe. | 19.44 |
| **FleetWatcher forensics** (FWA1_FLEETWATCHER_FORENSIC_AUDIT.md) | Separate ingestion pipeline. | 19.44 |
| **Dispatch readiness snapshot** | `dispatch_events` requires sub-day windowing that the digest cadence does not warrant. Surfaced in the Dispatch Command Digest today. | 19.45 |

## Insufficient-data behaviour

If **all** signals return zero, `_agg_transportation_intelligence` calls `insufficient_data_score(...)` — no fabricated score, no fake data, no empty-success. The 14-section layout still renders with canonical empty-state markers everywhere except Score (which is CRITICAL + `insufficient_data`).
