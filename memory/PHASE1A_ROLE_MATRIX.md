# Phase 1A · Role Matrix

**Program:** OMEGA · Platform Completion Program · Phase 1A · DESIGN
**Companion:** `PHASE1A_WORKFLOW_DESIGN.md` · `PHASE1A_STATE_MACHINE.md` (6 workflows · OC-005 elevated iter449)
**Mode:** Design-only · no code
**Date:** 2026-06-01

---

## 0 · Legend

| Symbol | Meaning |
|---|---|
| ✅ | Role can perform this transition |
| ❌ | Role cannot perform this transition |
| 🟢 | Role can perform AND should see the button in UI |
| 🟡 | Role can perform via API but UI hides the button (admin-only path) |
| (auto) | Transition is system-triggered, no actor role |

Roles: **SA** = Super-Admin · **A** = Admin · **S** = Safety · **HR** = HR · **PM** = PM (must be assigned to the job) · **D** = Dispatch · **Sh** = Shop · **FL** = Field Leadership · **F** = Field submitter (the original DR submitter) · **E** = Employee (no portal)

---

## 1 · Incidents

| Transition | SA | A | S | HR | PM | D | Sh | FL | F | E | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| OPEN → IN_PROGRESS | 🟢 | 🟢 | 🟢 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | Safety initiates investigation |
| OPEN → PENDING_REVIEW (direct) | 🟢 | 🟢 | 🟢 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | only when `corrected_on_site == "Yes"` |
| IN_PROGRESS → PENDING_REVIEW | 🟢 | 🟢 | 🟢 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | — |
| IN_PROGRESS → PENDING_CLOSURE | (auto) | (auto) | (auto) | n/a | n/a | n/a | n/a | n/a | n/a | n/a | triggered on first CAPA link |
| PENDING_CLOSURE → PENDING_REVIEW | (auto) | (auto) | (auto) | n/a | n/a | n/a | n/a | n/a | n/a | n/a | triggered on last CAPA closure |
| PENDING_CLOSURE → IN_PROGRESS (reopen) | 🟢 | 🟢 | 🟢 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | reason required |
| PENDING_REVIEW → CLOSED | 🟢 | 🟢 | 🟢 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | attestation + (OSHA gate if applicable) |
| PENDING_REVIEW → CLOSED (OSHA override) | 🟢 | 🟡 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | Super-Admin or Admin only · reason mandatory |
| CLOSED → IN_PROGRESS (reopen) | 🟢 | 🟢 | 🟢 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | reason required |

**Read access (View state · timeline):** SA · A · S · HR (read) · PM (job-scoped) · FL (job-scoped).

---

## 2 · Daily Report

| Transition | SA | A | S | HR | PM | D | Sh | FL | F | E | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| OPEN → IN_PROGRESS | 🟢 | 🟢 | ❌ | ❌ | 🟢¹ | ❌ | ❌ | ❌ | ❌ | ❌ | PM assigned to the job |
| IN_PROGRESS → CLOSED (approve) | 🟢 | 🟢 | ❌ | ❌ | 🟢¹ | ❌ | ❌ | ❌ | ❌ | ❌ | hours attestation checkbox required; incident-link guard if applicable |
| IN_PROGRESS → OPEN (return-to-field) | 🟢 | 🟢 | ❌ | ❌ | 🟢¹ | ❌ | ❌ | ❌ | ❌ | ❌ | `return_reason` required; notifies original submitter |
| OPEN → OPEN (re-submission via PATCH) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 🟢² | ❌ | only original submitter; only while `return_reason` is set |
| CLOSED → IN_PROGRESS (reopen) | 🟢 | 🟢 | ❌ | ❌ | 🟢¹ | ❌ | ❌ | ❌ | ❌ | ❌ | reason required |

¹ PM must be assigned (`project_manager` or co-PM) to the report's job
² "Field" here = the submitter; identified via existing submission token mechanism

**Read access:** SA · A · S · HR (read) · PM (job-scoped) · FL (job-scoped) · F (own).

---

## 3 · Payroll Variance Batch

| Transition | SA | A | S | HR | PM | D | Sh | FL | F | E | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| OPEN → IN_PROGRESS | (auto) | (auto) | n/a | (auto) | n/a | n/a | n/a | n/a | n/a | n/a | triggered on first row decision |
| IN_PROGRESS → PENDING_REVIEW | (auto) | (auto) | n/a | (auto) | n/a | n/a | n/a | n/a | n/a | n/a | triggered when all rows decided |
| PENDING_REVIEW → IN_PROGRESS (revert) | 🟢 | 🟢 | ❌ | 🟢 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | implicit when a row's decision is cleared |
| PENDING_REVIEW → CLOSED (finalize) | 🟢 | 🟢 | ❌ | 🟢 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | Sandy attestation required |
| CLOSED → IN_PROGRESS (reopen) | 🟢 | 🟢 | ❌ | 🟢 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | reason required |

**Read access:** SA · A · HR · (Admin can see all; HR sees their own batches; others ❌).

---

## 4 · QA/QC Inspection · Inspection-level

| Transition | SA | A | S | HR | PM | D | Sh | FL | F | E | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| OPEN → IN_PROGRESS | 🟢 | 🟢 | ❌ | ❌ | 🟢¹ | ❌ | ❌ | ❌ | ❌ | ❌ | PM assigned to job |
| IN_PROGRESS → PENDING_REVIEW | (auto) | (auto) | n/a | n/a | (auto) | n/a | n/a | n/a | n/a | n/a | triggered when all deficiencies non-OPEN |
| PENDING_REVIEW → CLOSED | 🟢 | 🟢 | ❌ | ❌ | 🟢¹ | ❌ | ❌ | ❌ | ❌ | ❌ | every deficiency CLOSED |
| PENDING_REVIEW → IN_PROGRESS (revert) | (auto) | (auto) | n/a | n/a | (auto) | n/a | n/a | n/a | n/a | n/a | triggered when a deficiency reverts |
| CLOSED → IN_PROGRESS (reopen) | 🟢 | 🟢 | ❌ | ❌ | 🟢¹ | ❌ | ❌ | ❌ | ❌ | ❌ | reason required |

## 5 · QA/QC Inspection · Deficiency-level

| Transition | SA | A | S | HR | PM | D | Sh | FL | F | E | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| OPEN → IN_PROGRESS (assign) | 🟢 | 🟢 | ❌ | ❌ | 🟢¹ | ❌ | ❌ | ❌ | ❌ | ❌ | `assigned_to` field required |
| IN_PROGRESS → PENDING_REVIEW (claim resolved) | 🟢 | 🟢 | ❌ | ❌ | 🟢¹ | ❌ | ❌ | 🟢² | ❌ | ❌ | crew claims resolution; FL allowed if their crew is assigned |
| PENDING_REVIEW → CLOSED (verify) | 🟢 | 🟢 | ❌ | ❌ | 🟢¹ | ❌ | ❌ | ❌ | ❌ | ❌ | PM verifies |
| PENDING_REVIEW → IN_PROGRESS (reject verification) | 🟢 | 🟢 | ❌ | ❌ | 🟢¹ | ❌ | ❌ | ❌ | ❌ | ❌ | reason required |
| CLOSED → IN_PROGRESS (reopen deficiency) | 🟢 | 🟢 | ❌ | ❌ | 🟢¹ | ❌ | ❌ | ❌ | ❌ | ❌ | reason required |

¹ PM = job-scoped
² FL = scoped to crew the deficiency is assigned to

---

## 6 · Site Inspection · Inspection-level

| Transition | SA | A | S | HR | PM | D | Sh | FL | F | E | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| OPEN → IN_PROGRESS | 🟢 | 🟢 | 🟢 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | Safety initiates review |
| IN_PROGRESS → PENDING_REVIEW | (auto) | (auto) | (auto) | n/a | n/a | n/a | n/a | n/a | n/a | n/a | all findings non-OPEN |
| PENDING_REVIEW → CLOSED | 🟢 | 🟢 | 🟢 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | every finding CLOSED |
| CLOSED → IN_PROGRESS (reopen) | 🟢 | 🟢 | 🟢 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | reason required |

## 7 · Site Inspection · Finding-level

| Transition | SA | A | S | HR | PM | D | Sh | FL | F | E | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| OPEN → IN_PROGRESS (assign) | 🟢 | 🟢 | 🟢 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | — |
| IN_PROGRESS → PENDING_REVIEW (claim resolved) | 🟢 | 🟢 | 🟢 | ❌ | 🟢¹ | ❌ | ❌ | 🟢² | ❌ | ❌ | PM allowed if their job; FL allowed if their crew |
| PENDING_REVIEW → CLOSED (verify) | 🟢 | 🟢 | 🟢 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | Safety verifies |
| PENDING_REVIEW → IN_PROGRESS (reject) | 🟢 | 🟢 | 🟢 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | reason required |
| CLOSED → IN_PROGRESS (reopen) | 🟢 | 🟢 | 🟢 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | reason required |

---

## 7 · Site Inspection · Finding-level

| Transition | SA | A | S | HR | PM | D | Sh | FL | F | E | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| OPEN → IN_PROGRESS (assign) | 🟢 | 🟢 | 🟢 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | — |
| IN_PROGRESS → PENDING_REVIEW (claim resolved) | 🟢 | 🟢 | 🟢 | ❌ | 🟢¹ | ❌ | ❌ | 🟢² | ❌ | ❌ | PM allowed if their job; FL allowed if their crew |
| PENDING_REVIEW → CLOSED (verify) | 🟢 | 🟢 | 🟢 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | Safety verifies |
| PENDING_REVIEW → IN_PROGRESS (reject) | 🟢 | 🟢 | 🟢 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | reason required |
| CLOSED → IN_PROGRESS (reopen) | 🟢 | 🟢 | 🟢 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | reason required |

---

## 7.5 · JHA Acknowledgement Ledger (OC-005)

JHA acknowledgement is NOT a state-machine workflow. It is a single-event audit ledger. The "transitions" below are actually distinct ACTIONS on the ledger.

| Action | SA | A | S | HR | PM | D | Sh | FL | F | E | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Submit acknowledgement (POST /acknowledgements) — crew member signs | 🟢 | 🟢 | 🟢 | ❌ | ❌ | ❌ | ❌ | 🟢 | 🟢¹ | 🟢² | F = via public QR-token submission; E = same as F |
| Attest acknowledgement (verbal · FL/Safety witnesses) | 🟢 | 🟢 | 🟢 | ❌ | ❌ | ❌ | ❌ | 🟢 | ❌ | ❌ | when crew member cannot sign (gloves, tablet not available) |
| View ledger (per-JHA, per-job) | 🟢 | 🟢 | 🟢 | 🟢 (read) | 🟢³ | ❌ | ❌ | 🟢⁴ | 🟢¹ | ❌ | HR read-only; PM job-scoped; FL crew-scoped |
| View coverage dashboard (/safety/jha-acknowledgements) | 🟢 | 🟢 | 🟢 | 🟢 (read) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | Safety/Admin only |
| Soft-delete ack row (with reason) | 🟢 | 🟢 | 🟢 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | Safety only; reason required; audit_events row written |
| Restore soft-deleted ack | 🟢 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | Super-Admin only |

¹ F = crew member via signed QR token (same pattern as Daily Report public submission)
² E = same as F via QR
³ PM scoping = job assignment
⁴ FL scoping = crew assignment

**Read access (ledger):** SA · A · S · HR (read) · PM (job-scoped) · FL (crew-scoped) · F (own submissions via token).

**No closure / no reopen / no transitions.** Each row is OSHA evidence on creation.

---

## 8 · Cross-cutting role authorities

### 8.1 · Super-Admin overrides

Super-Admin is authorized to perform ANY transition on ANY workflow with a `reason` always required. This is the platform's break-glass authority. Logged with elevated `actor_role: "super-admin-override"` for audit cross-reference.

### 8.2 · Admin scope

Admin has the same authority as Safety / PM / HR within the role's scope. Admin can transition on any workflow within the platform.

### 8.3 · Per-job scoping for PM

PM authorization is gated on `(jobs_master.project_manager == pm_user_id OR pm_user_id ∈ jobs_master.co_pms)`. Existing scoping in `pm_portal_deps.py` is the source of truth.

### 8.4 · Per-crew scoping for FL

FL authorization on QA/QC and Site Inspection findings is gated on `(deficiency.assigned_to == fl_crew OR finding.assigned_to == fl_crew)`. Mapping uses existing FL crew assignment in `field_leadership_records`.

### 8.5 · Read access for HR

HR has READ-only access to all 5 workflows' state and history. HR cannot transition Incidents, DR, QA/QC, Site Inspections (intentionally aligned with prior "HR owns OSHA recordkeeping; Safety closes incidents" doctrine).

### 8.6 · Public submitters (F)

* Daily Report: can re-submit a returned-to-field DR (transitions OPEN → OPEN with revision_count++ via PATCH).
* All other workflows: cannot transition.

---

## 9 · Authority conflict resolution

When two roles both have authority on the same transition (e.g., PM and Admin both can close a DR), the audit row records the actual actor. There is no "tie-breaker" — first writer wins, second writer hits 409.

---

## 10 · Operational closure-authority summary

| Workflow | Primary closer | Secondary closer | Tertiary (break-glass) |
|---|---|---|---|
| Incidents | Safety | Admin | Super-Admin |
| Daily Reports | PM (assigned) | Admin | Super-Admin |
| Payroll Variance Batches | HR | Admin | Super-Admin |
| QA/QC Inspections (inspection-level) | PM (assigned) | Admin | Super-Admin |
| QA/QC Deficiencies | PM (assigned) | Admin | Super-Admin |
| Site Inspections (inspection-level) | Safety | Admin | Super-Admin |
| Site Findings | Safety | Admin | Super-Admin |
| JHA Acknowledgement Ledger (OC-005) | (no closure · per-row evidence) | n/a | n/a (Safety can soft-delete with reason) |

---

## 11 · OMEGA discipline

🟢 Design-only · role matrix · 5 workflows × 9 roles × 11 transitions covered.

🛑 Continue to `PHASE1A_CERTIFICATION_PLAN.md`.
