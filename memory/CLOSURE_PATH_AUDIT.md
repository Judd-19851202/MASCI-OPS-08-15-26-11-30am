# Closure Path Audit · OMEGA Completeness Audit

**Batch:** OMEGA · Operational Completeness Audit · Phase 6
**Mode:** READ-ONLY
**Date:** 2026-06-01

---

## 1 · Headline

**Of 55 workflows, 24 have a working closure path (terminal state via API + UI). 11 have closure surfaces but no audit trail. 9 have no closure path at all.**

---

## 2 · Per-workflow closure path

| # | Workflow | Closure mechanism | Endpoint | Audit trail? | Who can close? |
|---|---|---|---|---|---|
| 1 | Incident | ❌ none | — | — | none |
| 2 | CAPA | PATCH `status="Closed"` | `/safety/corrective-actions/{id}` | 🟡 partial (status field only · no history collection) | Safety · Admin |
| 3 | JHA form | ❌ none (DELETE only · destructive) | — | — | Safety · Admin (DELETE) |
| 4 | Safety Meeting | ❌ none (DELETE only) | — | — | Safety · Admin (DELETE) |
| 5 | FL Forms | ❌ none (signed boolean is per-submission only) | — | — | none for closure |
| 6 | PPE Issuance | ❌ none | — | — | none |
| 7 | PPE Return | ⚫ not implemented | — | — | n/a |
| 8 | Safety Training (form) | ❌ none (DELETE only) | — | — | n/a |
| 9 | Training Records | PATCH `status="revoked"` or natural expiry | `/safety/training-records/{id}` | 🟡 status only | Safety · Admin |
| 10-13 | Employees / Lifecycle | POST `/api/hr/employees/{id}/status` (terminate) or `/reactivate` | dedicated endpoints | 🟡 `_term_reason` + timestamp on doc | HR · Admin |
| 14 | Time Verification | n/a (derived) | — | — | n/a |
| 15 | Payroll Variance | Per-row decision via POST `/decide` · ❌ no batch finalize | rows: ✅ · batch: ❌ | row decision is the audit | HR · Admin (rows only) |
| 16-21 | PO Request | POST `/close` + POST `/cancel` | dedicated endpoints | ✅ (audit collection · iter prior) | PM · Admin |
| 22 | Vendor/Supplier | DELETE → archive (soft) + `/restore` | dedicated | 🟡 archive flag only | Admin |
| 23 | Job/Project | PATCH `/active=false` + DELETE soft | dedicated | 🟡 archive flag + restore | Admin |
| 25 | Daily Report | ❌ none (DELETE only) | — | — | Admin · Super-Admin (DELETE) |
| 26-29 | Photos | ❌ no closure (no orphan janitor) | — | — | n/a |
| 30 | Fleet Defects | POST `/clear` (Dispatch) or `/repair` (Shop) | dedicated | 🟡 state field + transition timestamps | Dispatch · Shop · Admin |
| 31 | DVIR | POST `/admin/equipment-inspections/{id}/signoff` (Shop) | dedicated | 🟡 signoff stamp = audit | Shop · Admin |
| 32 | Equipment Master | DELETE → archive + restore | dedicated | 🟡 archive flag | Admin |
| 33 | Asset Transfers | POST `/close` (terminal) or `/cancel` or `/reject` | dedicated | 🟡 state field; no history collection | PM · Dispatch · Admin |
| 34-36 | Dispatch | POST `/cancel` + `/transition(state="completed")` | dedicated | 🟡 `state_events` collection captures transitions | Dispatch · Admin |
| 37 | Driver Qualification | natural expiry · import re-application | — | ✅ `driver_qualification_audit` collection | HR · Admin |
| 38 | QA/QC | ❌ none (DELETE only) | — | — | Admin · Super-Admin (DELETE) |
| 39 | Site Inspection | ❌ none (DELETE only) | — | — | Admin · Super-Admin (DELETE) |
| 40 | Fire Extinguishers | PATCH `status` (Active → OutOfService → Disposed) · per-inspection history | dedicated | ✅ inspection history array | Safety · Admin |
| 41 | Safety Documents | PATCH `is_active=false` · DELETE | dedicated | 🟡 flag only | Safety · Admin |
| 42 | Document Expirations | DELETE on renewal · or status transition via PATCH | dedicated | 🟡 status field | Safety · HR · Admin |
| 43 | Tasks | PATCH `status="Done"` or `"Cancelled"` | dedicated | ✅ comment timeline | All roles (assignee) |
| 44 | Notifications | POST `/{id}/read` · `/acknowledge` | dedicated | 🟡 `is_read` + `acknowledged_at` | Self |
| 45 | Ops Events / Holds | POST `/holds/{id}/approve` · `/dismiss` · `/release` | dedicated | 🟡 status + transition timestamps | Dispatch · Safety · HR · Admin · gated |
| 46 | Time Off | POST `/decide` (approve/reject) | dedicated | 🟡 decision flag + timestamp | HR · FL · Admin |
| 50 | Scheduler Runs | natural terminal via `mark_completed` / `mark_failed` | scheduler-internal | ✅ (iter445 collection) | (autonomous) |
| 54 | Backup Digest | natural terminal `backup_runs.status` | scheduler | ✅ `backup_runs` collection | (autonomous) |
| 55 | Recovery Dashboard | `drill_runs` row | one-shot | ✅ `drill_runs` collection | Admin |
| 56 | User Directory | PATCH/DELETE · disable flag | dedicated | ✅ `admin_audit` | Admin |
| 60 | MFA | POST `/disable` | dedicated | ✅ `audit_events` | Self · Admin |

---

## 3 · Closure path classification

| Category | Count | Workflows |
|---|---|---|
| 🟢 Closure path WITH audit collection | 13 | PO Requests · Dispatch · Driver Qualification · Fire Extinguishers · Tasks (timeline) · Scheduler Runs · Backup · Recovery · User Directory · MFA · ops events · employees (partial) · training records (partial) |
| 🟡 Closure path WITHOUT audit collection (flag/timestamp only) | 11 | CAPA · Training Records · Asset Transfers · Fleet Defects · DVIR · Vendors · Jobs · Equipment Master · Safety Documents · Document Expirations · Time Off |
| 🔴 Closure path MISSING (record cannot exit active list) | 9 | Incidents · JHA · Safety Meetings · FL Forms · PPE Issuance · Daily Reports · QA/QC · Site Inspections · Payroll Variance (batch) |
| ⚫ Closure path UNIMPLEMENTED (workflow itself doesn't exist) | 1 | PPE Return |
| n/a (derived consumer · not a workflow) | 7 | Accountability · CC · Project Health · Time Verification · Photo Viewer · Photos (library) · Admin Settings |
| **Total** | **41** non-derived workflows |

---

## 4 · 🔴 Accumulation risk · workflows where records will pile up forever

| Workflow | Volume/week (estimated) | Records since 2026-01-01 (estimated) | Operator impact |
|---|---|---|---|
| Incidents | 1-3 | ~30 | Every incident on every dashboard appears "open" forever |
| Daily Reports | 30+ per active job · ~150/wk | ~3000+ | Time Verification builds atop these · never "verified" |
| Site Inspections | 5-10 | ~150 | Open-defect feeds the safety review queue endlessly |
| QA/QC | 3-5 | ~100 | Every deficiency stays visible to PM forever |
| JHA Forms | 1-2 per project per day | ~500 | Acknowledgement / archival ceremony absent |
| Safety Meetings | 1 per crew per day | ~2000 | Same |
| FL Forms | 5-10/wk | ~150 | Same |
| PPE Issuance | 2-5/wk | ~80 | Issuance counts grow unboundedly · no return rolls them off |
| Payroll Variance batches | 1/wk | ~24 batches | All show "open" because no finalize step |

Aggregate over a 24-month operating window, conservatively 50,000+ records that the platform cannot mark closed. None of them are deletable without losing the record — they're permanent until a closure surface is built.

---

## 5 · 🟡 Closure-without-audit · forensic gap if a dispute arises

For these 11 workflows, the record's status changes but **no separate history collection records the transition**:

| Workflow | What's missing | Real-world risk |
|---|---|---|
| CAPA | who closed it, when, why | Sandy/Safety dispute "this CAPA was closed without verification" — only the current `status="Closed"` and `closed_at` stamp survive |
| Asset Transfers | per-transition history | Dispute over who marked "received" without seeing the equipment |
| Fleet Defects | per-transition history | Shop says "we repaired this on date X" — only `state="cleared"` + cleared_at survive |
| DVIR | who signed off | `signed_off_by` field exists; full audit trail does not |
| Vendors / Jobs / Equipment Master | archive transitions | Soft-delete with restore exists; **who** archived isn't always captured |
| Safety Documents | activation transitions | Same |
| Document Expirations | renewal/expiry transitions | Date-driven recompute; manual edits hard to attribute |
| Time Off | approve/reject by whom · with comment | Decided field + timestamp exist; comment not standardized |

These are workflows where adding a `status_history[]` array (or a sibling collection) would close the gap without changing the user-visible workflow.

---

## 6 · Closure terminology fragmentation

| Concept | Used as terminal label by | Used as transitional label by |
|---|---|---|
| `closed` | PO · CAPA · Asset Transfer · Doc Expir | (none — terminal everywhere) |
| `completed` | Tasks (via `Done`) | governance integrity rule alias |
| `done` | Tasks · Scheduler Runs · Backup | (none) |
| `verified` | CAPA | governance alias |
| `resolved` | Accountability projection | governance alias |
| `cancelled` | PO · Asset Transfer · Tasks · Dispatch · Time Off | distinct semantic |
| `rejected` | Asset Transfer · Time Off · PO clarification | distinct semantic |
| `dismissed` | Ops Holds | distinct semantic (close without approval) |
| `released` | Ops Holds | (terminal for holds) |
| `archived` | Jobs · Suppliers · Equipment · Employees | soft-delete · not lifecycle-closed |

10 distinct terminal-state labels across the platform. Only `closed` is shared by more than 3 workflows.

---

## 7 · OMEGA discipline

🟢 Read-only · closure paths inventoried · 9 missing-closure workflows enumerated · no remediation proposed.

🛑 Continue to `AUDIT_TRAIL_COVERAGE_REPORT.md`.
