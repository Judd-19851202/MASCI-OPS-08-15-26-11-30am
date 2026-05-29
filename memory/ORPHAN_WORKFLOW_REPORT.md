# Orphan Workflow Report

_Phase V.5 · P0 Platform Trust Restoration · 2026-05-29 20:48 UTC._

> A workflow is classified ORPHAN when it satisfies ANY of:
> 1. Record exists but no owner exists
> 2. Record exists but no notification path exists
> 3. Record exists but no dashboard destination exists
> 4. Record exists but no next-step authority is defined

## 1 · Confirmed orphans (P0)

### ORPHAN-1 · Fleet DVIR
- **Record location**: `db.fleet_dvirs` (presumed; route file `backend/routes/fleet_ops.py` referenced but no notify wiring found)
- **Notification path**: NONE confirmed
- **Dashboard surface**: NONE confirmed (no "Open DVIRs" card on Dispatch or Shop hub)
- **Next-step authority**: undefined
- **Classification**: **P0 orphan candidate** — pending operator clarification of whether DVIR is operationally actionable or purely informational ledger
- **Operator question**: "Should a Fleet DVIR with a recorded defect drive a Shop / Dispatch task and notification? If yes, this orphan needs immediate closure."

## 2 · Soft orphans (P1 — exist but visibility incomplete)

### SOFT-1 · Field Leadership 10 forms
- **Notification**: ✅ email to safety + admin (`leadership_always_to`)
- **Dashboard surface**: search-only (admin FL forms list, FL Portal forms list)
- **Soft-orphan rationale**: email arrives in inboxes but there's no actionable "open FL forms" stat card on Safety or Admin hubs. Records reach the email recipients but don't surface as a "things to act on" queue.

### SOFT-2 · Safety Equipment Issuance / Training / Return
- **Notification**: ✅ email to `safety_forms_to`
- **Dashboard surface**: admin Safety Forms list · Safety Hub "Open Safety Forms" card (count-only, not actionable per-record)
- **Soft-orphan rationale**: same pattern as SOFT-1

### SOFT-3 · JHA (Job Hazard Analysis)
- **Notification**: ✅ email to safety + always_cc
- **Dashboard surface**: admin JHA list (search-only)
- **Soft-orphan rationale**: no task fan-out, no stat card on Safety Hub Primary Operations section

### SOFT-4 · Training Records (supervisor lens)
- **Notification**: ✅ employee bell + task
- **Soft-orphan rationale**: the supervisor of the trainee does not get a notification because `linked_supervisor` lookup is intermittent. Supervisors who want to know "what training is my crew owing?" have to navigate to the HR / Safety Training Records page and filter.

## 3 · Not orphans (validated complete chains)

For audit completeness — these workflows have all four pillars (owner · notification · dashboard · next-step):

- Daily Report
- Equipment Pre-Op (PASS and FAIL paths)
- Shop Recovery / Asset Transfer
- PO Request lifecycle (submit · approve / reject / clarify · receipt upload · close)
- Incident Report
- Safety Meeting
- Safety Inspection
- QA/QC (Concrete / Rebar / Subwork / Material Testing)
- Corrective Action
- Fire Extinguisher Inspection
- Dispatch Request
- Document Expiration
- Time Verification (read-only ledger — no event to orphan)
- Payroll Variance (weekly cron handles the system path; manual run is HR-Manager-driven so the "owner" IS the runner)
- Backup success rows (admin Backup Health panel)
- System Health outages

## 4 · Black-hole risk classification

| Workflow | Disappear risk? | Operator-perceived trust impact |
|---|---|---|
| ORPHAN-1 (Fleet DVIR) | **HIGH** — record exists but no human is told | "submitted DVIR · nobody knows" |
| SOFT-1 (FL forms) | LOW — email reaches recipients | "no dashboard list of forms my team submitted" |
| SOFT-2 (Safety forms) | LOW | same |
| SOFT-3 (JHA) | LOW | "did the safety supervisor SEE my JHA?" |
| SOFT-4 (Training supervisor) | MEDIUM — supervisor can be blindsided | "my crew missed training and I never knew" |

## 5 · Recommended classification per operator rubric

| ID | Operator rubric tier |
|---|---|
| ORPHAN-1 (Fleet DVIR) | **P0** — pending clarification |
| SOFT-1 (FL forms) | P1 |
| SOFT-2 (Safety forms) | P1 |
| SOFT-3 (JHA) | P1 |
| SOFT-4 (Training supervisor) | P1 |

## 6 · No-response paths

The audit confirms that **no workflow currently has a defined operator
process for "what happens if the owner doesn't respond"**, except:

- PO Requests — nightly cron creates approval-needed task, receipt-missing task
- Equipment Pre-Op FAIL — task remains open in Shop queue indefinitely
- Document Expirations — nightly cron task to HR

All other workflows rely on the human recipient to act. If they don't,
the workflow exists in the DB but has no escalation. This is the
"trust-killing black hole" pattern the operator warned about.

**Severity**: P2 across the board (no current operational catastrophe;
opportunity for a future "escalation framework" hardening pass).

## 7 · Stop condition

Audit only. No remediation begun. Operator owns the call on which (if any) orphans to close.

---

_End of ORPHAN_WORKFLOW_REPORT.md._
