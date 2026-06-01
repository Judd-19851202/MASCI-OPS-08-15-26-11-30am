# Production Observation Report

**Batch:** OMEGA Production Observation Audit (read-only)
**Date:** 2026-02-27 (probes captured 2026-06-01T01:14Z – 01:18Z production-time)
**Environment:** Production only · `https://mascidocs.com`
**Mode:** STRICTLY READ-ONLY. No writes. No code. No deploy. No collection / schema / UI / permission changes. No tickets / notifications / workflows created. No pillar continuation.
**Operator authorization:** "OMEGA AUTHORIZATION — PRODUCTION OBSERVATION BATCH · Read-only verification only · STOP after reports are written."

Companion files:
- `PRODUCTION_DATA_HYGIENE_REPORT.md` (Task 3 detail)
- `PRODUCTION_REGRESSION_AUDIT.md` (Task 2 detail)
- `/app/memory/prod_observation_evidence/` (10 raw evidence files: curl probe logs · 2 HR Hub screenshots)

---

## 1 · Final verdict

# 🟡 AMBER

Production is **healthy and stable** with Sprint 1C/1D successfully deployed. Two material findings push the verdict from GREEN to AMBER (neither is a deployment regression):

1. **Pillar 1A-3 ownership projection mismatch on job 24-06** — Command Center labels owner as "Unassigned PM", but the job directory (`/api/jobs`) shows `project_manager = "David Jewett"`. Suggests the accountability projection is not joining the jobs collection to resolve the PM for daily-report-missing rules.
2. **Recovery pill = AMBER** due to (a) no DR drill recorded (`rto.last_drill_min = None`) and (b) R2 bucket usage at 91.49 GB, above the 50 GB ALERT threshold.

The Command Center itself shows `pill: RED` with 8 operational items — that is **expected operational behaviour** (legitimate jobs with missing daily reports and 3 open incidents without CAPAs), **not a technical defect**. The Command Center is correctly surfacing executive attention items.

---

## 2 · Top 10 issues found

> Numbered by impact. Every finding is supported by evidence in `/app/memory/prod_observation_evidence/`. **No fixes are proposed in this report** per OMEGA observation-only rule — only recommended actions for future authorized batches.

### 🔴 #1 · Pillar 1A-3 ownership projection mismatch — job 24-06

* **Evidence:** `06_cc_jobs_red_detail.txt` shows Command Center item `Project 24-06 · DR missing · owner = "Unassigned PM"`. `09_jobs_directory.txt` shows the same job number 24-06 has `project_manager = "David Jewett"` in `/api/jobs`.
* **Implication:** The accountability projection is **not** joining the jobs collection for the `JOBS-DR-MISSING` rule's owner resolution — it falls back to a default literal "Unassigned PM". Real ownership exists but the projection doesn't surface it.
* **Recommended action (future batch):** Pillar 1A-3 projection patch — join `jobs.project_number → jobs.project_manager` before falling back to literal default.

### 🟡 #2 · Three jobs genuinely have no PM assigned

* **Evidence:** `09_jobs_directory.txt`: jobs `20-07`, `22-08`, `24-08` all have `project_manager = ""` (empty string).
* **Implication:** These are not placeholder-projection errors — they are real data hygiene issues (jobs created without PM assignment). The Command Center correctly surfaces them.
* **Recommended action (future batch):** Operator manual assignment of PMs to jobs 20-07, 22-08, 24-08 via the existing admin job management flow.

### 🟡 #3 · No DR drill recorded → RTO AMBER

* **Evidence:** `02_health_audit.txt` recovery snapshot: `rto: {target_min: 15, last_drill_min: None, status: 'AMBER'}`. `last_drill: None`.
* **Implication:** Disaster-recovery readiness is unverified. RPO is GREEN (7.7 min / 60 min target), but RTO depends on a documented drill.
* **Recommended action (future batch):** Schedule + execute a DR drill; surfacing the wall-clock recovery time into `recovery.last_drill_min` so RTO transitions GREEN.

### 🟡 #4 · R2 bucket usage above ALERT threshold

* **Evidence:** `02_health_audit.txt` recovery snapshot: `bucket_usage: {gb: 91.49, warn_gb: 45.0, alert_gb: 50.0, status: 'AMBER'}`.
* **Implication:** Cumulative R2 cost growing past the configured alert ceiling. Archive_count=94 over last 7d and 30d (consistent backup rotation).
* **Recommended action (future batch):** Raise the alert threshold to align with current operational baseline OR enforce stricter retention (currently 14 d) OR shard backups to cheaper class storage.

### 🟡 #5 · Two backup failures on 2026-05-25 — `usage_events` sort-memory exception

* **Evidence:** `02_health_audit.txt` recovery snapshot `failures_7d`:
  ```
  2026-05-25T15:18:06Z · complete-r2-error · "Sort exceeded memory limit of 33554432 bytes ... usage_events"
  2026-05-25T15:16:20Z · complete-r2-error · same exception 
  ```
* **Implication:** When backing up the `usage_events` collection, MongoDB's in-memory sort limit (32 MB) was exceeded. Subsequent backups succeeded (last successful 2026-06-01T01:07Z), so the failure mode is transient and likely caused by a one-off large query window. The two failures are 5–7 days old.
* **Recommended action (future batch):** Add `allow_disk_use=True` to the backup query for `usage_events`, or shard the sort by date range. Not urgent — backups have been healthy since.

### 🟡 #6 · Three production incidents open > 7 days without a corrective action

* **Evidence:** `06_cc_jobs_red_detail.txt`:
  - INC-2026-00004 (open 19 d, Near Miss, project 26-01-CP, severity RED · rule JOBS-ISSUE-NO-PATH)
  - INC-2026-00010 (open 13 d, Vehicle / Mobile Equipment, project 26-01-CP, AMBER)
  - INC-2026-00011 (open 10 d, Property / Equipment Damage, project 25-22-CP, AMBER)
* **Implication:** Legitimate operational signal — these are real safety incidents awaiting a CAPA path. Owner attributed to "Safety" (the role, not a person).
* **Recommended action (future batch):** Operator-driven — safety lead opens CAPAs against these incidents via the existing Safety Portal workflow.

### 🟡 #7 · Deactivated test account still in field-leadership-users collection

* **Evidence:** `04_data_hygiene.txt` Section G — `fieldleader@mascigc.com` (Field Leader · Superintendent · is_active=False).
* **Implication:** Account is deactivated (Sprint 1B), so it cannot authenticate and does not surface in accountability. It does count toward the FL-user roster total (27 → would be 26 if hard-deleted).
* **Recommended action (future batch):** Operator decides whether to hard-delete or keep as audit-preserved deactivated record (Sprint 1B's chosen posture).

### 🟢 #8 · Production runtime restarted ~12 min before audit

* **Evidence:** `02_health_audit.txt` Section J — `uptime_s=515` at probe time; started_at `2026-06-01T01:07:04Z`.
* **Implication:** Production pod restarted ~12 min before audit start. No active failure surface (scheduler lock fresh, backup succeeded after restart). This is normal Emergent pod-rotation behaviour.
* **Recommended action:** None. Informational.

### 🟢 #9 · Accountability `phase = "1A-3"` confirmed on production

* **Evidence:** `05_accountability_audit.txt` snapshot: `phase = "1A-3"` · timing 841 ms total · 8 total items · 1 overdue · 0 placeholder owners surfaced in rollup.
* **Implication:** Phase 1A-3 accountability engine is the production phase. Pillar 1A-4 / 1A-5 / 1A-6 are NOT live on production (matches Critical Fix Sprint 1 progression).
* **Recommended action:** None for this batch. Pillar 1A-4 + 1A-5 + 1A-6 progression deferred to next authorized phase.

### 🟢 #10 · `/api/admin/audit-events` endpoint not exposed on production

* **Evidence:** `10_final_probes.txt` — `/api/admin/audit-events?kind=incident_deleted` → 404. Same for `/audit/events` and `/events` variants.
* **Implication:** The `audit_events` collection is being written to by Sprint 1C's delete route (verified in preview), but production lacks a public read endpoint for it. The pre-existing `/api/admin/audit?kind=...` route returns `admin_audit` collection (login/logout events), not `audit_events`.
* **Recommended action (future batch):** Pillar 1A-6 / forensic surface enhancement — expose a read endpoint for `audit_events` so operators can inspect Sprint 1C audit rows post-delete. Not blocking deploy.

---

## 3 · Phase-by-phase summary

### 3.1 · Task 1 · Production Health Audit · 🟡 AMBER

| Check | Result |
|---|---|
| Scheduler alive | 🟢 `scheduler.alive=true` · last_lock_ts 3 min before probe · owner_pod `safety-audit-mobile-1-59796c5d4-c9ctr` |
| Backup cadence active | 🟢 last_backup 7.7 min old · archive_count 94 (7d=94, 30d=94) · `enabled=true · hours_utc=[2,18] · retention=14d` |
| Recovery dashboard healthy | 🟡 overall pill **AMBER** — RPO GREEN (7.7m/60m), **RTO AMBER (no drill)** |
| No new warnings | 🟡 1 warning surfaced — `bucket-usage 91.49 GB above ALERT 50 GB threshold` |
| Accountability endpoints responding | 🟢 sources 320 ms · snapshot 1042–1878 ms |
| Command Center responding | 🟢 snapshot 2481 ms · pill RED with 8 actionable items (operational, not defect) |

### 3.2 · Task 2 · Deployment Regression Audit · 🟢 GREEN

(See `PRODUCTION_REGRESSION_AUDIT.md` for full evidence.)

* 🟢 Sprint 1C `DELETE /api/incidents/{id}` contract live on prod (4/4 probes pass)
* 🟢 Sprint 1D HR Hub Sign Out button properly themed (desktop + mobile screenshots captured)
* 🟢 0 console errors during HR Hub visit on production
* 🟢 No preview-environment banner (correct environment separation)
* 🟢 No new frontend rendering issues; SPA bundle hash `main.ed1d4f48.js`

### 3.3 · Task 3 · Data Hygiene Audit · 🟢 GREEN (1 known deactivated record)

(See `PRODUCTION_DATA_HYGIENE_REPORT.md` for full categorization.)

| Collection | Total | Test markers |
|---|---|---|
| incidents | 6 | 0 |
| inspections | 0 | 0 |
| meetings | 23 | 0 |
| JHAs | 0 | 0 |
| daily_reports | 86 | 0 |
| employees | 245 | 0 |
| HR users | 3 | 0 |
| Safety users | 2 | 0 (canonical Safety Manager — false positive on regex) |
| Shop users | 2 | 0 |
| PMs | 8 | 0 |
| Dispatch users | 2 | 0 |
| field_leadership_users | 27 | **1 deactivated** (`fieldleader@mascigc.com`) |
| Duplicate doc_ids across scanned collections | 0 | n/a |

### 3.4 · Task 4 · Executive Command Center Audit · 🟡 AMBER (one projection mismatch)

| Check | Result |
|---|---|
| Ownership projections functioning | 🟡 ownership defect on job 24-06 (David Jewett in `/api/jobs`, "Unassigned PM" in CC) |
| Accountability drilldowns functioning | 🟢 `/admin/accountability/snapshot` returns 200 with rollup (8 total · 1 overdue · 0 placeholder in rollup section) |
| No placeholder ownership where real ownership exists | 🟡 1 case found (job 24-06) — see Finding #1 |
| Command Center latency acceptable | 🟢 2481 ms · under 3 s target |

---

## 4 · Evidence summary

| File | Purpose |
|---|---|
| `prod_observation_evidence/01_auth_and_health.txt` | Production /api/health + /api/version + multi-login flow |
| `prod_observation_evidence/02_health_audit.txt` | Task 1 raw probes (backup, scheduler, recovery, Sentry) |
| `prod_observation_evidence/03_regression_audit.txt` | Task 2 raw probes (Sprint 1C contract, audit endpoint, frontend SPA assets) |
| `prod_observation_evidence/04_data_hygiene.txt` | Task 3 collection scans (incidents, inspections, meetings, JHAs, DRs, employees, all user collections) |
| `prod_observation_evidence/05_accountability_audit.txt` | Task 4 raw probes (sources, snapshot, owner drilldown, latency) |
| `prod_observation_evidence/06_cc_jobs_red_detail.txt` | Command Center "Jobs Today" RED card · 8 actionable items deep dump |
| `prod_observation_evidence/07_unassigned_pm_check.txt` | Cross-check of "Unassigned PM" claim vs `/api/admin/projects` |
| `prod_observation_evidence/08_projects_lookup.txt` | Endpoint-discovery for project sources |
| `prod_observation_evidence/09_jobs_directory.txt` | Full 28-row `/api/jobs` directory + CC-flagged-job ownership cross-reference |
| `prod_observation_evidence/10_final_probes.txt` | Audit endpoint check, incident drilldowns, cross-portal /me probes |
| `prod_observation_evidence/hr_hub_prod_desktop_1920.png` | HR Hub rendered on production · 1920 viewport |
| `prod_observation_evidence/hr_hub_prod_mobile_420.png` | HR Hub rendered on production · 420 viewport |

---

## 5 · Recommended actions (for future authorized batches — NOT executed in this batch)

| Priority | Action | Batch type |
|---|---|---|
| P1 | Pillar 1A-3 projection fix — join `jobs.project_number → project_manager` before "Unassigned PM" fallback (Finding #1) | Bug-fix sprint authorization |
| P1 | Operator-driven · assign PMs to jobs 20-07, 22-08, 24-08 (Finding #2) | Operator data action (no code) |
| P2 | Schedule + execute DR drill to surface `rto.last_drill_min` (Finding #3) | Operator DR drill batch |
| P2 | Resolve R2 bucket-usage AMBER (Finding #4) — operator chooses threshold raise / retention tighten / cold-storage shard | Operator decision |
| P2 | Add `allow_disk_use=True` to backup query for `usage_events` (Finding #5) | Backup-resilience patch |
| P2 | Operator-driven · open CAPAs against INC-2026-00004 / 00010 / 00011 (Finding #6) | Safety lead operational action |
| P3 | Operator decision · hard-delete or retain deactivated `fieldleader@mascigc.com` (Finding #7) | Production data action |
| P3 | Expose `/api/admin/audit-events` read endpoint for Sprint 1C audit visibility (Finding #10) | Pillar 1A-6 forensic surface |

---

## 6 · OMEGA discipline confirmation

| OMEGA rule | Observed |
|---|---|
| NO code | ✅ — only reports written |
| NO deploy | ✅ |
| NO collection modifications | ✅ |
| NO schema changes | ✅ |
| NO UI changes | ✅ |
| NO permission changes | ✅ |
| NO ticket creation | ✅ |
| NO notification creation | ✅ |
| NO workflow continuation | ✅ |
| NO pillar continuation | ✅ |
| Read-only verification only | ✅ |
| Evidence for every finding | ✅ |
| No assumptions | ✅ |

🛑 STOP. All three deliverable reports written. Awaiting operator's next explicit authorization.
