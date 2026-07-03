# TRACK 19.44 · Project Intelligence · Data Source Map

| Signal | Collection | Query | Fallback |
|---|---|---|---|
| Active projects | `db.jobs_master` (fallback `jobs`, `projects`) | `{"status": {"$in": ["active", "in_progress"]}}` | 0 |
| Daily reports (7d) | `db.daily_reports` | `{"submitted_at": {"$gte": iso_7d_ago}}` | 0 |
| Missing/overdue reports | `db.daily_reports` | `{"status": {"$in": ["missing", "overdue"]}}` | 0 |
| Job photos (7d) | `db.job_photos` | `{"uploaded_at": {"$gte": iso_7d_ago}}` | 0 |
| Open constraints | `db.operational_constraints` | `{"status": {"$in": ["open", "in_progress"]}}` | 0 |
| Aging constraints (>30d) | `db.operational_constraints` | `{"status": open, "opened_at": {"$lt": -30d}}` | 0 |
| Project incidents (7d) | `db.incident_cases` | `{"submitted_at": {"$gte": iso_7d_ago}, "job_number": {"$exists": True, "$ne": None}}` | 0 |
| HIGH-attention cases | `db.incident_cases` | `{"attention_level": "high", "state": {"$ne": "CLOSED"}}` | 0 |
| Open POs (portfolio) | `db.po_requests` | `{"status": {"$in": PO_OPEN_STATUSES}}` | 0 |
| Top-5 by incident volume | `db.incident_cases.aggregate([...])` | `{"$group": {"_id": "$job_number", "count": {"$sum": 1}}}` | empty |

## Deferred

- Schedule status (on-time / off-track) — needs authoritative schedule system.
- QA/QC surface — depends on qa_qc collection landing.
- Weather delay integration — deferred.
