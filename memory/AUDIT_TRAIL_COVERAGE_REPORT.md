# Audit Trail Coverage Report · OMEGA Completeness Audit

**Batch:** OMEGA · Operational Completeness Audit · Phase 7
**Mode:** READ-ONLY
**Date:** 2026-06-01

---

## 1 · Headline

**41 active workflows · 13 (32 %) ship with a structured audit collection · 21 (51 %) rely on inline flag-only history · 7 (17 %) have no auditable history at all.**

---

## 2 · Audit collection inventory

| Collection | Purpose | Used by |
|---|---|---|
| `audit_events` | catch-all event log (incident_deleted, etc.) | safety routes · dispatch · admin_ops |
| `admin_audit` | every admin login + portal switch + directory mutation | auth · admin · MFA |
| `admin_audit_log` | legacy / per-request audit | server.py middleware |
| `scheduler_runs` | per-digest-fire audit (iter445) | scheduler-internal |
| `backup_runs` | per-backup audit | backup scheduler |
| `r2_degraded_events` | R2 health events | backup verification |
| `drill_runs` | DR drill executions | recovery dashboard |
| `state_events` | dispatch assignment transitions | dispatch_lifecycle.py |
| `continuity_events` | dispatch continuity events | dispatch_continuity.py |
| `driver_qualification_audit` | driver qual imports | hr_portal.py |
| `cleanup_*` historical evidence | Sprint 1B per-operation evidence | one-off |
| `corrective_actions.audit[]` (inline) | per-CAPA history (best practice but not universal) | safety/corrective_actions.py |
| `tasks.comments[]` (inline) | task timeline | tasks_notifications.py |
| `fire_extinguishers.inspections[]` (inline) | per-extinguisher inspection history | safety_portal/fire_extinguishers.py |

---

## 3 · Per-workflow coverage table

| # | Workflow | Status changes? | Audit collection | Inline history? | Coverage |
|---|---|---|---|---|---|
| 1 | Incidents | ❌ doesn't change | `audit_events` for delete only | ❌ | 🔴 NONE (for status) |
| 2 | CAPA | ✅ | (none dedicated) | ✅ `audit[]` inline | 🟢 |
| 3 | JHA form | ❌ doesn't change | (none) | ❌ | 🔴 NONE |
| 4 | Safety Meeting | ❌ doesn't change | (none) | ❌ | 🔴 NONE |
| 5 | FL Forms | per-kind only | (none) | per-kind fields | 🟡 |
| 6 | PPE Issuance | ❌ | (none) | ❌ | 🔴 NONE |
| 9 | Training Records | ✅ | (none) | `status` + `expires_on` only | 🟡 |
| 10-13 | Employees | ✅ | (none dedicated) | `_term_reason`, `_reactivated_at` fields | 🟡 |
| 14 | Time Verification | derived | n/a | n/a | n/a |
| 15 | Payroll Variance | per-row | `payroll_variance_decisions` is the audit | row decisions | 🟢 (rows) · 🔴 (batch) |
| 16-21 | PO Requests | ✅ | inline `audit_log[]` field on doc | ✅ | 🟢 |
| 22 | Suppliers | archive only | (none) | `deleted_at`, `restored_at` | 🟡 |
| 23-24 | Jobs / Project | ✅ | (none) | `is_active`, `archived_at`, `restored_at` + `_audit_log[]` | 🟢 |
| 25 | Daily Reports | ❌ | (none) | `audit_footer` endpoint (derived) | 🟡 |
| 30 | Fleet Defects | ✅ | (none) | `acknowledged_at`, `repaired_at`, `cleared_at`, `oos_at` fields | 🟡 |
| 31 | DVIR | ✅ | (none) | `signed_off_at`, `signed_off_by` fields | 🟡 |
| 32 | Equipment Master | archive | (none) | `deleted_at`, `restored_at` | 🟡 |
| 33 | Asset Transfers | ✅ | (none dedicated) | `state_history[]` inline field | 🟢 |
| 34-36 | Dispatch | ✅ | `state_events` (cross-cutting) | per-doc embedded | 🟢 |
| 37 | Driver Qualification | ✅ | `driver_qualification_audit` | per-import | 🟢 |
| 38 | QA/QC | ❌ | `audit_events` (delete only) | ❌ | 🔴 NONE |
| 39 | Site Inspection | ❌ | (none) | ❌ | 🔴 NONE |
| 40 | Fire Extinguishers | ✅ | `inspections[]` inline = full history | ✅ | 🟢 |
| 41 | Safety Documents | ✅ | (none) | `is_active`, `expires_on` | 🟡 |
| 42 | Document Expirations | ✅ | (none) | `status`, `renewed_at`, `expires_on` | 🟡 |
| 43 | Tasks | ✅ | (none) | `comments[]` inline + `status_history[]` | 🟢 |
| 44 | Notifications | ✅ | (none) | `is_read`, `acknowledged_at` | 🟡 |
| 45 | Ops Events / Holds | ✅ | `audit_events` (cross-cutting) | per-doc timestamps | 🟢 |
| 46 | Time Off | ✅ | (none) | `decided_at`, `decided_by`, decision field | 🟡 |
| 50 | Scheduler Runs | ✅ | `scheduler_runs` (iter445) | ✅ self-auditing | 🟢 |
| 54 | Backup Digest | ✅ | `backup_runs` | ✅ | 🟢 |
| 55 | Recovery Dashboard | ✅ | `drill_runs` | ✅ | 🟢 |
| 56 | User Directory | ✅ | `admin_audit` | ✅ | 🟢 |
| 60 | MFA | ✅ | `audit_events` (via mfa_routes) | ✅ | 🟢 |

---

## 4 · Aggregate audit coverage

| Coverage class | Count |
|---|---|
| 🟢 dedicated audit (collection OR inline history list) | 13 |
| 🟡 flag-only history (timestamps · last actor · status field) | 21 |
| 🔴 no audit at all for status changes | 7 |
| n/a (no status changes; derived consumers) | 7 |

**Overall coverage: 34/41 active workflows have at least flag-only history (83 %). Only 13/41 have a defensible "show me who changed this and when" trace (32 %).**

---

## 5 · 🔴 Workflows with zero status-change audit

The 7 workflows where NO audit exists for status changes (and no status changes occur because the workflow doesn't move):

| Workflow | Why this matters | OSHA / compliance impact |
|---|---|---|
| Incidents | OSHA-recordable incidents have no closure audit | HIGH — federal recordkeeping rules require closure tracking for recordable injuries |
| JHA forms | crew daily acknowledgement not audited | MEDIUM — JHA acknowledgement is a leading indicator |
| Safety Meetings | attendance amendments not audited | LOW — attendance captured at create |
| QA/QC Inspections | deficiency resolution not audited | MEDIUM — owner audits often request "show me when this was fixed" |
| Site Inspections | follow-up actions not audited | MEDIUM — same |
| FL Forms (most kinds) | post-submit changes not tracked | LOW — typically one-and-done |
| PPE Issuance | return not tracked at all | LOW (return workflow itself absent) |

---

## 6 · 🟡 Flag-only history · forensic strength assessment

Flag-only history (a `closed_at`, `closed_by`, current `status`) is sufficient for:

* Single-step transitions (Open → Closed)
* Workflows where reopening is forbidden or rare
* Workflows where the "who/when" is the only forensic data needed

It is insufficient for:

* Multi-step workflows where intermediate states matter (e.g., "this was Investigating for 14 days before being Closed")
* Disputes about prior state values
* Compliance regimes requiring full chain-of-custody

Workflows in the 🟡 column should be evaluated against their domain's compliance requirements before declaring them sufficient.

---

## 7 · Coverage by audit pattern

| Pattern | Workflows using it | Strength |
|---|---|---|
| Dedicated audit collection (sibling) | Scheduler Runs · Backup · Recovery · Dispatch Assignments · Driver Qual · Ops Events · User Directory · MFA | 🟢 Strongest |
| Inline `audit[]` / `audit_log[]` array on doc | PO Requests · Jobs · CAPA · Asset Transfers (`state_history[]`) · Tasks (`comments[]`) | 🟢 Strong (but harder to query across docs) |
| Inline domain history (e.g. `inspections[]`) | Fire Extinguishers · QAQC (deficiencies only) | 🟡 Domain-specific |
| Per-transition timestamp fields | Fleet Defects · DVIR · Suppliers/Jobs (archive) · Notifications · Time Off · Documents · Document Expirations · Training Records | 🟡 Sufficient for single-step |
| `cleanup_*` evidence | one-off Sprint 1B operational cleanups | 🟡 Operational, not user-driven |
| None | Incidents · JHA · Meetings · QAQC · Site Inspections · FL Forms · PPE Issuance | 🔴 Gap |

---

## 8 · OMEGA discipline

🟢 Read-only · audit collections + inline patterns enumerated · 7 zero-audit workflows flagged · no remediation proposed.

🛑 Continue to `COMMAND_CENTER_ACCOUNTABILITY_ALIGNMENT.md`.
