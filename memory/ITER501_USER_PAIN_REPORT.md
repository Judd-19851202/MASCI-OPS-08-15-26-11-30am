# ITER501 · USER PAIN REPORT

**Date**: 2026-06-02T21:02 UTC
**Mode**: READ-ONLY synthesis
**Source**: ITER500 Role-Based Friction Report + User Confusion Register + Top 25 Remaining Issues

---

## Scoring legend

Each issue scored 1 – 10 on 9 dimensions:

* **BI** Business Impact
* **UF** User Frequency
* **UFr** User Frustration
* **C2** Customer #2 Impact
* **WL** White Label Impact
* **OR** Operational Risk
* **GR** Governance Risk
* **IC** Implementation Complexity (10 = trivial, 1 = enormous)
* **ROI** Expected ROI

Composite ROI bias: high-frequency × high-frustration × low-complexity → highest score.

---

## Top 25 scored

| # | Issue | BI | UF | UFr | C2 | WL | OR | GR | IC | ROI |
|--:|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 1 | OC-005 JHP Acknowledgement Ledger | 9 | 6 | 6 | 8 | 6 | 8 | 9 | 3 | 7 |
| 2 | Approve / Reject hidden in dropdowns (Dispatch + PO + Time-off) | 9 | 9 | 8 | 8 | 7 | 7 | 6 | 8 | **9** |
| 3 | Reopen hidden in kebab (Incident / QA/QC / Site Inspection) | 8 | 7 | 8 | 7 | 6 | 6 | 7 | 8 | **9** |
| 4 | Universal undo / status reversal verb | 8 | 7 | 9 | 7 | 6 | 7 | 8 | 4 | 7 |
| 5 | Reactivate vs Rehire dual-path | 7 | 4 | 8 | 6 | 5 | 6 | 7 | 9 | 8 |
| 6 | Verb harmonization (Save/Submit/Create) | 6 | 10 | 7 | 9 | 8 | 4 | 4 | 5 | 7 |
| 7 | "Closed" semantic drift across modules | 7 | 8 | 8 | 8 | 7 | 5 | 5 | 4 | 6 |
| 8 | 5 statuses for "not currently working" | 7 | 5 | 8 | 7 | 6 | 5 | 7 | 5 | 6 |
| 9 | Daily Report "Open" status confusion | 6 | 9 | 7 | 6 | 5 | 5 | 4 | 7 | 7 |
| 10 | Constraint Resolve vs Close | 6 | 6 | 7 | 6 | 5 | 5 | 5 | 7 | 6 |
| 11 | Incident dual lifecycle / is_closed fields | 7 | 4 | 6 | 5 | 4 | 7 | 7 | 6 | 6 |
| 12 | HR Queue pending vs needs_review | 6 | 5 | 7 | 5 | 4 | 5 | 6 | 8 | 7 |
| 13 | Equipment expires_at ambiguity | 6 | 7 | 6 | 6 | 5 | 6 | 6 | 7 | 7 |
| 14 | Driver-qualification expiring-soon flag missing | 8 | 6 | 6 | 7 | 6 | 8 | 8 | 9 | **9** |
| 15 | Time-off approval verb (vs checkbox) | 6 | 7 | 7 | 6 | 5 | 5 | 6 | 8 | 8 |
| 16 | Asset-transfer receive verb (vs checkbox) | 5 | 5 | 6 | 5 | 4 | 6 | 5 | 8 | 7 |
| 17 | Dispatch drag-drop per-row toast | 5 | 8 | 8 | 5 | 5 | 4 | 3 | 10 | **9** |
| 18 | PO reject reason required | 6 | 5 | 5 | 6 | 5 | 6 | 8 | 8 | 7 |
| 19 | Admin audit-log filter chip-stack | 5 | 6 | 7 | 6 | 5 | 5 | 7 | 8 | 7 |
| 20 | Hub re-grouping (Hub / AdminHub / PmHub) | 7 | 10 | 7 | 9 | 8 | 4 | 4 | 6 | 8 |
| 21 | PM Crew Compliance discoverability | 6 | 6 | 6 | 6 | 5 | 5 | 6 | 8 | 7 |
| 22 | Constraint LifecyclePanel substrate (Rank #2) | 6 | 5 | 6 | 5 | 4 | 5 | 6 | 9 | 8 |
| 23 | Sub/Vendor archive workflow | 6 | 4 | 6 | 6 | 5 | 6 | 7 | 6 | 6 |
| 24 | Notifications digest opt-in + save banner | 5 | 5 | 6 | 6 | 6 | 5 | 5 | 8 | 7 |
| 25 | FleetDVIR fail/amend path | 6 | 6 | 7 | 5 | 4 | 7 | 6 | 5 | 6 |

ROI ≥ 9 (the highest-leverage residual): **#2, #3, #14, #17**.
ROI = 8 (one tier down): #5, #6 (frequency-weighted), #15, #20, #22.

---

## User pain by role

### HR (1 user per customer · governance owner)
* Reactivate vs Rehire confusion (#5) — high
* HR Queue pending vs needs_review (#12) — medium
* 5 "not working" statuses (#8) — medium
* Universal undo (#4) — high (recovery-from-mistakes pain)

### Safety (1–2 users · audit-grade)
* OC-005 JHP ledger missing (#1) — high
* Reopen hidden in kebab (#3) — high (Incident detail page)
* Driver-qualification expiring-soon (#14) — high
* Notifications digest opt-in (#24) — low

### Superintendent (~5 users)
* Reopen hidden (#3) — medium (Site Inspection detail)
* Daily Report "Open" confusion (#9) — high
* Constraint Resolve vs Close (#10) — medium
* Hub sprawl (#20) — high (they touch many surfaces)

### Foreman / Field Leadership (~25 users · highest count by headcount)
* Daily Report "Open" confusion (#9) — high (this is the #1 most-filed form)
* Verb harmonization (#6) — medium (every form)
* Asset transfer receive (#16) — low frequency
* FleetDVIR fail/amend (#25) — medium

### PM (~5 users)
* PM Crew Compliance discoverability (#21) — high
* Approve/Reject dropdowns (#2) — high (PO requests live here)
* Hub re-grouping (#20) — high
* Time-off approval (#15) — medium

### Payroll (~1–2 users · weekly batch)
* Time-off approval verb (#15) — high
* "Closed" semantic drift on time-off vs pay-period (#7) — high
* Verb harmonization (#6) — low

### Operations / Dispatch (~2 users · daily)
* Dispatch drag-drop toast (#17) — high (every drag = uncertainty)
* Approve/Reject dropdowns (#2) — high (Dispatch approval flow)
* Reopen hidden (#3) — medium (closed dispatch records)

### Executive (1–2 users · weekly read-only)
* Hub re-grouping (#20) — medium
* Notifications digest (#24) — low
* Verb harmonization (#6) — low (don't notice it daily)

### Admin / Super-admin (1–2 users · monthly)
* Admin audit-log filter chip-stack (#19) — high
* Sub/Vendor archive (#23) — medium
* OC-005 ledger missing (#1) — high
* Universal undo (#4) — high (mistake-recovery)

---

## Per-issue user-pain answers

For each of the 25 issues:

| # | Notice immediately? | Generates support calls? | Generates confusion? | Reduces trust? |
|--:|:-:|:-:|:-:|:-:|
| 1 OC-005 | No (silent gap) | Maybe (Safety asks) | Medium | Low |
| 2 Approve/Reject dropdown | Yes | **Yes** | **High** | Medium |
| 3 Reopen kebab | Eventually | **Yes** | **High** | Medium |
| 4 Universal undo | On mistake | **Yes** | High | **High** |
| 5 Reactivate/Rehire | On rehire event | Yes | **High** | Medium |
| 6 Verb mix | Subtle | Low | **High** | Low |
| 7 "Closed" drift | Subtle | Medium | **High** | Medium |
| 8 5 statuses | On HR change | Yes | **High** | Medium |
| 9 DR "Open" | Daily | **High** | **High** | Medium |
| 10 Resolve vs Close | On constraint | Medium | High | Low |
| 11 Dual lifecycle field | Rare | Low | Medium | Low |
| 12 HR Queue states | On queue use | Medium | High | Low |
| 13 expires_at | On equipment | Medium | Medium | Low |
| 14 Driver-qual flag | On compliance | High | Medium | **High** |
| 15 Time-off verb | On approval | Medium | High | Medium |
| 16 Asset-transfer | On receive | Low | Medium | Low |
| 17 Dispatch toast | **Daily** | **High** | **High** | Medium |
| 18 PO reject reason | On reject | Low | Medium | Medium |
| 19 Audit-log filter | On audit | Medium | High | Low |
| 20 Hub sprawl | **Daily** | Medium | **High** | Medium |
| 21 PM Crew Compliance | Weekly | Medium | High | Low |
| 22 Constraint Lifecycle | Subtle | Low | Medium | Low |
| 23 Sub/Vendor archive | Rare | Medium | Medium | Medium |
| 24 Notifications | Subtle | Low | Medium | Medium |
| 25 FleetDVIR fail/amend | Weekly | Medium | Medium | Medium |

---

## Top frustration drivers (synthesized)

1. **Buttons hidden behind dropdowns** (#2) — every PM/Dispatch/Safety hits this multiple times per day.
2. **Reopen hidden in kebab** (#3) — closing-the-loop pain on every lifecycle-bearing record.
3. **Dispatch drag-drop without toast** (#17) — the entire dispatcher day is a series of "did that take?" moments.
4. **Daily Report "Open"** (#9) — every foreman, every day, asks "did my report go through?"
5. **Hub sprawl** (#20) — every non-HR user wades through alphabetized tile walls.

---

End of pain report.
