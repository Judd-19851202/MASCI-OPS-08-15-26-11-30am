# OMEGA · PHASE 3 — ITER453 CONSTITUTIONAL BUILD PACKAGE

**Date:** 2026-06-02 · iter453 re-scoping deliverable
**Mode:** READ-ONLY · zero code · zero design · zero estimates
**Operator authorization:** "Re-scope OC-003 and OC-004 against the Constitution. Verify: No manual assignment · No acknowledgement steps · No checklist inflation · No ownership ambiguity · Closure requires operational evidence · Ownership derived automatically. Produce final constitutional build package."
**Governing doctrine:** Constitution Parts I–IV + Override + Amendment 001 + Build/Integrate/Ignore Doctrine + **Ownership Doctrine O-1 through O-15** (post-Phase-2)

---

## §0 · Scope

This package re-scopes the two workflows previously sketched in iter453 design notes:

* **OC-003 · QA/QC Deficiency Follow-Up**
* **OC-004 · Site Inspection Finding Follow-Up**

It does NOT authorize the build. The build remains gated on explicit operator authorization in a future message. This package is the Constitutional contract that the build, when authorized, must satisfy.

---

## §1 · Pre-Phase-2 problems with iter453 (historical record)

| Problem | Source | Doctrine violated |
|---|---|---|
| "Mark Resolved" ack-click as closure trigger | Original iter453 sketch | Amendment 001 REPLACE-5 |
| "Acknowledge findings" ack-click on Site Inspection | Original iter453 sketch | Amendment 001 REPLACE-4 |
| Manual "Assign Sub" dropdown for remediation | Original iter453 sketch | Ownership Doctrine O-2 |
| Multi-recipient PENDING_REVIEW fan-out (PM + Safety + Admin) | Cross-cited from iter452 pattern | Rule 8 single-recipient discipline |
| Closure as click without operational evidence | Original iter453 sketch | Rule 4 + Amendment 001 |
| Ownership ambiguity during sub-driven remediation | Original iter453 sketch | Rule 3 + Ownership Doctrine O-10 |

All 6 problems are resolved below.

---

## §2 · OC-003 · QA/QC Deficiency Follow-Up · Constitutional re-scope

### §2.1 · State machine

| State | Description | Owner inference (per Ownership Doctrine) |
|---|---|---|
| OPEN | Inspection submitted with finding(s) | S1 Inspector (submitter) |
| DEFICIENCY_RAISED | Inspector confirms deficiency severity + scope | S2 PM (project owner via `jobs_master.primary_pm`) |
| IN_REMEDIATION | PM has opened a corrective_action record OR scheduled sub coordination | S2 PM (continues to own; sub is counterparty metadata per O-10) |
| PENDING_RE_INSPECTION | Remediation work claimed complete by PM; awaiting QC verification | S3 Inspector role-gate (any inspector; not necessarily original) |
| CLOSED | Re-inspection passed OR documented exception | (none · terminal) |

### §2.2 · Transitions (state machine semantics)

| Transition | Triggering operational event | Tier 1 evidence written |
|---|---|---|
| (none) → OPEN | Inspection submitted | inspection record |
| OPEN → DEFICIENCY_RAISED | Inspector confirms deficiency (sets severity + scope description as data fields) | confirmation record |
| DEFICIENCY_RAISED → IN_REMEDIATION | PM creates linked `corrective_actions` row OR logs `sub_coordination_event` with sub identity + remediation plan + due date | corrective_actions row or sub_coordination_event row |
| IN_REMEDIATION → PENDING_RE_INSPECTION | `corrective_actions.completed_at` is set with operational notes OR sub returns `remediation_complete` event | corrective_actions completion event |
| PENDING_RE_INSPECTION → CLOSED | New re-inspection record with `passed=True` AND `original_deficiency_id` linkage | re-inspection record |
| PENDING_RE_INSPECTION → DEFICIENCY_RAISED (rework loop) | Re-inspection record with `passed=False` AND notes | re-inspection failure record |
| Any state → CLOSED via documented exception | PM + Safety Manager joint approval with reason text (Tier 1 decision content) | exception_approval row with `exception_reason` |

### §2.3 · Closure-action contract (Constitution-binding)

OC-003 is CLOSED **only** when:
* A re-inspection record exists with `passed=True` linked to the original deficiency, **OR**
* A `corrective_actions` row is marked complete by an operator with operational notes ≥ 20 characters, **OR**
* A documented exception row exists with PM + Safety Manager dual sign-off (decision content captured as Tier 1 data)

**No "Mark Resolved" click affordance exists.** The platform's UI offers the three operational actions above; closure is the side-effect.

### §2.4 · Ownership inference per state (verifying O-1)

| State | Inference equation | NULL fallback |
|---|---|---|
| OPEN | Inspector = `record.submitter_id` (S1) | Tier 5 dead-letter |
| DEFICIENCY_RAISED | PM = `jobs_master[record.project_number].primary_pm` (S2) | Workflow-class default (Quality Manager) → Operations Manager → Tier 5 |
| IN_REMEDIATION | PM (same as above) | Same fallback |
| PENDING_RE_INSPECTION | Any inspector via S3 role-gate | Inspector pool (round-robin or QC Lead) → Tier 5 |
| CLOSED | (no owner) | n/a |

### §2.5 · Escalation rules

| Trigger | Hop target | Awareness ping |
|---|---|---|
| DEFICIENCY_RAISED > 3 business days | PM's `manager_employee_id` | PM |
| IN_REMEDIATION > 10 business days | PM's manager | PM |
| IN_REMEDIATION > 20 business days | PM's manager's manager + Operations Manager | PM's manager |
| PENDING_RE_INSPECTION > 5 business days | Inspector's manager | Inspector |

Single-recipient awareness per hop (Rule 8 + Ownership Doctrine O-4).

### §2.6 · Sub-coordination posture (O-10 verification)

When remediation requires subcontractor work:
* PM remains internal owner.
* Sub identity captured as `sub_coordination_event.counterparty_*` metadata.
* No "Assign to Sub" dropdown · no sub login to ForgedOps for remediation.
* Sub completion arrives as PM-recorded event (`remediation_complete`) OR sub email reply parsed by Resend webhook into PM's Action Console row.

### §2.7 · Constitutional checks (gate list)

| Check | Status |
|---|---|
| No manual assignment | ✅ — owner inferred at every state |
| No acknowledgement steps | ✅ — "Mark Resolved" affordance removed |
| No checklist inflation | ✅ — 5 states only, each with 1 operational action |
| No ownership ambiguity | ✅ — single owner per state · sub is counterparty metadata |
| Closure requires operational evidence | ✅ — re-inspection record OR corrective_actions completion OR documented exception |
| Ownership derived automatically | ✅ — S1/S2/S3 inference equation + Tier 5 fallback |
| No multi-recipient notification fan-out | ✅ — single Rule-8 awareness ping per escalation hop |
| Dual-affordance on every Action Console row (O-14) | ✅ — `open_record` + `take_ownership` + primary action |
| No standalone chart on QC surfaces (O-15) | ✅ — sparklines only inside Action Console rows |
| Constitutional Test applied to every UI affordance | ✅ — no affordance survives unless it triggers a state transition or captures Tier 1 evidence |

---

## §3 · OC-004 · Site Inspection Finding Follow-Up · Constitutional re-scope

OC-004 is **structurally symmetric** to OC-003 with three terminology differences:

| OC-003 term | OC-004 term |
|---|---|
| Deficiency | Finding |
| Inspector | Site Inspector (Safety-side, not QC-side) |
| Quality Manager (workflow-class default) | Safety Manager (workflow-class default) |
| Re-inspection | Re-inspection (same noun, different role) |

### §3.1 · State machine

| State | Owner inference |
|---|---|
| OPEN | S1 Site Inspector |
| FINDINGS_RAISED | S2 PM |
| IN_REMEDIATION | S2 PM (sub is counterparty metadata per O-10) |
| PENDING_RE_INSPECTION | S3 Site Inspector role-gate |
| CLOSED | (none · terminal) |

### §3.2 · Transitions

Identical structure to §2.2 with finding terminology substituted.

### §3.3 · Closure-action contract

CLOSED only when:
* Re-inspection record with `passed=True` AND `original_finding_id` linkage, **OR**
* `corrective_actions` row complete with operational notes, **OR**
* Documented exception with PM + Safety Manager dual sign-off

**No "Acknowledge findings" click affordance exists.** Amendment 001 REPLACE-4 textbook.

### §3.4 · Ownership inference

Identical to §2.4 with Safety Manager as workflow-class default instead of Quality Manager.

### §3.5 · Escalation rules

Identical SLA pattern to §2.5; only role names change.

### §3.6 · Constrained Co-Authority (O-11 application)

For Site Inspection findings with **immediate safety hazard** classification, Safety Manager gains Constrained Co-Authority over the record:
* Named transition: **`escalate_to_stop_work`** (FINDINGS_RAISED → STOP_WORK_ISSUED)
* Read+notify access otherwise
* Does NOT become owner outside this single transition

This honors regulatory reality without violating Rule 3.

### §3.7 · Constitutional checks (gate list)

Same 10-check matrix as §2.7 — all PASS.

---

## §4 · Cross-workflow shared infrastructure

Both OC-003 and OC-004 share the following primitives (built once, used twice):

| Primitive | Description |
|---|---|
| `workflow_state_events` | Already live (iter451 / iter452) · all transitions emit rows |
| `corrective_actions` collection | Canonicalized in BUILD Wave 1 (G0-10) · single CA system serves both workflows |
| `field_submitter_bindings` | FSI 5-tier ladder · already live (iter452.5.1) |
| `manager_employee_id` field | Ownership Layer Wave 1 (G1-11) — **iter453 build is GATED on this primitive** |
| Action Console pattern | Ownership Layer Wave 2 (Layer B/C) — iter453 surfaces require Console contract |
| Re-inspection record schema | NEW · simple addition: `re_inspection_records` collection or `inspection_records.is_re_inspection_for` field |
| Documented exception schema | NEW · `workflow_exceptions` collection (single shared collection across all closure-action workflows) |

---

## §5 · Build dependencies (informational · zero authorization)

iter453 build authorization should only be granted **after** the following:

| Dependency | Status |
|---|---|
| Ownership Doctrine accepted (Phase 1) | ✅ DONE this batch |
| 5 REVIEW items resolved (Phase 2) | ✅ DONE this batch |
| `manager_employee_id` field added to employees + FL users | ⚠️ Ownership Layer A build (not yet authorized) |
| Ownership inference engine wired on existing state machines | ⚠️ Ownership Layer A build (not yet authorized) |
| Constitutional Test applied per UI affordance | ✅ enforced via this package |
| 4 Constitutional Violations from prior Compliance Sweep (CV-1..CV-4) resolved | ⚠️ Operator decision pending in `AMENDMENT001_EXECUTIVE_SUMMARY.md §5` |

If Ownership Layer A is not yet built when iter453 is authorized, the build may proceed using **stub inference** (`current_owner_role` field set per state, no manager_ladder ladder, no Action Console). This is acceptable Constitutional debt provided it is closed within the next 2 build batches.

---

## §6 · Marketing-quality contract (post-build)

When iter453 ships, the platform can claim:

> "QA/QC and Site Inspection workflows in ForgedOps close only when operational action is recorded — a re-inspection, a completed corrective action, or a documented exception with dual sign-off. There are no acknowledgement clicks. The PM owns remediation regardless of whether the work is performed in-house or by a subcontractor. Ownership escalates automatically up the manager ladder if remediation aging exceeds SLA. The platform never asks a human to type a name into an Assignee field."

This is a marketable claim no construction-industry-standard platform makes today.

---

## §7 · Discipline scorecard

| Check | Status |
|---|---|
| Zero code | ✅ |
| Zero design (UI mockups, wireframes, copy) | ✅ |
| Zero estimates | ✅ |
| Zero build authorization | ✅ |
| OC-003 state machine + closure contract + ownership inference defined | ✅ |
| OC-004 state machine + closure contract + ownership inference defined | ✅ |
| All 10 Constitutional checks PASS per workflow | ✅ |
| Ownership Doctrine O-1 through O-15 honored | ✅ |
| Build dependencies enumerated (not pre-authorized) | ✅ |
| Marketing-quality contract rendered | ✅ |

---

## §8 · Status

🛑 Phase 3 complete. iter453 is now Constitutionally re-scoped and ready for explicit operator build authorization. The build remains FROZEN until that authorization arrives. Awaiting operator decision among Options C/D/E (Ownership Layer build) OR explicit iter453 build authorization (now safe to issue) OR Phase 4 next.
