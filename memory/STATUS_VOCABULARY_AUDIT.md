# Status Vocabulary Audit · OMEGA Completeness Audit

**Batch:** OMEGA · Operational Completeness Audit · Phase 3 · Status Vocabulary
**Companion:** `OPERATIONAL_LIFECYCLE_MATRIX.md` · `SOURCE_OF_TRUTH_AUDIT.md`
**Mode:** READ-ONLY · evidence-first
**Date:** 2026-06-01

---

## 1 · Headline

**18 distinct status vocabularies are in active use across the platform — and 11 of the 18 are pairwise incompatible.** The Incident Lifecycle defect documented earlier is not unique. The fragmentation is systemic.

---

## 2 · Per-collection status field inventory

| # | Collection | Field name(s) | Allowed values (source) | Consumer that defines it | Editable? |
|---|---|---|---|---|---|
| 1 | `incidents` | `status` (extra="allow") + `resolution_status` | "open" only (Sprint 1B backfill) | (no producer) | ❌ no PATCH |
| 2 | `incidents` (frontend label) | derived `followUpStatus` | `Follow-Up Required · Investigation Open · Operationally Complete` | `ViewIncident.jsx:60-110` | derived |
| 3 | `incidents` (SafetyIncidents filter) | `status` | `Open · Investigating · Closed` | `SafetyIncidents.jsx:38-42` | filter only |
| 4 | `corrective_actions` | `status` | `Open · In Progress · Pending Review · Verified · Closed` | `OPEN_CAPA_STATES` in `ViewIncident.jsx:66` + `safety_portal/corrective_actions.py` patch handler | ✅ PATCH |
| 5 | `corrective_actions` (governance) | `status` lookup | `closed · completed · verified · resolved` (treated equivalent) | `governance.py:347` | (read) |
| 6 | `jhas` | (no status field) | — | — | n/a |
| 7 | `meetings` | (no status field) | — | — | n/a |
| 8 | `field_leadership_records` | `kind` (not status) · public `signed` boolean | varies per kind | `field_leadership_portal.py` | varies |
| 9 | `daily_reports` | (no canonical status field) | — | — | n/a |
| 10 | `tasks` | `status` | `Open · In Progress · Done · Cancelled` (per code) | `tasks_notifications.py` PATCH | ✅ PATCH |
| 11 | `notifications` | `is_read` boolean + `acknowledged_at` ts | `read · unread · acknowledged` (derived) | `tasks_notifications.py` | ✅ POST |
| 12 | `operations_events` | `severity` + `status` | open/closed via PATCH | `operations.py:431` | ✅ PATCH |
| 13 | `operations_holds` | `status` | `pending · approved · dismissed · released` | `operations.py:499-567` | ✅ POST (3 transitions) |
| 14 | `dispatch_assignments` | `state` | per `lifecycle.py:857 /lifecycle/states` enum | `dispatch_lifecycle.py:595` `transition` | ✅ POST |
| 15 | `continuity_events` | `kind` (not status) | varies | `dispatch_continuity.py:238` | (read-only) |
| 16 | `asset_transfers` | `status` | `requested · approved · rejected · in_transit · received · cancelled · closed` | `asset_transfers.py:454-579` | ✅ POST |
| 17 | `po_requests` | `status` | `open · approved · clarification · receipt_uploaded · closed · cancelled` | `po_requests.py:573-893` | ✅ POST |
| 18 | `fleet_defects` | `state` | `open · acknowledged · in_repair · cleared · oos` | `fleet_ops.py:792-918` | ✅ POST |
| 19 | `equipment_inspections` | derived `signed_off` (timestamp presence) | "signed_off" / "open" | admin signoff endpoint | ✅ POST signoff/delete-signoff |
| 20 | `fire_extinguishers` | `status` + each inspection rated `condition` | `Active · Out of Service · Disposed` (per shape) | `fire_extinguishers.py` patch + inspect | ✅ PATCH |
| 21 | `safety_documents` | `kind` + `is_active` | derived expired/active | `documents.py:141` patch | ✅ PATCH |
| 22 | `document_expirations` | `status` | `active · expired · grace · renewed` | `document_expirations.py:429` | ✅ PATCH |
| 23 | `safety_training_records` | `status` + `expires_on` | `current · expired · expiring_soon · revoked` | `safety_portal/training.py:88` | ✅ PATCH |
| 24 | `qaqc_inspections` | (no status field) — only deficiencies array | — | — | n/a |
| 25 | `inspections` (site safety) | (no status field) | — | — | n/a |
| 26 | `equipment_master` | `is_active` + `deleted_at` | — | server.py PUT | ✅ PUT |
| 27 | `jobs_master` | `is_active` + `archived_at` | — | `PATCH /admin/jobs/:id/active` | ✅ PATCH |
| 28 | `employees` | `is_active` + `status` (employment) + `_term_reason` | `Active · Terminated · LOA · Reactivated` | `employee_lifecycle.py:968` | ✅ POST `/status` |
| 29 | `payroll_variance_batches` | `status` | `open · pending_review · finalized` (per code) | `payroll_variance.py` | (read · per-row mutation only) |
| 30 | `payroll_variance_decisions` | `decision` | `accept · reject · adjust` | (per-row) | ✅ POST |
| 31 | `time_off_requests` | `status` | `pending · approved · rejected · cancelled` | `field_leadership_portal.py:decide` | ✅ POST decide |
| 32 | `r2_degraded_events` | `status` (severity-bound) | varies | (autonomous · audit only) | ❌ |
| 33 | `backup_runs` | `status` + `ok` | `done · failed · in_progress` | scheduler | ❌ (audit only) |
| 34 | `scheduler_runs` (iter445) | `status` + `dedup_attempts` | `in_progress · done · failed` | scheduler | ❌ (audit only) |
| 35 | `drill_runs` | `status` | `done · failed` | recovery dashboard | ❌ |
| 36 | `user_directory` | `is_active` + `is_disabled` | — | admin CRUD | ✅ |
| 37 | `audit_events` / `admin_audit` / `audit_log` | `kind` (event-typed) | enum varies | autonomous | ❌ |

**Total: 37 entities with status-like behavior · 18 distinct vocabularies in active production code paths.**

---

## 3 · Accountability projection's separate vocabulary (consumer · not source)

`lib/accountability_projection.py` derives a unified 4-state lifecycle ONLY for its own use:

| Accountability label | Derivation |
|---|---|
| `open` | nothing else applies |
| `in_progress` | source has open CAPA / linked unresolved |
| `resolved` | `corrected_on_site == "Yes"` OR linked CAPA closed |
| `overdue` (boolean) | derived from `due_at` + `status != resolved` |

This vocabulary does NOT match any of the source workflow vocabularies. It is an internal contract for the accountability dashboard.

---

## 4 · Command Center's separate vocabulary (consumer · not source)

`routes/command_center.py` emits hardcoded "current_status" strings:

| Hardcoded label | Source rule |
|---|---|
| `Open · no resolution path` | JOBS-ISSUE-NO-PATH |
| `Open · unresolved` | SAF-CRITICAL-UNRESOLVED |
| `Open · OSHA notification clock active` | SAF-OSHA-OPEN |
| `Backup overdue` | SYSTEM-BACKUP-STALE |
| (other rule-specific labels) | per-rule |

None of these strings reads `entity.status`. They are template strings appended after rule evaluation.

---

## 5 · Frontend label vocabularies (display-only)

| Page | Label vocab | Source |
|---|---|---|
| `SafetyIncidents.jsx` filter | `Open · Investigating · Closed` | hardcoded |
| `ViewIncident.jsx` banner | `Follow-Up Required · Investigation Open · Operationally Complete` | derived |
| `SafetyCorrectiveActions.jsx` | `Open · In Progress · Pending Review · Verified · Closed` | matches DB |
| `PoRequests.jsx` row pill | `Open · Approved · Clarification · Receipt · Closed · Cancelled` | matches DB |
| `AssetTransfers.jsx` row pill | `Requested · Approved · Rejected · In Transit · Received · Cancelled · Closed` | matches DB |
| `Tasks.jsx` row pill | `Open · In Progress · Done · Cancelled` | matches DB |
| `EmployeeStatus.jsx` | `Active · Terminated · LOA · Reactivated` | matches DB |
| `AdminSchedulerRuns.jsx` | `done · failed · in_progress · dedup_attempts:n` | matches DB |
| `OperationsEvents.jsx` | per-event-kind labels (varies) | matches DB |

---

## 6 · Casing inconsistencies

The same status often appears with different casing/format across the codebase:

| Concept | DB (incidents) | DB (capa) | DB (tasks) | DB (po_requests) | Acc projection |
|---|---|---|---|---|---|
| "open" | `"open"` | `"Open"` | `"Open"` | `"open"` | `"open"` |
| "in progress" | (n/a) | `"In Progress"` | `"In Progress"` | (n/a — `clarification`) | `"in_progress"` |
| "closed" | (n/a) | `"Closed"` | (uses `"Done"`) | `"closed"` | `"resolved"` |
| "resolved" | (n/a) | (uses `"Verified"`) | (n/a) | (n/a) | `"resolved"` |

**Title Case vs snake_case · "Closed" vs "Done" vs "Verified" vs "resolved"** — all referring to the same operational concept ("the work is finished").

---

## 7 · Mismatch risk matrix

| Risk | Surface | Probability | Impact |
|---|---|---|---|
| `SafetyIncidents.jsx` status filter is functionally inert (list endpoint strips `status`) | Frontend | 🟢 already observed in prod | LOW (cosmetic; no closure capability anyway) |
| Command Center labels diverge from DB status for incidents | Consumer | 🟢 already observed | MEDIUM (executive sees "Open · unresolved" while DB says only "open"; never any other state) |
| Accountability projection states (open/in_progress/resolved) don't map to operator's named 4-state lifecycle | Consumer | 🟢 already observed | HIGH (operator-facing surface uses wrong vocab) |
| Daily Reports have no status — Time Verification / Payroll Variance built atop them inherit "no status" | Cross-workflow | 🟢 confirmed | HIGH (no way to mark a DR "reviewed" — every DR is implicitly always-pending) |
| Documents / Training: `expires_on` drives derived states (`expiring_soon`/`expired`) that aren't stored — recomputed at every read | Backend | 🟢 confirmed | LOW (correct by construction; date drift safe) |
| `safety_documents.is_active` vs `is_disabled` (user_directory) — same concept, different field name | Cross-collection | 🟢 confirmed | LOW (no UI exposes both side by side) |
| `equipment_inspections` "signed_off" is a timestamp-presence derivation, not a status field — multi-signoff / partial signoff cannot be represented | Backend | 🟢 confirmed | MEDIUM (operator cannot indicate "shop reviewed but not yet repaired") |
| `qaqc_inspections` has no status whatsoever — once a QA/QC fail is filed, no path to mark "remediated" | Backend | 🟢 confirmed | HIGH (QA/QC defects accumulate forever; no follow-up surface) |
| `inspections` (site safety) same as QA/QC — no status, no follow-up | Backend | 🟢 confirmed | HIGH |
| `jhas` no status — no acknowledgement ledger | Backend | 🟢 confirmed | MEDIUM (OSHA-significant: per crew per day JHA acknowledgement not tracked in field) |
| `meetings` no status — attendance is captured on create but cannot be amended | Backend | 🟢 confirmed | LOW (rarely needed) |
| Fleet Defects: same state-machine concept as Asset Transfers but uses `state` instead of `status` | Cross-collection | 🟢 confirmed | LOW (field-name only) |
| Dispatch Assignments: same as above (`state` field, separate state enum) | Cross-collection | 🟢 confirmed | LOW (separate domain) |
| Payroll Variance batches don't have a "finalize" path even though every row has a decision | Workflow | 🟢 confirmed | MEDIUM (Sandy can decide every row but the batch never closes) |
| Continuity Events have no closure | Workflow | 🟢 confirmed | LOW (event-typed audit log; closure not semantically meaningful) |

---

## 8 · Consolidation map (informational · not authorized to implement)

If a future batch is authorized to canonicalize status vocab, the recommended canonical map would be:

| Canonical (snake) | Title-case display | English label | Equivalent today |
|---|---|---|---|
| `open` | `Open` | Open | open / Open / pending / requested / unread |
| `in_progress` | `In Progress` | In Progress | In Progress / acknowledged / in_repair / Investigating / clarification / in_transit / received |
| `resolved` | `Resolved` | Resolved | Closed (terminal) / Done / Verified / closed / cleared / approved (variant) / repaired / signed_off |
| `cancelled` | `Cancelled` | Cancelled / Withdrawn | cancelled / rejected / dismissed / disposed |

**Not authorized in this audit — informational only.**

---

## 9 · OMEGA discipline

🟢 Read-only · 18 vocabularies catalogued · 11 pairwise incompatibilities identified · no schema changes proposed.

🛑 Continue to `SOURCE_OF_TRUTH_AUDIT.md`.
