# TRACK 19.43 · Fleet Intelligence · Data Source Map

| Signal | Collection | Query | Fallback |
|---|---|---|---|
| Total fleet | `db.equipment_master` (fallback `equipment_units`) | `{}` | 0 |
| OOS units | `db.equipment_units` | `{"status": {"$in": ["OOS", "Down", "Out of Service"]}}` | 0 |
| Active safety holds | `db.asset_holds` | `{"hold_type": "safety", "status": "active"}` | 0 |
| Active maint/repair holds | `db.asset_holds` | `{"hold_type": {"$in": ["maintenance", "repair"]}, "status": "active"}` | 0 |
| Open defects | `db.fleet_defects` | `{"status": {"$in": ["open", "in_progress"]}}` | 0 |
| Critical defects | `db.fleet_defects` | `{"severity": "critical", "status": {"$in": ["open", "in_progress"]}}` | 0 |
| Inspections last 7d | `db.equipment_inspections` | `{"submitted_at": {"$gte": iso_7d_ago}}` | 0 |
| Overdue inspections | `db.equipment_inspections` | `{"next_due_at": {"$lt": now}, "status": {"$in": ["due", "scheduled"]}}` | 0 |
| Transfers last 7d | `db.equipment_transfers` | `{"created_at": {"$gte": iso_7d_ago}}` | 0 |
| Equipment incidents last 7d | `db.incident_cases` | `{"incident_type": "equipment_damage", "submitted_at": {"$gte": iso_7d_ago}}` | 0 |
| Top-5 safety-hold rows | `db.asset_holds` | `{"hold_type": "safety", "status": "active"}, .limit(5)` | falls back to Top-5 OOS |

## Deferred sources

- MaintainX integration — separate track.
- FleetWatcher forensics — Track 19.44.
- Utilisation metrics (engine hours) — Track 19.45+ once Motive events land.
