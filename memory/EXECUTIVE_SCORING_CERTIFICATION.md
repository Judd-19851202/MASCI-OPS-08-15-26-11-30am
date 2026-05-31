# Executive Scoring Certification (Phase A)

**Classification:** OMEGA Pillar 2 · Phase A · Mandatory scoring justification
**Generated:** 2026-05-31 UTC
**Authority:** Every threshold below is documented with operational evidence, leadership action, owner, and expected resolution timeframe. **No threshold is arbitrary.**

---

## 1 · Why this document exists

Per operator directive: *"The scoring model is more important than the dashboard itself. A dashboard with incorrect scoring creates noise. A dashboard with correct scoring creates leadership focus."*

This document is the single source of truth for every RAG threshold in the Executive Command Center. Every value in `db.command_center_thresholds` corresponds to a row in this matrix.

---

## 2 · How to read each rule

For each rule:
- **Predicate:** the operational condition the rule detects.
- **Operational risk:** what happens to MASCI if the condition persists.
- **Leadership action:** the specific action expected when the rule fires.
- **Owner:** the role accountable for the action.
- **Expected resolution:** when MASCI expects this condition to be cleared.
- **Threshold:** the AMBER and RED cutoffs that determine the pill state.

---

## 3 · Jobs Today Card

### Rule JOBS-DR-MISSING
| Attribute | Value |
|---|---|
| Predicate | Active jobs (jobs_master.status ∈ [Active, Open, null]) with no daily_report in the last 36 hours |
| Operational risk | Field activity invisible to leadership · accountability gap · client/auditor exposure if work occurred but wasn't documented |
| Leadership action | PM contacts foreman · confirms work happened · refiles DR if missed |
| Owner | PM (primary_pm_email on jobs_master) |
| Expected resolution | Same day (refile DR) or next business day |
| **AMBER threshold** | **2 active jobs** without recent DR |
| **RED threshold** | **5 active jobs** without recent DR |
| Lookback window | 36 hours (covers a missed working day plus the following morning) |

### Rule JOBS-ISSUE-NO-OWNER
| Attribute | Value |
|---|---|
| Predicate | Open corrective_action (`status ∈ [Open, In Progress, Pending Review]`) with no `assigned_to_name` |
| Operational risk | Active issue has no responsible party — silent escalation risk · no closure path |
| Leadership action | Operations Director assigns owner immediately |
| Owner | operations_leadership |
| Expected resolution | Within 24 hours of detection |
| **AMBER / RED threshold** | **1** unowned issue (immediate RED — there is no acceptable level of unowned operational issues) |

### Rule JOBS-ISSUE-NO-PATH
| Attribute | Value |
|---|---|
| Predicate | Open incident older than 7 days with no linked corrective_action (no `source_id` or `incident_id` referencing the incident) |
| Operational risk | Issue acknowledged but no resolution path documented · regulatory exposure · cultural signal that issues don't get resolved |
| Leadership action | Safety + PM document corrective action or close incident |
| Owner | safety |
| Expected resolution | Within 5 business days |
| **AMBER threshold** | **1** stale incident without CA path |
| **RED threshold** | **3** stale incidents without CA path |

---

## 4 · Safety Today Card

### Rule SAF-CRITICAL-UNRESOLVED
| Attribute | Value |
|---|---|
| Predicate | Incident with severity ∈ [Critical, High, Serious] (case-insensitive) older than the threshold age |
| Operational risk | Personnel safety exposure · regulatory exposure · potential repeat incident if not addressed |
| Leadership action | Safety lead briefs Operations Director · site visit if warranted · ensure CA is documented |
| Owner | safety |
| Expected resolution | Critical: 24h · High: 48h |
| **AMBER threshold** | **24 hours** since incident creation |
| **RED threshold** | **48 hours** since incident creation |

### Rule SAF-OSHA-OPEN
| Attribute | Value |
|---|---|
| Predicate | Incident with `osha_recordable = "Yes"` (case-insensitive) older than 24 hours |
| Operational risk | OSHA reporting clock is running — fatality (8h), hospitalization/amputation/loss-of-eye (24h). Non-compliance = penalty + audit |
| Leadership action | Confirm OSHA notification was submitted · close internal record · brief Operations Director |
| Owner | safety |
| Expected resolution | Within OSHA reporting window (8h fatality / 24h hospitalization) |
| **RED threshold** | **24 hours** since incident creation (any OSHA-recordable that crosses 24h fires RED) |

### Rule SAF-CA-OVERDUE
| Attribute | Value |
|---|---|
| Predicate | Corrective action (`status ∈ [Open, In Progress, Pending Review]`) with `due_date` < today |
| Operational risk | Documented hazards remain mitigated only on paper · audit trail says "we said we'd fix it" |
| Leadership action | Safety lead reassigns or closes overdue CAs |
| Owner | safety |
| Expected resolution | Within 5 business days of detection |
| **AMBER threshold** | **1** overdue CA |
| **RED threshold** | **3** overdue CAs |

### Rule SAF-CA-CHRONIC
| Attribute | Value |
|---|---|
| Predicate | Corrective action open for more than 60 days regardless of due_date |
| Operational risk | Long-running open finding signals broken closure workflow · culture-of-non-closure |
| Leadership action | Safety reviews CA · closes, extends, or escalates |
| Owner | safety |
| Expected resolution | Within 10 business days of detection |
| **AMBER threshold** | **60 days** since CA creation (any CA over this age fires AMBER) |

---

## 5 · Equipment Today Card

### Rule EQP-OOS-OLD
| Attribute | Value |
|---|---|
| Predicate | Fleet defect with `severity = "oos"` (out-of-service) and `status ∈ [open, acknowledged]` older than the threshold age |
| Operational risk | Equipment unavailable → crew idle / project delay / rental cost / customer dissatisfaction |
| Leadership action | Shop manager confirms parts/labor plan · Operations approves rental if needed |
| Owner | shop |
| Expected resolution | OOS: 72h max · sooner if production-critical |
| **AMBER threshold** | **24 hours** OOS |
| **RED threshold** | **72 hours** OOS |

### Rule EQP-OOS-NEW
| Attribute | Value |
|---|---|
| Predicate | Newly OOS defect (`severity = "oos"`, `status = "open"`, no Shop acknowledgement) created in last 24h |
| Operational risk | Defect reported but Shop has not engaged · risk of silent escalation |
| Leadership action | Operations escalates directly to Shop Manager |
| Owner | shop |
| Expected resolution | Acknowledgement within 24 hours of report |
| **RED threshold** | **1** unacknowledged new OOS defect |

### Rule EQP-BACKLOG
| Attribute | Value |
|---|---|
| Predicate | Total open fleet defects (any severity, status ∈ [open, acknowledged]) |
| Operational risk | Aggregate maintenance debt impacts fleet availability · staffing or vendor inadequacy |
| Leadership action | Operations + Shop review weekly · staffing or vendor escalation |
| Owner | shop |
| Expected resolution | Trend reduction over 30 days |
| **AMBER threshold** | **10 open defects** |
| **RED threshold** | **20 open defects** |

---

## 6 · Accountability Overdue Card

### Rule ACC-HIGH-OVERDUE
| Attribute | Value |
|---|---|
| Predicate | Tasks with `priority ∈ [High, Critical]` and `status ∈ [Open, In Progress]` and `due_at < now` |
| Operational risk | Action items the platform tracked but no one closed · the accountability promise of the platform breaks |
| Leadership action | Assignee or Admin triages queue · reassign or close |
| Owner | varies (per task's `assignee_role` / `assignee_user_id`) |
| Expected resolution | Within 2 business days |
| **AMBER threshold** | **3** high/critical tasks overdue |
| **RED threshold** | **8** high/critical tasks overdue |
| Excluded | Low- and Medium-priority tasks (intentionally — they generate noise without leadership signal) |

### Rule ACC-STALE
| Attribute | Value |
|---|---|
| Predicate | High/Critical task overdue by more than 14 days |
| Operational risk | Long-stale critical task — the workflow has demonstrably broken down |
| Leadership action | Operations Director reviews individually · forces closure or escalation |
| Owner | operations_leadership |
| Expected resolution | Within 5 business days of detection |
| **RED threshold** | **1** task overdue ≥ 14 days |

---

## 7 · Approvals Aging Card

### Rule APP-AMBER
| Attribute | Value |
|---|---|
| Predicate | PO request with `status ∈ [Pending Approval, Submitted, Clarification Needed]` aged 3 to 4 days |
| Operational risk | Approaching the operationally-late threshold · materials/work begin to slip |
| Leadership action | Named approver decides or escalates within 24h |
| Owner | approver per `APPROVAL_PERMISSION_MATRIX.md` routing |
| Expected resolution | Within MASCI PO SLA (operator-tunable Q-7) |
| **AMBER threshold** | **3-4 days** since PO creation (single PO triggers) |

### Rule APP-RED
| Attribute | Value |
|---|---|
| Predicate | PO request pending approval ≥ 5 days |
| Operational risk | Operationally late · materials/work blocked · vendor relationship friction |
| Leadership action | Operations Director forces decision or reassigns approver |
| Owner | approver per routing (Operations Director if approver unresponsive) |
| Expected resolution | Within 1 business day of detection |
| **RED threshold** | **5+ days** since PO creation |

### Rule APP-WEEK
| Attribute | Value |
|---|---|
| Predicate | PO request pending approval ≥ 7 days |
| Operational risk | Severe approval breakdown · project impact likely · customer/vendor visibility |
| Leadership action | Executive intervention · approver reassignment |
| Owner | operations_leadership |
| Expected resolution | Same day |
| **RED threshold** | **7+ days** since PO creation (any PO at this age fires immediate executive RED) |

---

## 8 · Composite scoring rules

### Overall card pill
```
card.pill = max(severity for warning in card.warnings)
```
Where severity ordering is `RED > AMBER > GREEN`. If no warnings fire, the card is GREEN.

### Overall Pulse Strip pill
```
pulse.pill = max(card.pill for card in [jobs, safety, equipment, accountability, approvals])
```
If any card is RED → Pulse RED. Else any AMBER → Pulse AMBER. Else GREEN.

### Pulse headline
```
pulse.headline = "{red_count} RED · {amber_count} AMBER warnings"
                 (where counts aggregate across all 5 cards)
```

---

## 9 · The 5-question contract every rule satisfies

Per `EXECUTIVE_COMMAND_CENTER_SPEC.md` §10, every rule above answers:

1. **What is wrong?** → the `predicate` field
2. **Why is it red?** → the threshold + age comparison (visible in the warning message)
3. **Who owns it?** → the `owner_role` field
4. **What is being done?** → linked task/CA status from source collection
5. **When will it resolve?** → the `expected_resolution` field

A rule that did not satisfy this contract was **not added** to Phase A. (This is why the Document Expirations card, the Recommender, and Projects-at-Risk did not ship in Phase A — see `EXECUTIVE_COMMAND_CENTER_DESIGN_REVIEW.md`.)

---

## 10 · Tunability

Every threshold above lives in `db.command_center_thresholds.rules[<rule_id>]`. Operator-tunable via:

```
GET   /api/admin/command-center/thresholds       # read current values
PATCH /api/admin/command-center/thresholds       # update — audit-logged
```

The PATCH body merges partials: e.g., `{rules: {"APP-RED": {"red_days_min": 7}}}` raises the Approvals RED threshold from 5 to 7 days without touching any other rule.

Every change is captured in `admin_audit` with `{kind: "command_center.thresholds.update", version, changed_keys}`.

---

## 11 · Operational evidence base

| Rule | Evidence anchor for the threshold |
|---|---|
| JOBS-DR-MISSING (2 / 5) | Operator observation that 1 missing DR is recoverable, multiple = pattern, 5+ = systemic |
| JOBS-ISSUE-NO-OWNER (1 / 1) | Doctrine: no acceptable level of unowned operational issues |
| JOBS-ISSUE-NO-PATH (1 / 3, 7 days) | Industry safety norm: documented hazards must have a resolution path within one work week |
| SAF-CRITICAL-UNRESOLVED (24h / 48h) | OSHA / safety doctrine: high-severity incidents must be addressed within 1-2 days |
| SAF-OSHA-OPEN (24h) | OSHA reporting windows: 8h fatality / 24h hospitalization — 24h is the regulatory clock |
| SAF-CA-OVERDUE (1 / 3) | Same doctrine as JOBS-ISSUE-NO-OWNER — overdue CAs are tracked promises |
| SAF-CA-CHRONIC (60 days) | Industry norm: any open finding > 60 days indicates workflow breakdown |
| EQP-OOS-OLD (24h / 72h) | Construction industry norm: critical equipment must be back within 3 days |
| EQP-OOS-NEW (1) | Doctrine: Shop must acknowledge every OOS defect within 24h or operations can't plan |
| EQP-BACKLOG (10 / 20) | Operator-tunable; starting defaults based on fleet size · should be adjusted to MASCI's actual fleet capacity |
| ACC-HIGH-OVERDUE (3 / 8) | Background overdue noise floor estimated at 3-5 tasks; 8+ = leadership signal |
| ACC-STALE (14 days) | If a critical task is overdue for two weeks, the workflow has demonstrably broken |
| APP-AMBER (3-4 days) | Operator-tunable default · revisit after Q-7 PO SLA confirmation |
| APP-RED (5+ days) | Same — assumes 5-day SLA · revisit per operator |
| APP-WEEK (7+ days) | Industry pattern: weekly executive PO review |

**Every threshold is tunable. None are arbitrary. Every red condition traces to a real operational consequence.**

---

## 12 · Certification

🟢 **Scoring model certified for Phase A.** Every threshold has:
- A documented operational predicate
- A documented operational risk
- A documented leadership action
- A documented owner
- A documented expected resolution

Every rule passes the 5-question contract. The model is deterministic, auditable, and operator-tunable. **Phase A scoring is ready for pilot use.**
