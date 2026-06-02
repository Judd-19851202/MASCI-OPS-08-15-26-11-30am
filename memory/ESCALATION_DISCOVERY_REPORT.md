# OMEGA · ESCALATION DISCOVERY REPORT

**Date:** 2026-06-02 · Companion to `OWNERSHIP_LAYER_DISCOVERY_AUDIT.md`
**Mode:** READ-ONLY · zero code · zero design · zero estimates
**Purpose:** Discover how escalation occurs without notification fan-outs, manager-pings, or department-wide CCs. **Escalation is automatic ownership transfer up the `manager_employee_id` ladder at SLA breach.** The previous owner is informed once; the new owner becomes the accountable party.

---

## §0 · Foundational rule (Constitution Rule 7 + Rule 8 + Override)

> Escalation is not a notification — it is an ownership change. When age-in-state exceeds the workflow-class SLA, the platform automatically promotes ownership to the next level up the manager ladder. The previous owner is notified once (Rule 8 single-recipient discipline) for awareness, not for re-action. The new owner sees the record in their Action Console.

This is the inverse of every ticket-system escalation model. Tickets escalate by adding watchers and CCs. ForgedOps escalates by **changing who is accountable**. Only one person owns at any moment, regardless of escalation hop count.

---

## §1 · Class-level SLA defaults (informational)

| Workflow class | Active-state SLA (default) | Justification |
|---|---|---|
| Incidents · OPEN | 4h | Safety triage must be immediate |
| Incidents · UNDER_INVESTIGATION | 2 business days | Investigation typically 1-2d for non-OSHA |
| Incidents · CORRECTIVE_ACTION_REQUIRED | 5 business days | CAPA remediation window |
| Incidents · PENDING_CLOSURE | 3 business days | OSHA close-out paperwork window |
| Daily Reports · PENDING_REVIEW | 48 hours | Office-side review cadence |
| QA/QC · DEFICIENCY_RAISED | 3 business days | PM accept work scope |
| QA/QC · IN_REMEDIATION | 10 business days | Sub-coordination realistic window |
| QA/QC · PENDING_RE_INSPECTION | 5 business days | QC re-inspection cadence |
| Site Inspections | Symmetrical to QA/QC | — |
| Payroll Variances · UNDER_REVIEW | 24h before payroll cut | Cycle-driven |
| Payroll Variances · APPROVED | Up to payroll cut time | Cycle-driven |
| Toolbox Talk per crew | Daily (resets per crew per shift) | Operational reality |
| Training expirations | 30d / 14d / past-due | Industry standard |
| Equipment Pre-Op | Per-shift (resets) | Operational reality |
| Equipment defect (Open) | 7 business days | Shop turnaround |
| Equipment PM cycle | 30d / overdue | Manufacturer schedule |
| Asset Transfer (IN_TRANSIT) | 24h | Transfer logistics |
| Fleet DVIR | Per-shift (resets) | DOT requirement |
| Fleet defect (Open) | 7 business days | Shop turnaround |
| Fleet DQ-file | 30d / past-due | Regulatory |
| HR Time Off | 5 business days | Standard request window |
| HR Onboarding (field-side) | 14 calendar days from hire | Safety-readiness window |
| HR Offboarding (field-side) | 14 calendar days from termination | Asset/access return window |
| Performance Review | HRIS-owned · INTEGRATE consumer | — |
| Project Ops · Submittal | 21 business days | Industry standard |
| Project Ops · RFI | 14 business days | Industry standard |
| Project Ops · CO | 21 business days | Industry standard |
| Project Ops · Pay-App approval | 30 calendar days | Contract terms |
| Project Ops · Sub-Mgmt insurance | 30d / 14d / 7d / past-due | Risk management |
| Project Ops · Meeting-Minutes | n/a · record-of-fact | — |

SLAs are operator-configurable per tenant. Defaults shown are heavy-civil-GC industry norms.

---

## §2 · Escalation events × 10 workflows

For each workflow class, the table names:
* **Trigger** (the SLA breach that fires escalation)
* **Hop pattern** (who ownership transfers to)
* **Awareness notification** (single-recipient former-owner ping)

### §2.1 · Incidents

| Trigger | Hop | Awareness ping |
|---|---|---|
| OPEN > 4h | Safety Manager (already next-state owner) | Submitter |
| UI > 2 bd | Safety Manager's manager | Safety Manager |
| CAR > 5 bd | PM's manager (manager_employee_id) | PM |
| CAR > 10 bd | PM's manager's manager | PM's manager |
| PC > 3 bd | Safety Manager's manager | Safety Manager |

### §2.2 · Daily Reports

| Trigger | Hop | Awareness ping |
|---|---|---|
| PENDING_REVIEW > 48h | PM's manager | PM |
| PENDING_REVIEW > 5 bd | PM's manager's manager (Operations Manager) | PM's manager |

### §2.3 · QA/QC

| Trigger | Hop | Awareness ping |
|---|---|---|
| DEFICIENCY_RAISED > 3 bd | PM's manager | PM |
| IN_REMEDIATION > 10 bd | PM's manager | PM |
| IN_REMEDIATION > 20 bd | PM's manager's manager + Operations Manager | PM's manager |
| PENDING_RE_INSPECTION > 5 bd | Inspector's manager | Inspector |

### §2.4 · Site Inspections

Symmetrical to QA/QC.

### §2.5 · Payroll Variances

| Trigger | Hop | Awareness ping |
|---|---|---|
| UR > 24h before cut | PM's manager | PM |
| UR > 0h before cut | Operations Manager (cycle-breaker) | PM + PM's manager |
| APPROVED but unfinalized at cut | Payroll Lead | Payroll handler |

### §2.6 · Safety (Training)

| Trigger | Hop | Awareness ping |
|---|---|---|
| Training expiring < 14d | Direct manager (manager_employee_id) | Employee |
| Training expired | Manager's manager + Safety Manager | Direct manager |
| Training expired > 30d | Operations Manager + Safety Manager (continued employment exposure) | Manager's manager |

### §2.7 · Equipment

| Trigger | Hop | Awareness ping |
|---|---|---|
| Open defect > 7 bd | Shop Foreman's manager (Equipment Manager) | Shop Foreman |
| Open defect > 14 bd | Equipment Manager's manager (Operations Manager) | Equipment Manager |
| PM overdue > 30d | Equipment Manager's manager | Equipment Manager |
| Asset IN_TRANSIT > 24h | Equipment Manager + receiving PM | Sender |

### §2.8 · Fleet

| Trigger | Hop | Awareness ping |
|---|---|---|
| Open DVIR defect > 7 bd | Fleet Manager's manager | Fleet Manager |
| DQ-file expiring < 14d | Driver's direct manager + Fleet Manager | Driver |
| DQ-file expired | Manager's manager + Safety Manager (DOT exposure) | Direct manager |
| DQ-file expired > 7d | Operations Manager + Safety Manager (driver cannot legally drive) | Manager's manager |

### §2.9 · HR

| Trigger | Hop | Awareness ping |
|---|---|---|
| Time Off REQUESTED > 5 bd | Manager's manager | Direct manager |
| Onboarding open > 14d | Safety Manager + Operations Manager | Direct manager |
| Offboarding open > 14d | Equipment Manager + Safety Manager + Operations Manager | Direct manager |
| Performance review overdue (HRIS-side) | HRIS escalation owns (INTEGRATE consumer) | (HRIS-side) |

### §2.10 · Project Operations

| Trigger | Hop | Awareness ping |
|---|---|---|
| Submittal external > 21 bd | PM (re-engage counterparty) → PM's manager if > 30 bd | PM (initially); PM's manager (secondary) |
| RFI external > 14 bd | PM (re-engage) → PM's manager if > 21 bd | PM, then PM's manager |
| CO external > 21 bd | PM → PM's manager | Same pattern |
| Pay-App approval > 30 cd | PM + Accounting (EX-1 lens) → PM's manager if > 45 cd | PM, then PM's manager |
| Sub-Mgmt insurance < 14d | PM | (initially silent) |
| Sub-Mgmt insurance < 7d | PM + PM's manager | PM |
| Sub-Mgmt insurance expired | Operations Manager + Safety Manager (work-stoppage exposure) | PM's manager |

---

## §3 · The manager_employee_id ladder

Every escalation hop above presupposes the existence of `manager_employee_id` on employees and FL users (G1-11 BUILD primitive · Top 10 Rank #1 component). The escalation algorithm:

```
escalate(record, current_owner):
    next_owner = employees[current_owner].manager_employee_id
    if next_owner is NULL:
        next_owner = workflow_class_default_role
    if next_owner is NULL:
        next_owner = Operations Manager
    if next_owner is NULL:
        next_owner = Tenant Super-Admin (break-glass)
    if next_owner is NULL:
        next_owner = ADMIN_DEAD_LETTER_EMAIL  (Tier 5 dead-letter)
    transition_record_owner(record, current_owner → next_owner)
    awareness_notify(current_owner, "ownership of <record> escalated to <next_owner>")
```

This is the **same ladder** as the NULL-inference fallback ladder in `OWNERSHIP_INFERENCE_MATRIX.md §11`. Escalation and orphan-resolution share infrastructure.

---

## §4 · Notification discipline (Rule 8 textbook)

Every escalation hop sends **one** notification to **one** person (the previous owner). Never multi-recipient. Never department-wide. The new owner sees the record in their Action Console — no notification needed, because the new owner's console already filtered to "things you own".

| Forbidden pattern | Why |
|---|---|
| CC PM + Safety + Admin on every escalation | Rule 8 violation — single recipient discipline |
| Push notification to "Safety Department" group | Group ownership violates Rule 3 (One Owner) |
| SMS blast to all crew supervisors | Rule 8 violation |
| "Escalation Hub" surface with all-org escalation list | Anti-checklist clause violation |
| Email digest of "all open escalations" to executives | Replace with Action Console executive rollup (§7 below) |

| Permitted pattern | Why |
|---|---|
| Single email to previous owner ("ownership transferred to <name>") | Awareness only · no action required by previous owner |
| Single email/in-app surface to new owner ("you now own <record>") | Optional — new owner already sees it in Action Console |
| iter452.5.2 Resend Bounce Webhook on delivery failure | Re-routes to backup owner via Rule 7 auto-escalate · already pre-authorized |

---

## §5 · Auto-escalation cadence

Escalation cron sweeps records at workflow-class-appropriate cadences (recommended; operator-tunable):

| Workflow class | Sweep frequency |
|---|---|
| Incidents · Payroll Variances · Time Off | Hourly |
| Daily Reports · QA/QC · Site Inspections · Equipment defects · Fleet defects | Every 4 hours |
| Sub-Mgmt insurance · Training expirations · DQ-file · PM cycles | Daily 06:00 local |
| Long-window PM workflows (Submittal/RFI/CO/Pay-App) | Daily 06:00 local |

All sweeps share a single idempotent escalation engine — never multiple notification systems competing. Sweep records `workflow_state_events` rows with `evidence.escalation_hop` for Phase 1B auditability.

---

## §6 · What escalation NEVER includes

| Forbidden | Why |
|---|---|
| User-initiated "Escalate this" button | Rule 7 violation — escalation is automatic; user-initiated escalation invites favoritism + abuse |
| "Snooze escalation" affordance | Rule 1 + Rule 4 — workflows must end via operational action, not delay |
| Custom escalation chain per record | Rule 6 violation — escalation rules are workflow-class properties, not per-record fields |
| Multiple parallel escalations | Rule 3 violation — One Owner per moment |
| Escalation that doesn't transfer ownership | Defeats the model — notification-only escalations become noise |

---

## §7 · Executive escalation rollup (Action Console pattern)

Executives see escalation activity as **Action Console rows**, not dashboards:

| Console row | One-tap action affordances |
|---|---|
| "Records escalated to me this week" (per executive) | Open record · escalate again (skip-hop) · close (with reason) |
| "Records that hit max-hop ladder this week" (Operations Manager view) | Open · reassign by transition · request operations review |
| "PMs with > N records in escalation" (Executive portfolio) | Open PM scorecard · call PM (telephony hook) · request 1:1 |
| "Workflows with chronically-breached SLAs by class" (Operations Manager) | Open class SLA settings (operator-tunable) · request workflow review |

Each row has a one-tap action. No row is read-only. Override anti-checklist clause enforced.

---

## §8 · Discipline scorecard

| Check | Status |
|---|---|
| Zero code | ✅ |
| Zero design | ✅ |
| Class-level SLAs informational only | ✅ |
| Per-workflow escalation events documented | ✅ |
| manager_employee_id ladder algorithm rendered | ✅ |
| Rule 8 single-recipient discipline enforced throughout | ✅ |
| Forbidden patterns enumerated | ✅ |
| Action Console pattern preserved for executive surfaces | ✅ |
| No user-initiated escalation affordance | ✅ |
| No multi-recipient broadcast pattern | ✅ |

🛑 **STOPPED.**
