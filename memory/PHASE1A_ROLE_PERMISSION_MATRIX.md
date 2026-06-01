# Phase 1A · Role Permission Matrix (Final · 6 workflows)

**Program:** OMEGA · PCP · Phase 1A · Final Build Package
**Authoritative source:** `PHASE1A_ROLE_MATRIX.md` (extended for OC-005)
**Mode:** Design-only
**Date:** 2026-06-01

---

## 1 · Cross-workflow permission summary

### Roles
* **SA** = Super-Admin (break-glass — any transition with reason)
* **A** = Admin
* **S** = Safety
* **HR** = HR
* **PM** = PM (job-scoped where applicable)
* **D** = Dispatch
* **Sh** = Shop
* **FL** = Field Leadership (crew-scoped where applicable)
* **F** = Field submitter (original submitter · public token)
* **E** = Employee (no portal · public QR submission)

### Workflows
* I = Incidents (OC-001)
* DR = Daily Reports (OC-002)
* QI = QA/QC Inspection (OC-003)
* QD = QA/QC Deficiency (OC-003)
* SI = Site Inspection (OC-004)
* SF = Site Finding (OC-004)
* JA = JHA Acknowledgement Ledger (OC-005) — actions, not transitions
* PV = Payroll Variance Batch (OC-007)

---

## 2 · Master permission matrix (forward transitions only)

### 2.1 · CREATE / SUBMIT / INITIATE

| Workflow | SA | A | S | HR | PM | D | Sh | FL | F | E |
|---|---|---|---|---|---|---|---|---|---|---|
| Incident (create record) | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ |
| DR (create record) | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ |
| QI (create) | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ |
| SI (create) | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| JA (submit ack) | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| PV (create batch via CSV upload) | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

### 2.2 · START WORK · OPEN → IN_PROGRESS

| Workflow | SA | A | S | HR | PM | D | Sh | FL | F | E |
|---|---|---|---|---|---|---|---|---|---|---|
| I | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| DR | ✅ | ✅ | ❌ | ❌ | ✅¹ | ❌ | ❌ | ❌ | ❌ | ❌ |
| QI | ✅ | ✅ | ❌ | ❌ | ✅¹ | ❌ | ❌ | ❌ | ❌ | ❌ |
| QD (assign · OPEN→IN_PROGRESS) | ✅ | ✅ | ❌ | ❌ | ✅¹ | ❌ | ❌ | ❌ | ❌ | ❌ |
| SI | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| SF (assign) | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| PV (auto on first row decision) | (auto) | (auto) | n/a | (auto) | n/a | n/a | n/a | n/a | n/a | n/a |

### 2.3 · CLAIM RESOLVED · IN_PROGRESS → PENDING_REVIEW

| Workflow | SA | A | S | HR | PM | D | Sh | FL | F | E |
|---|---|---|---|---|---|---|---|---|---|---|
| I | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| QD (crew claims) | ✅ | ✅ | ❌ | ❌ | ✅¹ | ❌ | ❌ | ✅² | ❌ | ❌ |
| QI (auto on all deficiencies non-OPEN) | (auto) | (auto) | n/a | n/a | (auto) | n/a | n/a | n/a | n/a | n/a |
| SF (crew claims) | ✅ | ✅ | ✅ | ❌ | ✅¹ | ❌ | ❌ | ✅² | ❌ | ❌ |
| SI (auto) | (auto) | (auto) | (auto) | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| PV (auto on all rows decided) | (auto) | (auto) | n/a | (auto) | n/a | n/a | n/a | n/a | n/a | n/a |
| DR | n/a — skips PENDING_REVIEW | | | | | | | | | |
| JA | n/a — no states | | | | | | | | | |

### 2.4 · CLOSE · → CLOSED

| Workflow | SA | A | S | HR | PM | D | Sh | FL | F | E |
|---|---|---|---|---|---|---|---|---|---|---|
| I | ✅ (override) | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| DR | ✅ | ✅ | ❌ | ❌ | ✅¹ | ❌ | ❌ | ❌ | ❌ | ❌ |
| QI | ✅ | ✅ | ❌ | ❌ | ✅¹ | ❌ | ❌ | ❌ | ❌ | ❌ |
| QD (verify) | ✅ | ✅ | ❌ | ❌ | ✅¹ | ❌ | ❌ | ❌ | ❌ | ❌ |
| SI | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| SF (verify) | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| PV (finalize) | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| JA | n/a — no closure (immutable evidence) | | | | | | | | | |

### 2.5 · REOPEN · CLOSED → IN_PROGRESS (reason required)

| Workflow | SA | A | S | HR | PM | D | Sh | FL | F | E |
|---|---|---|---|---|---|---|---|---|---|---|
| I | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| DR | ✅ | ✅ | ❌ | ❌ | ✅¹ | ❌ | ❌ | ❌ | ❌ | ❌ |
| QI | ✅ | ✅ | ❌ | ❌ | ✅¹ | ❌ | ❌ | ❌ | ❌ | ❌ |
| QD | ✅ | ✅ | ❌ | ❌ | ✅¹ | ❌ | ❌ | ❌ | ❌ | ❌ |
| SI | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| SF | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| PV | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| JA | n/a (Super-Admin can restore soft-deleted ack with reason) | | | | | | | | | |

### 2.6 · ADMINISTRATIVE / OUT-OF-BAND

| Action | SA | A | S | HR | PM | D | Sh | FL | F | E |
|---|---|---|---|---|---|---|---|---|---|---|
| Cross-cutting admin view `/api/admin/workflow-state-events` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| JHA ack soft-delete (with reason) | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| JHA ack restore (after soft-delete) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| OSHA-recordable incident closure (with attestation) | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| OSHA-recordable incident closure (without attestation · override) | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

### 2.7 · READ ACCESS (state · history)

| Workflow | SA | A | S | HR | PM | D | Sh | FL | F | E |
|---|---|---|---|---|---|---|---|---|---|---|
| I | ✅ | ✅ | ✅ | ✅ | ✅¹ | ❌ | ❌ | ✅¹ | ❌ | ❌ |
| DR | ✅ | ✅ | ✅ | ✅ | ✅¹ | ❌ | ❌ | ✅¹ | ✅⁴ | ❌ |
| QI | ✅ | ✅ | ✅ | ❌ | ✅¹ | ❌ | ❌ | ✅¹ | ❌ | ❌ |
| QD | ✅ | ✅ | ✅ | ❌ | ✅¹ | ❌ | ❌ | ✅² | ❌ | ❌ |
| SI | ✅ | ✅ | ✅ | ❌ | ✅¹ | ❌ | ❌ | ✅¹ | ❌ | ❌ |
| SF | ✅ | ✅ | ✅ | ❌ | ✅¹ | ❌ | ❌ | ✅² | ❌ | ❌ |
| PV | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| JA (ledger view) | ✅ | ✅ | ✅ | ✅ (read) | ✅¹ | ❌ | ❌ | ✅² | ✅⁴ | ❌ |
| JA coverage dashboard | ✅ | ✅ | ✅ | ✅ (read) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

¹ PM/FL scoping = job-assigned (PM) or crew-assigned (FL)
² Crew-scoped for QD/SF/JA
³ HR is read-only on Safety domain (existing platform doctrine)
⁴ F can read their own submissions via the existing public-token flow

---

## 3 · Scoping rules (codified)

### 3.1 · PM job-scope

A PM is authorized on workflow X for job J iff:
```
J.project_manager == PM.user_id  OR  PM.user_id in J.co_pms
```
Existing helper: `lib/pm_portal_deps.py:assert_pm_scope_for_job`.

### 3.2 · FL crew-scope

An FL user is authorized on workflow X for crew C iff:
```
C in fl_user.assigned_crews  OR  fl_user.is_supervisor_for(C)
```
Existing helper: `lib/field_leadership_portal.py:assert_fl_scope_for_crew`.

### 3.3 · HR read-only on Safety

HR token can READ Incidents · QI · QD · SI · SF · JA. HR cannot transition any of them. Enforced at route level via `if role == "hr": raise 403`.

### 3.4 · Super-Admin override

Super-Admin can perform ANY transition on ANY workflow with `reason` always required. The audit row marks `actor_role="super-admin-override"`.

---

## 4 · Privacy / data exposure

Only Safety + Admin can view the FULL `workflow_state_events` history globally. Per-doc history reads scope by:
* PM: only their assigned jobs
* FL: only their crew's records
* HR: read-only on Safety domain
* Field/Employee submitters: only via public token (their own records)

Audit rows do NOT contain employee SSN/birthdate/sensitive PII. Display names + roles + reasons only.

---

## 5 · OMEGA discipline

🟢 Design-only · 6 workflows × 11 transitions/actions × 10 roles · scoping rules codified · privacy posture documented · 0 over-broad role grants.

🛑 Continue to `PHASE1A_BUILD_PLAN.md`.
