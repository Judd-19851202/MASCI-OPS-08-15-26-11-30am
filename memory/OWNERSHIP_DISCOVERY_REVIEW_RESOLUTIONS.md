# OMEGA · PHASE 2 — OWNERSHIP DISCOVERY REVIEW RESOLUTIONS

**Date:** 2026-06-02 · Doctrine resolution package
**Mode:** READ-ONLY · zero code · zero design · zero implementation
**Operator authorization:** "Perform doctrine-only resolution of: Counterparty pseudo-state · DOT joint ownership · Operations Manager overload · Visibility versus ownership distinction · Chart drift risk. Achieve 100 % constitutional clarity before Ownership Layer build authorization."

---

## §0 · Resolution framework

Each REVIEW REQUIRED item is resolved with:
* **Tension** — the Constitutional ambiguity surfaced in `CONSTITUTIONAL_COMPLIANCE_REVIEW.md`
* **Resolution** — the binding doctrine that resolves the ambiguity
* **Forward rule** — the rule that becomes part of the Ownership Doctrine
* **Verification** — how to know the rule is being honored at scoping time

No solutions are designed. No UI is specified. No implementation is planned. Doctrine only.

---

## §1 · REVIEW-1 — Counterparty "external owner" pseudo-state in PM workflows

### Tension
Rule 3 (One Owner) requires exactly one accountable internal person at every moment. PM workflows (Submittal · RFI · CO · Pay-App) include states where the record sits with an external counterparty (Engineer of Record · Designer · Owner Rep · Architect). Naming an external party as the owner would violate Rule 3 because ForgedOps cannot enforce accountability on parties outside the tenant.

### Resolution
**PM is the sole internal owner at every state, including counterparty-pending states.** The counterparty is captured as **record metadata** (not as owner). The state name describes the *operational situation* ("Submittal under external review"), not an ownership transfer.

### Forward rule (added to Ownership Doctrine)
> **O-10 · Internal-Owner Invariant.** Every workflow record has exactly one internal accountable owner at every moment. Counterparties (subs, owners, engineers, designers, vendors, regulators) are stored as record metadata (`counterparty_role`, `counterparty_contact_email`, `counterparty_due_at`), never as owners. When a record's situation is "awaiting counterparty response," the internal owner (typically the PM) remains accountable for chasing the counterparty. The state machine names the situation; the owner does not change.

### Verification at scoping
| Check | Pass criterion |
|---|---|
| Per-state owner inference returns an internal employee/user | ✅ never a counterparty record |
| Counterparty information stored as metadata fields | ✅ not as `assignee_id` |
| Escalation ladder activates when counterparty SLA breached | ✅ PM's manager via `manager_employee_id`, not the counterparty's manager |

---

## §2 · REVIEW-2 — DOT joint ownership exception

### Tension
When a Fleet driver's DQ-file expires more than 7 days, the escalation hop names both **Operations Manager** (workflow-class default for chronic Fleet+HR exposure) and **Safety Manager** (DOT regulatory exposure). Two named recipients on one record creates Rule 3 ambiguity.

### Resolution
**Operations Manager is the sole accountable owner; Safety Manager is a Rule-8-compliant single-recipient awareness participant with a constrained authority.** Safety Manager may invoke a constrained one-tap action — **`pull_driver_from_service`** — that is a state transition (DQ_EXPIRED → DQ_DRIVER_GROUNDED). Outside that one transition, Safety Manager has read+notify only.

This preserves One Owner (Ops Mgr) while honoring the regulatory reality (Safety Mgr's authority to remove driver from service is non-delegable).

### Forward rule (added to Ownership Doctrine)
> **O-11 · Constrained Co-Authority.** When regulatory exposure requires a non-owner role to invoke a single state transition (typically a removal-from-service or stop-work action), that role is documented as a **Constrained Co-Authority** with:
> 1. Exactly one named state transition they may invoke
> 2. Read+notify access to the record
> 3. No general ownership of the record
>
> Constrained Co-Authority is not joint ownership; it is a single-transition delegation that preserves One Owner everywhere else.

### Verification at scoping
| Check | Pass criterion |
|---|---|
| Constrained Co-Authority documented per workflow class | ✅ in workflow-class config |
| Owner remains singular at every state | ✅ Rule 3 honored |
| Co-Authority's only affordance is the named state transition | ✅ no "edit", "reassign", "close" affordances |
| Co-Authority transition writes Tier 1 evidence | ✅ Amendment 001 honored |

### Other workflows where Constrained Co-Authority applies (informational)
| Workflow | Owner | Co-Authority | Named transition |
|---|---|---|---|
| Fleet · DQ_EXPIRED | Ops Mgr | Safety Mgr | `pull_driver_from_service` |
| Equipment · IN_SERVICE | Shop Foreman | Safety Mgr | `red_tag_for_safety` |
| Incident · UNDER_INVESTIGATION | Safety Mgr | Operations Manager | `escalate_to_executive` |
| Project Ops · ANY | PM | Operations Manager | `pause_project_for_review` |

---

## §3 · REVIEW-3 — Operations Manager console overload risk

### Tension
If many workflow classes default to Operations Manager as the workflow-class fallback role, and the manager-ladder escalation also frequently hops to Operations Manager, the role can experience console overload at tenant scale. Rule 6 (Minimize Human Decisions) is at risk if Operations Manager must manually triage hundreds of records.

### Resolution
**Operator-tunable per-tenant role-mapping for workflow-class defaults**, plus a **deputy delegation primitive** that uses state transitions rather than assignment UI.

### Forward rules (added to Ownership Doctrine)
> **O-12 · Tunable Role Mapping.** Workflow-class default roles are tenant-configurable in workflow-class config (one-time setup, not per-record). MASCI may map the "Fleet workflow-class default" to "Fleet Manager" rather than the platform fallback "Operations Manager." Tunable role-mapping is **not** per-record assignment — it is class-level configuration.

> **O-13 · Deputy Delegation via State Transition.** When an owner is unavailable (PTO · long-term absence), they may invoke a **`delegate_to_deputy(deputy_user_id, until)`** state transition on their entire console for a bounded period. The deputy becomes the new state-machine-resolved owner for the duration. At expiration, ownership reverts automatically. Delegation is **not** a per-record action; it is a console-wide state transition with start + end timestamps captured as Tier 1 evidence.

### Verification at scoping
| Check | Pass criterion |
|---|---|
| Workflow-class config per tenant available | ✅ no per-record assignment dropdown |
| Deputy delegation is a single bounded transition | ✅ not a perpetual reassignment |
| Reversion automatic at deputy expiration | ✅ Rule 7 honored |
| Tier 1 evidence written for delegation start + end | ✅ Amendment 001 honored |

---

## §4 · REVIEW-4 — Executive visibility vs ownership distinction

### Tension
The Action Console pattern blends "see this" and "own this." An executive who taps an action affordance becomes the new owner (escalate-to-self). But executives often want to **see** without **owning** — view a record for situational awareness without becoming accountable.

### Resolution
**Dual-affordance pattern per Action Console row:** **`open_record`** (read · no ownership transfer · no audit footprint beyond "viewed by") and **`take_ownership`** (escalate-to-self · new owner · audit-logged).

### Forward rule (added to Ownership Doctrine)
> **O-14 · Dual-Affordance per Action Console Row.** Every Action Console row exposes two affordances:
> 1. **`open_record`** — read access · no ownership transfer · "viewed by" audit only (per-user, per-record, per-day deduplicated)
> 2. **`take_ownership`** — explicit ownership transfer to the viewer · Tier 1 evidence captured ("X escalated <record> to self")
>
> The row's primary action affordance (e.g., "Escalate · Approve · Reassign by transition") sits alongside both. No row is read-only by accident; no row transfers ownership by accident.

### Verification at scoping
| Check | Pass criterion |
|---|---|
| Dual affordances present on every Action Console row | ✅ |
| `open_record` is informational, not transfer | ✅ Rule 2 honored |
| `take_ownership` writes Tier 1 evidence | ✅ Amendment 001 honored |
| No accidental ownership change from "drilling into" a record | ✅ Rule 3 honored |

---

## §5 · REVIEW-5 — Chart drift risk (row-metadata → standalone dashboards)

### Tension
Charts and sparklines are permitted as Action Console row metadata. Over time, designers/customers may push for "just this one chart" as a standalone tile, gradually evolving toward Dashboard pattern — violating the Override anti-checklist clause.

### Resolution
**Constitutional Test as mandatory pre-build gate for every new chart, sparkline, or visualization element.** Plus a hard **No-Standalone-Chart rule**: every chart must live inside an Action Console row whose row-level action transfers ownership or transitions state.

### Forward rule (added to Ownership Doctrine)
> **O-15 · No-Standalone-Chart Rule.** Every chart, sparkline, KPI, or visualization element must live inside an Action Console row whose row-level action affordance changes a record's state, transfers ownership, or invokes Constrained Co-Authority. Standalone charts are forbidden. The chart's purpose is to inform the action — not to inform contemplation. If the operator cannot answer "what action does this chart drive?", the chart fails the test and must not be built.

### Verification at scoping
| Check | Pass criterion |
|---|---|
| Every proposed chart is in an Action Console row | ✅ never standalone tile |
| The row has at least one action affordance | ✅ Override anti-checklist clause honored |
| The chart's purpose is documented as "what action this drives" | ✅ Rule 9 honored |
| Constitutional Test passes for the chart | ✅ Amendment 001 reference applied |

---

## §6 · Aggregate doctrine additions (O-10 through O-15)

The 5 resolutions add the following **6 forward-binding rules** to the Ownership Doctrine:

| Rule | Resolution |
|---|---|
| **O-10 · Internal-Owner Invariant** | Counterparty pseudo-state resolved · internal PM remains sole owner; counterparty captured as metadata |
| **O-11 · Constrained Co-Authority** | DOT joint-ownership resolved · single state-transition delegation pattern (no joint ownership) |
| **O-12 · Tunable Role Mapping** | Ops Mgr overload resolved (part 1) · workflow-class defaults tenant-configurable at class level |
| **O-13 · Deputy Delegation via State Transition** | Ops Mgr overload resolved (part 2) · bounded delegation as state transition · automatic reversion |
| **O-14 · Dual-Affordance per Action Console Row** | Visibility-vs-ownership distinction resolved · `open_record` + `take_ownership` always available |
| **O-15 · No-Standalone-Chart Rule** | Chart drift risk resolved · every chart inside Action Console row with action affordance |

Combined with the original 9 ownership rules (O-1 through O-9) from `OWNERSHIP_DISCOVERY_CANONICAL_ACCEPTANCE.md`, the Ownership Doctrine now has **15 binding rules**.

---

## §7 · 100 % Constitutional clarity achieved

After Phase 2 resolution:

| Document | Pre-resolution | Post-resolution |
|---|---|---|
| `OWNERSHIP_LAYER_DISCOVERY_AUDIT` | 9 PASS · 0 REVIEW · 0 CONFLICT | 9 PASS · 0 REVIEW · 0 CONFLICT |
| `OWNERSHIP_INFERENCE_MATRIX` | 8 PASS · 0 REVIEW · 0 CONFLICT | 8 PASS · 0 REVIEW · 0 CONFLICT |
| `OWNERSHIP_TRANSFER_MATRIX` | 8 PASS · 1 REVIEW · 0 CONFLICT | **9 PASS** · 0 REVIEW · 0 CONFLICT |
| `ESCALATION_DISCOVERY_REPORT` | 10 PASS · 2 REVIEW · 0 CONFLICT | **12 PASS** · 0 REVIEW · 0 CONFLICT |
| `EXECUTIVE_VISIBILITY_REQUIREMENTS` | 11 PASS · 2 REVIEW · 0 CONFLICT | **13 PASS** · 0 REVIEW · 0 CONFLICT |
| **TOTAL** | 46 PASS · 5 REVIEW · 0 CONFLICT | **51 PASS · 0 REVIEW · 0 CONFLICT** |

🟢 **100 % Constitutional clarity achieved.** The Ownership Doctrine is now ready for Ownership Layer build authorization without further documentation gates.

---

## §8 · Status

🛑 Phase 2 complete. Zero code · zero design · zero estimates · zero authorization. Ownership Doctrine = 15 binding rules. Awaiting operator decision on Ownership Layer A / B / C build authorization (Options C / D / E from `OWNERSHIP_LAYER_DISCOVERY_EXECUTIVE_SUMMARY.md §13`) OR Phase 3 (iter453 build package) OR Phase 4 (Operating System Audit).
