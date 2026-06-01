# Operational Completeness Register · OMEGA Master Register

**Batch:** OMEGA · Operational Completeness Audit · Phase 10
**Companion:** all 9 prior audit deliverables in `/app/memory/`
**Mode:** READ-ONLY
**Date:** 2026-06-01

---

## 1 · Register legend

| Severity | Meaning |
|---|---|
| 🔴 CRITICAL | Workflow appears usable but cannot be completed, closed, approved, resolved, or audited |
| 🟡 IMPORTANT | Workflow works but missing lifecycle, status clarity, role action, or source-of-truth coherence |
| 🟢 MINOR | Usable but confusing, inconsistent, or poorly labeled |
| ⚫ PLACEHOLDER | Surface exists but real workflow is not implemented |

---

## 2 · Register · 22 findings

### 🔴 CRITICAL (10 findings)

| ID | Workflow | Severity | Classification | What exists | What is missing | Business risk | Affected roles | Source files / routes / collections | Evidence | Recommended remediation phase | Blocks current ops? | Customer #2? | White Label? | ForgedOps Ops Center? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OC-001 | Incident closure | 🔴 | 🔴 INCOMPLETE | `status` field exists (Sprint 1B); 4-vocab display | No PATCH endpoint; no Mark-* buttons; no audit; OSHA records remain "open" forever | OSHA recordkeeping non-compliance; Sandy/Safety has no closure ledger | Safety · Admin · HR (read) | `routes/safety.py:202-260, 754-879`; `incidents` | `INCIDENT_LIFECYCLE_AUDIT.md` | Phase 1A · same scope as incident lifecycle remediation | YES | YES | YES | YES |
| OC-002 | Daily Reports closure | 🔴 | 🔴 INCOMPLETE | Create + view + delete | No PATCH; no review/approve; no edit-after-submit; no audit | Office cannot mark a DR "reviewed"; Time Verification + Payroll Variance inherit "always pending" | PM · Admin · HR (read) | `routes/daily_reports.py`; `daily_reports` | `OPERATIONAL_LIFECYCLE_MATRIX.md` §4.1 | Phase 1B | YES | YES | YES | YES |
| OC-003 | QA/QC deficiency resolution | 🔴 | 🔴 INCOMPLETE | Create + view + delete; deficiencies stored as array | No per-deficiency status; no resolve/re-inspect | QA/QC defects accumulate forever; sub disputes unresolvable | PM · Admin | `routes/qaqc.py`; `qaqc_inspections` | `OPERATIONAL_LIFECYCLE_MATRIX.md` §4.1 | Phase 1B | YES | YES | YES | YES |
| OC-004 | Site Inspection follow-up | 🔴 | 🔴 INCOMPLETE | Create + view + delete | No follow-up surface; no Pass/Fail item resolution after initial submit | Safety walks accumulate; <80% grade has no remediation trail | Safety · PM · Admin | `routes/safety.py` (`/inspections/*`); `inspections` | same | Phase 1B | YES | YES | YES | YES |
| OC-005 | JHA acknowledgement ledger | 🔴 | 🔴 INCOMPLETE | JHA library exists; iter445 added FL Hub visibility | No per-crew per-day acknowledgement record; OSHA-significant | Crew acknowledgement unaudited; OSHA exposure | Safety · FL · Admin | `routes/safety.py` (`/jhas/*`); `jhas` | `OPERATIONAL_LIFECYCLE_MATRIX.md` §4.1 | Phase 2 | YES | YES | YES | YES |
| OC-006 | Safety Meeting amend / status | 🔴 | 🔴 INCOMPLETE | Create + view + delete | No edit; attendance is immutable after submit | Attendance corrections require re-file | Safety · FL · Admin | `routes/safety.py` (`/meetings/*`); `meetings` | same | Phase 2 | NO | YES | YES | NO |
| OC-007 | Payroll Variance batch finalize | 🔴 | 🔴 INCOMPLETE | Per-row decisions wired (`status` enum suggests `finalized` is intended) | No batch-level finalize endpoint | Batches accumulate; Sandy can't close a payroll week even after deciding every row | HR · Admin | `payroll_variance.py`; `payroll_variance_batches` | `USER_TASK_COMPLETION_AUDIT.md` §3.2 | Phase 1B | YES | YES | YES | YES |
| OC-008 | PPE Issuance return / reconciliation | 🔴 | ⚫ PLACEHOLDER | Issuance workflow exists | NO return workflow; NO collection; NO endpoint; NO UI | PPE accountability cannot be closed; lost-PPE attribution impossible | Safety · Field · Admin | (no files); `safety_equipment_issuances` (one-way) | `OPERATIONAL_WORKFLOW_INVENTORY.md` row 7 | Phase 2 | YES | YES | YES | YES |
| OC-009 | Photo Delete / Orphan Janitor | 🔴 | ⚫ PLACEHOLDER | Photos served; orphans known to exist (per prior audits) | No per-photo delete endpoint; no orphan janitor; no audit | Storage waste; broken refs accumulate; R2 governance risk | Admin | `routes/job_photos.py`; `job_photos` | `OPERATIONAL_LIFECYCLE_MATRIX.md` row 29 | Phase 2 | NO | YES | YES | YES |
| OC-010 | Status vocabulary fragmentation | 🔴 | 🟡 PARTIAL (cross-cutting) | 18 distinct vocabs in use | No canonical vocab map; consumers disagree | Executive sees different "status" on same record across surfaces | All | `STATUS_VOCABULARY_AUDIT.md` | same | Phase 3 (cross-cutting refactor · NOT authorized in this audit) | NO (cosmetic in many cases) | YES | YES | YES |

### 🟡 IMPORTANT (8 findings)

| ID | Workflow | Severity | Classification | What exists | What is missing | Recommended phase | Blocks current ops? | Customer #2? |
|---|---|---|---|---|---|---|---|---|
| OC-011 | FL Forms post-submit edit | 🟡 | 🟡 PARTIAL | Create + view + delete | No PATCH; signed boolean is per-kind only; no status across kinds | Phase 3 | NO | NO |
| OC-012 | Safety Training (form) renewal linkage | 🟡 | 🟡 PARTIAL | Create + view; canonical Training Records is patchable | Linkage from training form to canonical record not enforced | Phase 3 | NO | NO |
| OC-013 | Employee Onboarding multi-step | 🟡 | 🟡 PARTIAL | Single-record create with active flag | No multi-step orientation/I-9/training-assign checklist | Phase 2 | NO | YES |
| OC-014 | Employee Offboarding multi-step | 🟡 | 🟡 PARTIAL | Status mutator + summary endpoint | No checklist forcing PPE return + access deactivation + exit | Phase 2 | YES | YES |
| OC-015 | Time Verification dispute/resolve | 🟡 | 🟡 PARTIAL | Read-only view + CSV export | No per-row dispute marker; no resolution audit | Phase 2 | NO | YES |
| OC-016 | Continuity Events edit / close | 🟡 | 🟡 PARTIAL | Create + list | No edit / no close | Phase 3 | NO | NO |
| OC-017 | Manual safety digest fire lives in Admin (Safety friction) | 🟡 | 🟡 PARTIAL | Admin-only `/admin/digest-config` | Safety officer must impersonate admin | Phase 3 (UI surface relocation) | NO | NO |
| OC-018 | Audit-trail gaps in flag-only history workflows | 🟡 | 🟡 PARTIAL | 21 workflows have flag-only history | 11 of them are forensic-critical (CAPA · Asset Transfers · Fleet Defects · DVIR · Suppliers · Jobs · Equipment Master · Documents · Time Off · Document Expirations · Vendors) | Phase 4 | NO | YES |

### 🟢 MINOR (3 findings)

| ID | Workflow | Severity | Detail | Phase |
|---|---|---|---|---|
| OC-019 | Casing inconsistency (`Open` vs `open`, `Closed` vs `closed`) | 🟢 | Same status concept, different casing across collections | Phase 4 |
| OC-020 | Status pill always shows OPEN on `SafetyIncidents.jsx` (list endpoint strips field) | 🟢 | Cosmetic — every incident shows OPEN regardless of stored value | Phase 1A (along with OC-001) |
| OC-021 | Project Health "Unresolved high/critical" count grows unbounded | 🟢 | `resolution_status != "Closed"` query · no producer for "Closed" | Phase 1A |

### ⚫ PLACEHOLDER (1 finding · also in CRITICAL)

| ID | Workflow | Detail |
|---|---|---|
| OC-022 | Reopen actions across the platform | 17 workflows show "close" but only 3 show "reopen" · once closed, only admin DB write can reopen |

---

## 3 · Aggregate

| Severity | Findings |
|---|---|
| 🔴 CRITICAL | 10 |
| 🟡 IMPORTANT | 8 |
| 🟢 MINOR | 3 |
| ⚫ PLACEHOLDER | 1 |
| **Total** | **22** |

---

## 4 · Findings × strategic gates

| Gate | # findings that block it |
|---|---|
| **MASCI daily operations today** | 6 (OC-001, OC-002, OC-003, OC-004, OC-007, OC-014) |
| **Customer #2 readiness (ForgedOps)** | 16 (all 🔴 + most 🟡) |
| **White Label readiness** | 16 (status vocab fragmentation + workflow incompleteness make per-tenant overrides unsafe) |
| **ForgedOps Operations Center readiness** | 12 (the operations center will read the same workflow data; gaps propagate) |

---

## 5 · Cross-finding themes

| Theme | IDs |
|---|---|
| "Create-and-forget" workflows (5 of 9 zero-status workflows) | OC-001 OC-002 OC-003 OC-004 OC-005 OC-006 |
| Missing audit collections | OC-018 + parts of OC-001 OC-007 |
| Vocabulary fragmentation | OC-010 OC-019 OC-020 |
| Missing return / reconciliation | OC-008 OC-009 OC-022 |
| Multi-step lifecycle absent | OC-013 OC-014 OC-007 |

---

## 6 · OMEGA discipline

🟢 22 findings catalogued · severity-assigned · phase-grouped · no remediation initiated.

🛑 Continue to `OPERATIONAL_COMPLETENESS_EXECUTIVE_SUMMARY.md` for the operator-facing one-pager.
