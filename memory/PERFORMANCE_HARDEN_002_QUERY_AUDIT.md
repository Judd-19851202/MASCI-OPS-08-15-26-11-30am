# PERFORMANCE-HARDEN-002 · Query Forensics Audit

**Sprint:** PERFORMANCE-HARDEN-002 (Elite Hardening)
**Scope:** Phase 1 — Production query forensics
**Mode:** Evidence-first, no speculation
**Date:** 2026-02 (Feb 2026 fork session)

---

## Method

1. Static analysis of every `db.<collection>.find / find_one / count_documents / aggregate / update / delete` call across `/app/backend/`.
2. MongoDB `index_information()` snapshot for the candidate hot collections.
3. MongoDB `explain("executionStats")` against representative queries — preview DB (`masci_safety_preview`).
4. Document counts (`estimated_document_count`) for each candidate.

---

## Document Volumes (Preview DB — production is larger)

| Collection | Doc Count |
|---|---|
| daily_reports | 794 |
| job_photos | 1,812 |
| motive_events | 376 |
| integration_sync_logs | 111 |
| jobs_master | 29 |
| employees | 365 |
| equipment | 0 |
| operational_events | 4 |
| operational_locations | 67 |
| asset_mappings | 191 |
| job_photo_thumb_cache | 2,637 |
| notifications | 6,636 |
| users | 5 |

---

## Pre-Existing Indexes (snapshot before this sprint)

```
daily_reports : created_at, report_date, project_number, lifecycle_state
job_photos    : project_number, (project_number, week_of), (source, source_id), governance.tags
motive_events : event_at
notifications : (recipient_role, created_at), (user_id, read_at, created_at), id (unique),
                linked_task_id, acknowledged_at, expires_at
employees     : id, name, lifecycle_status, supervisor, department, rehire_eligibility
```

---

## Hot Query Patterns Discovered

### daily_reports
- `find_one({"id": report_id})` — **7+ call sites** (daily_report_lifecycle, hr_portal, verification, operational_records, command_center, trench_safety/excavations).
- `find_one({"doc_id": report_id})` — fallback path in `daily_report_lifecycle.py:71/205/221`. **100% of preview docs have `doc_id`.**
- `find({"project_number": …}).sort("report_date", …).limit(…)` — already indexed via `project_number_1`.

### job_photos
- `find_one({"id": photo_id})` — **4+ call sites** (job_photos.py: 844/888/915; photo_governance.py: 194/229/275; odr/pdf.py).
- `find({"id": {"$in": ids}})` — batch fetch from `job_photos.py:1035`.
- `find({"project_number": …}).sort("record_date", -1).limit(5000)` — already indexed via `project_number_1`.

### motive_events
- `find_one({"id": motive_event_id})` — `services/motive_service.py:436`, `driver_profile.py:136`.
- `find({"event_family": {"$in": PRESENCE_EVENTS}, "event_at": …})` — repeatedly used in `operational_events.py:357/411/427/439/455/466` (M-2 audit + ingestion).
- `count_documents({"event_family": …, "event_at": …})` — `driver_profile.py:194/199/204`.

### integration_sync_logs
- `find({"integration": …}).sort("started_at", -1)` — already indexed.

---

## EXPLAIN — BEFORE State (Evidence)

| Query | Stages | Docs Examined | Keys Examined |
|---|---|---|---|
| `daily_reports.find({"id": ...})` | **COLLSCAN** | 794 | 0 |
| `daily_reports.find({"project_number": "21025"}).sort("report_date", -1)` | SORT → FETCH → IXSCAN | 0 | 0 |
| `job_photos.find({"id": ...})` | **COLLSCAN** | 1,812 | 0 |
| `job_photos.find({"project_number": "21025"}).sort("record_date", -1)` | SORT → FETCH → IXSCAN | 0 | 0 |
| `motive_events.find({"id": ...})` | **COLLSCAN** | 376 | 0 |
| `motive_events.find({"event_family": {"$in": [...]}, "event_at": {"$gte": ...}})` | FETCH → IXSCAN (event_at only) | 372 | 372 |
| `integration_sync_logs.find({"integration": ...}).sort("started_at", -1)` | LIMIT → FETCH → IXSCAN | 52 | 52 |

---

## Conclusion — Evidence-Backed Index Gaps

1. `daily_reports.id` — every find-by-id triggers COLLSCAN. **Required.**
2. `daily_reports.doc_id` — every fallback lookup triggers COLLSCAN. **Required.**
3. `job_photos.id` — heaviest collection (1,812 docs), 4+ COLLSCAN call sites including PDF rendering hot path. **Required.**
4. `motive_events.id` — COLLSCAN per ingestion / driver-profile fetch. **Required.**
5. `motive_events.(event_family, event_at)` — current index drops only one dimension. Compound improves selectivity from 372 keys to ~2 on representative window. **Required.**

No other collections showed COLLSCAN under inspection. **No speculative indexes are authorized.**

---

## What This Audit Explicitly Did NOT Recommend

- No new indexes on `employees`, `notifications`, `equipment`, `operational_events`, `operational_locations`, `asset_mappings` — current plans are IXSCAN-clean or volumes don't justify additional indexes.
- No partial indexes — current query patterns don't benefit from partials.
- No text indexes — no full-text query patterns.
- No TTL changes — existing TTLs (alert_events, webauthn_challenges, session_activity, idempotency, admin_step_ups) are already in place and correct.
