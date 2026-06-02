# OMEGA · EXECUTIVE VISIBILITY REQUIREMENTS

**Date:** 2026-06-02 · Companion to `OWNERSHIP_LAYER_DISCOVERY_AUDIT.md`
**Mode:** READ-ONLY · zero code · zero design · zero estimates
**Purpose:** Define what executive visibility ForgedOps must provide for each workflow class — strictly as **Action Consoles** (rows with one-tap action affordances), never as read-only dashboards. **Executive visibility is not reporting · it is operational re-engagement.**

---

## §0 · Foundational rule (Override anti-checklist clause + Rule 9)

> The platform must remain an operator's execution system, never an auditor's checklist system. Executive surfaces are no exception. Every executive view in ForgedOps must let the executive **do something** with what they see — not just look at it. Read-only KPI tiles are forbidden; Action Console rows are the only permitted pattern.

This is the inverse of every "executive dashboard" pattern in enterprise software. Dashboards optimize for "how does the business look?" Action Consoles optimize for "what should the executive **do** about it?"

---

## §1 · The Executive Action Console contract

Every executive surface in ForgedOps must satisfy:

| Contract | Requirement |
|---|---|
| **One-tap affordance per row** | Every row has at least one action button that performs an operational state transition |
| **Action triggers ownership transfer** | The affordance, when tapped, transfers ownership to the executive (or to a delegate via skip-hop) — making the executive the new accountable party |
| **No standalone "View" affordances** | Drilling into a record is a side-effect of choosing the action, not an independent goal |
| **No KPI tiles with no action** | KPIs may appear as row metadata, but no tile is presented purely as a number |
| **Single accountable owner per row** | Rule 3 — no group-owned rows |
| **Tier 1 evidence trace per row** | Tier 1 events that put the record on the console are accessible via the action context |

---

## §2 · Executive visibility per workflow class

### §2.1 · Incidents (OC-001)

| Console row | One-tap action | Owner of the action |
|---|---|---|
| "CAR > 5 bd by PM" | Open · request-update · escalate-skip-hop | Executive (becomes new owner if skip-hop) |
| "OSHA-recordable incidents this quarter" | Open · request OSHA review meeting (calendar hook) | Executive |
| "Incidents reopened in last 30d" | Open · request root-cause review | Executive |
| "Safety Manager backlog (UI > 2 bd)" | Open · request Safety 1:1 (calendar hook) | Executive |

### §2.2 · Daily Reports (OC-002)

| Console row | One-tap action |
|---|---|
| "DRs in PENDING_REVIEW > 48h by PM" | Open · escalate-skip-hop · request PM 1:1 |
| "PMs with > 3 stale PENDING_REVIEW DRs" | Open PM scorecard · escalate-skip-hop |
| "Projects with no DR in last 5 bd" | Open project Action Console · request superintendent review |

### §2.3 · QA/QC (OC-003)

| Console row | One-tap action |
|---|---|
| "Open deficiencies > SLA by PM" | Open · escalate-skip-hop · open project quality scorecard |
| "Sub-driven remediation > 10 bd" | Open · request sub-coordination review |
| "Inspectors with > N PENDING_RE_INSPECTION backlog" | Open · escalate-skip-hop |

### §2.4 · Site Inspections (OC-004)

Symmetrical to QA/QC.

### §2.5 · Payroll Variances (OC-007)

| Console row | One-tap action |
|---|---|
| "Variances UR > 24h pre-cut by PM" | Open · escalate-skip-hop · request PM 1:1 |
| "Trend: Variance volume > 30d rolling avg by project" | Open project variance Action Console · request supervisor review |
| "Unfinalized after cut by Payroll handler" | Open · escalate-skip-hop |

### §2.6 · Safety (Training · JHP · Toolbox Talk)

| Console row | One-tap action |
|---|---|
| "Training expirations next 30d by manager" | Open · request manager 1:1 · request mass-training scheduling |
| "Crews missing Toolbox Talk this week by foreman" | Open · request foreman review |
| "JHP downloads with unresolved identity (Tier 5 dead-letter)" | Open · request safety review |

### §2.7 · Equipment

| Console row | One-tap action |
|---|---|
| "Open defects > 7 bd by Shop Foreman" | Open · escalate-skip-hop |
| "PM cycles overdue by Equipment Manager" | Open · request maintenance scheduling review |
| "Asset utilization low this month by job" | Open · request PM redeployment review |
| "Asset Transfer IN_TRANSIT > 24h" | Open · escalate-skip-hop |

### §2.8 · Fleet

| Console row | One-tap action |
|---|---|
| "Open Fleet defects > 7 bd by driver" | Open · escalate-skip-hop |
| "DQ-file expirations next 30d by driver" | Open · request mass-renewal scheduling |
| "DQ-file expired drivers (DOT exposure)" | Open · request Fleet + Safety review · pull-driver-from-service (skip-hop with reason) |
| "CSA scores trending negative this quarter" | Open ELD integration view · request Fleet review |

### §2.9 · HR

| Console row | One-tap action |
|---|---|
| "Onboarding incomplete > 14d by manager" | Open · escalate-skip-hop |
| "Offboarding incomplete > 14d by manager" | Open · escalate-skip-hop · ensure asset/access return |
| "Time Off > 5 bd unapproved by manager" | Open · escalate-skip-hop |
| "Headcount changes this quarter (HRIS integration)" | Open HRIS-side data · no action (read-only acceptable for HRIS consumed data per Rule 9) |

### §2.10 · Project Operations

| Console row | One-tap action |
|---|---|
| "RFIs > 14 bd unanswered by project" | Open · escalate-skip-hop · request PM 1:1 |
| "Submittals > 21 bd by project" | Open · escalate-skip-hop |
| "Change Orders unapproved > 21 bd by counterparty" | Open · request PM 1:1 · request counterparty escalation |
| "Pay-Apps awaiting payment > 30 cd (EX-1 lens)" | Open · request Accounting 1:1 · request Owner Rep escalation |
| "Subs with insurance expired" | Open · pull-from-active-work · request Risk Management |
| "Backlog vs in-progress by project" (CRM-integrated · EX-13 INTEGRATE) | Open backlog · no action (CRM-owned consumed read-only acceptable per Rule 9) |

---

## §3 · Portfolio rollup (cross-workflow executive view)

The top-level executive Action Console rolls up activity across all 10 workflow classes:

| Portfolio row | What it shows | One-tap action |
|---|---|---|
| **PM Scorecard** (per PM, one row each) | Open records owned across all workflows + SLA breach rate + escalation count last 30d | Open per-PM Action Console (filtered to that PM) · request PM 1:1 (calendar hook) |
| **Project Risk Lens** (per project) | Open records by class · SLA breach % · CAR open · sub insurance status | Open project Action Console · request project review meeting |
| **Operations Manager Workload** | Records escalated to Operations Manager last 30d · max-hop records · workflow-class-default fallbacks invoked | Open Operations review · request Operations 1:1 |
| **Safety Manager Workload** | Open incidents · CAR backlog · training compliance · DOT exposure | Open Safety Action Console · request Safety 1:1 |
| **Executive Direct Queue** (records escalated directly to executive) | Records currently owned by executive via escalation skip-hop | Open · close (with reason) · re-delegate (skip-hop) |

---

## §4 · The 8 mandatory executive surfaces

Drawing from `OWNERSHIP_LAYER_DISCOVERY_AUDIT.md §C.4` and operator-named priorities, ForgedOps must provide these 8 Action Console surfaces at minimum for executive operability:

| # | Surface | Maps to |
|---|---|---|
| 1 | **PM Portfolio Action Console** | G1-2 + G1-3 |
| 2 | **Project Risk Lens** | G1-3 |
| 3 | **Operations Manager Action Console** | G1-1 |
| 4 | **Safety Action Console** | G1-1 + G1-6 |
| 5 | **Fleet + DOT Action Console** | G1-7 + G1-8 |
| 6 | **Accounting/EX-1 Integration Surface** | EX-1 + Pay-App + CO + Lien-Waiver views |
| 7 | **HR Operational Surface** (field-side only · HR-side via HRIS) | OC-013 + OC-014 field-side |
| 8 | **"What's open across the platform that I own"** Action Console (Rule 3 self-view) | G1-14 |

All 8 surfaces follow the Action Console contract from §1. **Zero read-only dashboard tiles.**

---

## §5 · What executive visibility EXCLUDES

| Forbidden | Why |
|---|---|
| Read-only KPI dashboards | Override anti-checklist clause |
| "Print Board Packet" auto-generator with ack ride-along | V-13 Rule 11 violation |
| "Executive Inbox" of digests requiring ack | Rule 1 + Rule 11 violation |
| Multi-recipient executive blast emails | Rule 8 violation |
| Drill-down to record without action affordance | Anti-checklist + Rule 9 (Operator First) |
| External BI tool replacement (Tableau · Power BI · Looker) | Rule 9 — ForgedOps is operational, not BI; BI integrates via data export, not internal rebuild |
| "Weekly KPI Acknowledged" boolean (V-13) | Amendment 001 Rule 11 violation |

---

## §6 · Mobile vs desktop posture

Executive Action Consoles must work on mobile (executives travel) but with the same Action Console contract — no read-only tiles, no dashboards. Mobile UX defaults:

| Mobile pattern | Posture |
|---|---|
| Per-row swipe actions (left = escalate-skip-hop · right = request 1:1) | Permitted · one-tap equivalent |
| Tap row → action sheet (open · escalate · request review) | Permitted |
| Drill into record then back to console | Permitted (the record IS the action context) |
| Pull-to-refresh | Permitted |
| Charts / sparklines | Permitted only as row metadata, never as standalone tile |

---

## §7 · Executive visibility ≠ executive ownership

A subtle but critical distinction:

* Executive **visibility** = sees the rows that need attention
* Executive **ownership** = becomes the new accountable party for a record (via skip-hop or natural escalation)

The Action Console pattern blends these: visibility surfaces records that need action; tapping the action affordance optionally transfers ownership. Executives can choose to acknowledge they've seen (informational pass-through) or escalate-to-self (take ownership). The platform never assigns ownership to an executive automatically without their explicit action.

---

## §8 · Discipline scorecard

| Check | Status |
|---|---|
| Zero code | ✅ |
| Zero design | ✅ |
| Action Console contract defined | ✅ |
| Per-workflow executive surfaces enumerated | ✅ |
| Portfolio rollup defined | ✅ |
| 8 mandatory surfaces named | ✅ |
| Forbidden patterns enumerated | ✅ |
| Mobile posture stated | ✅ |
| Override anti-checklist clause enforced throughout | ✅ |
| Rule 8 single-recipient discipline preserved | ✅ |
| Amendment 001 violations (V-13) explicitly excluded | ✅ |

🛑 **STOPPED.**
