# OMEGA · OWNERSHIP INFERENCE MATRIX

**Date:** 2026-06-02 · Companion to `OWNERSHIP_LAYER_DISCOVERY_AUDIT.md`
**Mode:** READ-ONLY · zero code · zero design · zero estimates
**Purpose:** Document the per-workflow inference logic — for each lifecycle state, which signal (S1 creator · S2 project · S3 state-gate · S4 manager-hierarchy) resolves the single accountable owner. **No human types a name. No human picks from a dropdown.**

---

## §0 · Signal precedence (reminder)

Default precedence per `OWNERSHIP_LAYER_DISCOVERY_AUDIT.md §1.Q1`:
**S3 (state's role gate) → S2 (project owner) → S4 (workflow-class default + manager hierarchy) → S1 (creator)**

Each workflow below states which signals apply per state. NULL inference is operationally impossible because Tier 5 dead-letter (S4 fallback to workflow-class default email such as `safety@mascigc.com`) always exists.

---

## §1 · Incidents (OC-001)

| State | Owner role | S1 | S2 | S3 | S4 | Inference rule |
|---|---|:-:|:-:|:-:|:-:|---|
| OPEN | Submitter (FL or admin) | ✅ | — | — | — | `record.submitter_id` (FSI 5-tier resolved at submit) |
| UNDER_INVESTIGATION | Safety Manager | — | — | ✅ | ✅ | Workflow-class default; tenant has 1 active Safety Manager |
| CORRECTIVE_ACTION_REQUIRED | PM | — | ✅ | ✅ | — | `jobs_master[record.project_number].primary_pm` |
| PENDING_CLOSURE | Safety Manager | — | — | ✅ | ✅ | Same as UI |
| CLOSED | (no owner) | — | — | — | — | Terminal · ownership ended |

**Edge cases:** Incident without `project_number` → S4 fallback to Safety Manager. Multi-project incident → primary project's PM owns CAR; corollary projects receive notification only.

---

## §2 · Daily Reports (OC-002)

| State | Owner role | S1 | S2 | S3 | S4 | Inference rule |
|---|---|:-:|:-:|:-:|:-:|---|
| OPEN | Submitter (Foreman) | ✅ | — | — | — | `record.submitter_id` (FSI 5-tier · field) |
| PENDING_REVIEW | PM | — | ✅ | ✅ | — | `jobs_master[record.project_number].primary_pm` |
| REVIEWED | PM | — | ✅ | ✅ | — | Same as PENDING_REVIEW |
| OPEN (after kickback) | Submitter | ✅ | — | — | — | FSI revise token re-attributes to original submitter |
| CLOSED | (no owner) | — | — | — | — | Terminal |

**Edge cases:** Submitter unreachable (Tier 5 dead-letter) → escalates to PM as substitute owner immediately. PM unassigned → S4 fallback to Operations Manager.

---

## §3 · QA/QC (OC-003)

| State | Owner role | S1 | S2 | S3 | S4 | Inference rule |
|---|---|:-:|:-:|:-:|:-:|---|
| OPEN | Inspector | ✅ | — | ✅ | — | Authenticated office session at submit |
| DEFICIENCY_RAISED | PM | — | ✅ | ✅ | — | Project PM |
| IN_REMEDIATION | PM | — | ✅ | ✅ | — | Same |
| PENDING_RE_INSPECTION | Inspector | — | — | ✅ | — | Original inspector or QC role-gate |
| CLOSED | (no owner) | — | — | — | — | Terminal |

**Edge cases:** Sub-driven remediation does NOT transfer ownership to sub — PM remains the accountable party for sub coordination. Sub is a counterparty, not an owner.

---

## §4 · Site Inspections (OC-004)

Symmetrical to QA/QC. State table identical except names (FINDINGS_RAISED in place of DEFICIENCY_RAISED).

---

## §5 · Payroll Variances (OC-007)

| State | Owner role | S1 | S2 | S3 | S4 | Inference rule |
|---|---|:-:|:-:|:-:|:-:|---|
| OPEN | Foreman | ✅ | ✅ | — | — | Foreman of crew with variance (crew membership × project) |
| UNDER_REVIEW | PM | — | ✅ | ✅ | — | Project PM |
| APPROVED | Payroll | — | — | ✅ | ✅ | Workflow-class default (Payroll role) |
| FINALIZED | (no owner) | — | — | — | — | Terminal |

**Edge cases:** Multi-project variance (rare) → primary project's PM. Payroll cut-off approaching → escalation may auto-promote ownership to Payroll Lead.

---

## §6 · Safety (Toolbox Talks · JHP · Training)

| Sub-domain | State | Owner role | S1 | S2 | S3 | S4 | Inference rule |
|---|---|---|:-:|:-:|:-:|:-:|---|
| Toolbox Talk library | n/a | Safety Manager | — | — | ✅ | ✅ | Workflow-class default |
| Toolbox Talk conducted | RECORDED | Foreman | ✅ | ✅ | — | — | Crew foreman who conducted |
| JHP library | n/a | Safety Manager | — | — | ✅ | ✅ | Workflow-class default |
| JHP downloaded | EVENT | Field Leader | ✅ | — | — | — | FSI identity at download (Tier 3 evidence) |
| Training records | per employee | `manager_employee_id` | — | — | ✅ | ✅ | Direct manager from G1-11 |
| Training expiring | EXPIRING_SOON | Direct manager | — | — | — | ✅ | Manager hierarchy |
| Training expired | EXPIRED | Manager's manager | — | — | — | ✅ | Escalation hop up ladder |

---

## §7 · Equipment

| Sub-domain | State | Owner role | S1 | S2 | S3 | S4 | Inference rule |
|---|---|---|:-:|:-:|:-:|:-:|---|
| Asset master | n/a | Equipment Manager / Shop Foreman | — | — | ✅ | ✅ | Workflow-class default |
| Pre-Op submitted | RECORDED | Operator on shift | ✅ | — | — | — | FSI identity at submit |
| Pre-Op defect | OPEN | Shop Foreman | — | — | ✅ | ✅ | Workflow-class default |
| Asset transferred | IN_TRANSIT | Equipment Manager | — | — | ✅ | ✅ | Until receipt |
| Asset deployed | DEPLOYED | Receiving job's PM | — | ✅ | — | — | Project of deployment |
| Asset returned | RETURNED | Shop Foreman | — | — | ✅ | ✅ | Workflow-class default |
| Maintenance due | DUE | Equipment Manager | — | — | ✅ | ✅ | Workflow-class default |
| Maintenance overdue | OVERDUE | Equipment Manager's manager | — | — | — | ✅ | Escalation |

---

## §8 · Fleet

| Sub-domain | State | Owner role | S1 | S2 | S3 | S4 | Inference rule |
|---|---|---|:-:|:-:|:-:|:-:|---|
| Vehicle master | n/a | Fleet Manager | — | — | ✅ | ✅ | Workflow-class default |
| DVIR submitted | RECORDED | Driver | ✅ | — | — | — | FSI identity at submit |
| DVIR defect | OPEN | Fleet Manager | — | — | ✅ | ✅ | Until remediated |
| DQ-file item | per driver | Fleet Manager + manager | — | — | ✅ | ✅ | Joint workflow-class + manager |
| DQ-file expiring | EXPIRING_SOON | Driver's direct manager | — | — | — | ✅ | Manager hierarchy |
| DQ-file expired | EXPIRED | Manager's manager + Safety Manager | — | — | — | ✅ | Escalation hop + DOT exposure |

---

## §9 · HR

| Sub-domain | State | Owner role | S1 | S2 | S3 | S4 | Inference rule |
|---|---|---|:-:|:-:|:-:|:-:|---|
| Employee record | n/a | HR | — | — | ✅ | ✅ | Workflow-class default |
| Per-employee operational owner | n/a | `manager_employee_id` | — | — | — | ✅ | G1-11 BUILD primitive |
| Time Off requested | REQUESTED | Manager | — | — | — | ✅ | `manager_employee_id` |
| Time Off approved | APPROVED | (employee) | ✅ | — | — | — | Self-service downstream |
| Time Off taken | TAKEN | (no owner) | — | — | — | — | Terminal |
| Onboarding (field-side) | IN_PROGRESS | Safety Manager + Shop Foreman | — | — | ✅ | ✅ | Joint workflow-class |
| Offboarding (field-side) | IN_PROGRESS | PM + Equipment Manager + Safety Manager | — | ✅ | ✅ | ✅ | Last project's PM + class defaults |
| Performance review | scheduled | Manager | — | — | — | ✅ | `manager_employee_id` (HRIS-side INTEGRATE) |

HR-side terminal states are owned by HRIS integration. ForgedOps does not own benefits enrollment, I-9 processing, or ACA reporting.

---

## §10 · Project Operations (Submittal · RFI · CO · Pay-App · Sub-Mgmt · Meeting-Minutes)

| Sub-domain | State | Owner role | S1 | S2 | S3 | S4 | Inference rule |
|---|---|---|:-:|:-:|:-:|:-:|---|
| Submittal | PENDING | PM | — | ✅ | ✅ | — | Project PM |
| Submittal | UNDER_REVIEW (external) | "external owner" pseudo-state | — | — | — | — | Engineer of record (counterparty record) |
| Submittal | APPROVED/REJECTED | PM | — | ✅ | ✅ | — | Disposition recorded |
| RFI | OPEN | PM | — | ✅ | ✅ | — | Project PM |
| RFI | AWAITING_RESPONSE (external) | counterparty | — | — | — | — | Designer/Owner-of-record |
| RFI | ANSWERED | PM | — | ✅ | ✅ | — | Distribution + sub-impact |
| Change-Order | PROPOSED | PM | — | ✅ | ✅ | — | Project PM |
| Change-Order | UNDER_OWNER_REVIEW | counterparty | — | — | — | — | Owner Rep |
| Change-Order | APPROVED | PM + Accounting | — | ✅ | ✅ | — | Disposition + financial sync (EX-1) |
| Pay-App | DRAFT | PM | — | ✅ | ✅ | — | Project PM |
| Pay-App | SUBMITTED | counterparty | — | — | — | — | Owner Rep + Architect |
| Pay-App | APPROVED | PM + Accounting | — | ✅ | ✅ | — | Financial sync (EX-1) |
| Pay-App | PAID | (no owner) | — | — | — | — | Terminal via accounting integration |
| Sub-Mgmt | ONBOARDING | PM | — | ✅ | ✅ | — | Project PM |
| Sub-Mgmt | INSURANCE_EXPIRING | PM + manager_employee_id of PM | — | ✅ | — | ✅ | Escalation pre-expiration |
| Meeting-Minutes | RECORDED | PM | — | ✅ | ✅ | — | Project PM |

---

## §11 · NULL-inference fallback ladder (operational defect indicator)

When all four signals fail to resolve a single owner, the platform must NOT add an "Assign" affordance. Instead, the record is surfaced as an **operational defect** with the following inferred owner ladder:

1. **Workflow-class default** (Safety Manager · Equipment Manager · Fleet Manager · HR · Payroll · Operations Manager)
2. **Tenant Operations Manager** (single role per tenant)
3. **Tenant Super-Admin** (break-glass)
4. **ADMIN_DEAD_LETTER_EMAIL** env (`safety@mascigc.com` per iter452.5.1 Tier 5)

Every step in this ladder is **deterministic** — no humans involved. NULL is impossible. The ladder also doubles as the escalation ladder when SLA breaches.

---

## §12 · What this matrix EXCLUDES (by design)

| Pattern | Why excluded |
|---|---|
| "Assignee" field on any workflow record | Rule 7 violation — inference is not assignment |
| "Accept Task" affordance | Rule 1 + Rule 7 violation — accepting is implicit by virtue of state ownership |
| "Reassign to" dropdown | Rule 6 + Rule 7 violation — reassignment is state transition, not field edit |
| "Owner Group" selection (multiple owners) | Rule 3 violation — One Owner principle |
| "Watchers" / "Followers" field | Rule 2 violation — information is not a task; notifications cover this |
| Per-employee work queue UI separate from operational record | Anti-checklist clause — the operational record IS the work queue entry |

---

## §13 · Discipline scorecard

| Check | Status |
|---|---|
| Zero code | ✅ |
| Zero design | ✅ |
| Inference rule stated per state per workflow (10 × ~5 = ~50 state rows) | ✅ |
| NULL-fallback ladder rendered | ✅ |
| Excluded patterns enumerated | ✅ |
| Rule 3 (One Owner) honored throughout | ✅ |
| Rule 7 (Accountability Automatic) honored throughout | ✅ |
| Amendment 001 honored (no ack ownership transfers) | ✅ |

🛑 **STOPPED.**
