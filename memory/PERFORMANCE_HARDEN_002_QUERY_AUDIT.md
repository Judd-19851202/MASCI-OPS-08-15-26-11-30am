# PERFORMANCE-HARDEN-002 · Phase 2A · Production Query Forensics

```
Environment    : production (masci_safety) + preview cross-check
Access Level   : prod-DB-read (no writes to prod)
Evidence Source: prod-DB explain("executionStats") on canonical query shapes
Confidence     : VERIFIED for every COLLSCAN/IXSCAN classification below
```

---

## §2A.1 · Production volume snapshot (2026-06-09 21:00 UTC · masci_safety)

Top collections by document count:

| Collection | Doc count |
|---|---|
| `integration_sync_logs` | 41,261 |
| `audit_events` | 11,946 |
| `directory_sessions` | 1,949 |
| `motive_events` | 1,620 |
| `session_activity` | 1,062 |
| `job_photos` | 789 |
| `equipment_master` | 470 |
| `employees` | 262 |
| `asset_mappings` | 190 |
| `notifications` | 142 |
| `admin_audit_log` | 142 |
| `daily_reports` | 115 |
| `passkeys_credentials` | 0 |
| `idempotency` | 0 |
| `operational_events` | 0 |

(Lower-volume collections omitted.)

## §2A.2 · Existing index coverage gaps (PROD)

This is the central forensic finding: **the 5 indexes added in the prior PERFORMANCE-HARDEN-002 sprint are present in PREVIEW but NOT yet in PROD**, because they ship via `ensure_safety_indexes` in `server.py` and prod has not been deployed since.

Indexes currently MISSING in prod (will land on next prod deploy):

| Collection | Index | Current state in prod |
|---|---|---|
| `daily_reports` | `id` | ❌ COLLSCAN |
| `daily_reports` | `doc_id` | ❌ COLLSCAN |
| `job_photos` | `id` | ❌ COLLSCAN |
| `motive_events` | `id` | ❌ COLLSCAN |
| `motive_events` | `(event_family, event_at)` compound | ❌ uses event_at only |
| **`directory_sessions`** | **`token`** | **❌ COLLSCAN (NEW this refresh)** |
| **`integration_sync_logs`** | **`(integration, status, started_at)` compound** | **❌ uses integration only (NEW this refresh)** |

## §2A.3 · Canonical query explain results — PROD live

| Query | Stages | docs examined | keys examined | ms |
|---|---|---|---|---|
| `daily_reports.find({"id": "x"})` | **COLLSCAN** | 115 | 0 | 0 |
| `daily_reports.find({"doc_id": "x"})` | **COLLSCAN** | 115 | 0 | 0 |
| `daily_reports.find({"project_number": "21025"}).sort("report_date",-1).limit(50)` | SORT → FETCH → IXSCAN | 0 | 0 | 0 |
| `daily_reports.find({"lifecycle_state","project_number"})` | SORT → FETCH → IXSCAN | 0 | 0 | 0 |
| `job_photos.find({"id": "x"})` | **COLLSCAN** | 789 | 0 | 0 |
| `job_photos.find({"project_number": "21025"}).sort("record_date",-1).limit(100)` | SORT → FETCH → IXSCAN | 0 | 0 | 0 |
| `job_photos.find({"source": "daily_report", "source_id": "x"})` | FETCH → IXSCAN | 0 | 0 | 0 |
| `motive_events.find({"id": "x"})` | **COLLSCAN** | 1,620 | 0 | 1 |
| `motive_events.find({"event_family": $in, "event_at": $gte})` | FETCH → IXSCAN (event_at only) | 1,458 | 1,458 | 3 |
| `integration_sync_logs.find({"integration": "motive"}).sort("started_at",-1).limit(50)` | LIMIT → FETCH → IXSCAN | 52 | 52 | 0 |
| **`integration_sync_logs.find({"integration": "motive", "status": "success"}).sort("started_at",-1).limit(50)`** | LIMIT → FETCH → IXSCAN (integration only) | **41,261** | **41,261** | **125** |
| `audit_events.find({"actor":"admin"}).sort("at",-1).limit(50)` | LIMIT → FETCH → IXSCAN | 1,510 | 1,510 | 2 |
| `user_directory.find({"email": "..."})` | EXPRESS_IXSCAN | 1 | 1 | 0 |
| **`directory_sessions.find({"token": "x"})`** | **COLLSCAN** | **1,949** | **0** | **1** |
| `notifications.find({"recipient_role":"admin","read_at":null}).sort("created_at",-1).limit(50)` | LIMIT → FETCH → IXSCAN | 14 | 14 | 0 |
| `equipment_inspections.find({"equipment_id":"x"}).sort("inspection_date",-1).limit(20)` | LIMIT → FETCH → IXSCAN | 39 | 39 | 6 |

## §2A.4 · Highest-priority targets (evidence-backed)

| # | Pattern | Impact | Source code |
|---|---|---|---|
| 1 | `directory_sessions.find({"token":...})` | COLLSCAN on **EVERY authenticated request** · 1,949 docs scanned/request | `user_directory.py:427` |
| 2 | `integration_sync_logs.find({"integration","status"}).sort.limit(50)` | **125 ms** for filtered queries (41k key scan) | `routes/integrations/logs.py:30` |
| 3 | Prior sprint's 5 indexes (will deploy with code) | COLLSCAN of 115 / 789 / 1,620 docs eliminated | `daily_report_lifecycle.py`, `job_photos.py`, `motive_service.py` |

## §2A.5 · Endpoints NOT touched (intentional — already healthy or out of scope)

- `notifications` (compound `user_id_1_read_at_1_created_at_-1` already optimal)
- `session_activity` (real query is `.find({}).sort("last_seen_at",-1)` which uses TTL `last_seen_at_1` index efficiently)
- `alert_events` (real query is `.find({}).sort("at",-1)` which uses `at_1` index backward direction)
- `admin_audit_log` (write-only in application code — no read paths found, so no index needed)
- `equipment_inspections`, `safety_inspections`, `qaqc_inspections` (low-volume or already indexed)
- `passkeys_credentials`, `webauthn_challenges`, `idempotency` (volume = 0 or TTL-bounded)
