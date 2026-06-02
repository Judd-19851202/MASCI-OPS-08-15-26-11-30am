# ITER501 · TOP 25 REMAINING ISSUES

**Date**: 2026-06-02T21:00 UTC
**Authority**: OMEGA ITER501 — Top Remaining Operational Gaps Analysis
**Mode**: READ-ONLY synthesis · no code · no fixes · no deploy
**Source**: ITER500 audit suite (10 reports) + Rank #1 deliverables + post-deploy certification + 1200+ historical memory docs

---

## Scope reminder

This list is the prioritized residual after **Rank #1 is shipped + targeted-correction applied + production certified on observable surface**. Items 1–6 of the Top 25 Discoverability failures (Save below fold on 6 form pages) are therefore **already retired** and removed from this list. What remains is the next 25.

---

## Top 25 (ranked by composite value · 1 = highest)

| # | Issue | Source | Status |
|--:|---|---|---|
| 1 | **OC-005 JHP Acknowledgement Ledger** — not built; the operator authorization workflow for JHP / Job Hazard Posting sign-off has no ledger surface; signal-only flags exist but cannot be acknowledged or audited end-to-end | DEAD_END #1 · iter454 backlog | **Tier 1 dead-end** |
| 2 | **Approve / Reject hidden in dropdown menus** on Dispatch + PO requests + Time-off | DISCOVERABILITY #7 #8 #17 | **Top discoverability** |
| 3 | **Lifecycle "Reopen" hidden in kebab** on Incident, QA/QC, Site Inspection detail pages — there is no top-level Reopen verb; users believe closure is final | DISCOVERABILITY #9 #10 #11 + DEAD_END #11 | **Top discoverability** |
| 4 | **Universal "undo a status change"** — no in-app reversal verb on any lifecycle; mistakes require backend ticket | DEAD_END #2 | **Tier 1 dead-end** |
| 5 | **Reactivate vs Rehire dual-path** confusion on Inactive → Active employee transitions | DEAD_END #16 + FRICTION #4 | High HR friction |
| 6 | **Verb inconsistency** — Save / Submit / Create / File / Send used interchangeably across the platform; same action, different word per page | FRICTION #1 | **Top friction** |
| 7 | **"Closed" means different things** across QA/QC vs Inspection vs Incident vs Constraint vs Daily Report | FRICTION #25 | Cross-module semantic drift |
| 8 | **5 statuses for "not currently working"** (Inactive / Suspended / Leave of Absence / Terminated / Resigned) — operators cannot remember which to use | FRICTION #2 | High HR friction |
| 9 | **Daily Report submit → "Open" status** until shop confirms; foremen think the report failed | FRICTION #5 | High DR friction |
| 10 | **Constraint Resolve vs Close** — same module, two near-identical verbs with different downstream effects | FRICTION #7 + DEAD_END #15 | Cross-domain |
| 11 | **Incident `lifecycle_state` + `is_closed` dual field** — operators can produce contradictory states | FRICTION #8 | Data-integrity adjacent |
| 12 | **HR Queue pending vs needs_review** — two queue states with no clear delta | FRICTION #17 + DEAD_END #17 | HR mid-frequency |
| 13 | **Equipment `expires_at` ambiguity** — does "expires" mean inspection or registration? | FRICTION #11 | Fleet / shop |
| 14 | **Driver-qualification expiring-soon visual flag missing** in the dashboard | DEAD_END #24 | Compliance risk |
| 15 | **Time-off approval as table checkbox, no toast / no verb** | FRICTION #10 + DEAD_END #7 + DISCOVERABILITY #17 | Payroll / HR |
| 16 | **Asset-transfer receive as subtle checkbox, no verb / no tri-state UX** | FRICTION #13 + DEAD_END #8 + DISCOVERABILITY #18 | Logistics |
| 17 | **Dispatch crew drag-drop** has no per-row toast — dispatcher can't tell if the move stuck | DEAD_END #10 | Dispatch |
| 18 | **PO request reject** with no required reason field — auditability gap | DEAD_END #9 | Procurement |
| 19 | **Admin audit-log "filter active" chip-stack missing** — long lists, no visible filter state | DEAD_END #18 + DISCOVERABILITY #13 | Admin friction |
| 20 | **Hub tile sprawl** (`Hub.jsx` 587 lines · no grouping); AdminHub (133 lines · alphabetical · 35+ pages) | DISCOVERABILITY #19 #20 | Cross-role |
| 21 | **PM Crew Compliance pages buried in PmHub** — high-value monitoring buried in nav | DISCOVERABILITY #22 | PM |
| 22 | **Constraint module flat detail page** — no LifecyclePanel substrate (Rank #2 candidate) | DISCOVERABILITY #23 | Constraint module |
| 23 | **Sub/Vendor archive workflow doesn't exist** — operators can't retire a sub cleanly | DEAD_END #12 + FRICTION #16 + DISCOVERABILITY #24 | Procurement / governance |
| 24 | **Notifications digest config opt-in buried** in admin · no save banner · users don't know if it took | DEAD_END #13 + DEAD_END #20 + DISCOVERABILITY #25 | Cross-role |
| 25 | **FleetDVIR pass-with-defects without explicit fail state** + no post-submit edit/amend path | FRICTION #9 + DEAD_END #11 | Fleet ops |

---

## Distribution of issue classes

| Class | Count |
|---|---:|
| Discoverability / button visibility | 7 |
| Workflow gap / dead-end | 8 |
| Semantic / terminology drift | 5 |
| HR / Lifecycle specific | 4 |
| Compliance / audit | 3 |
| Logistics / fleet | 3 |
| (Multi-class overlap — sum > 25 by design) | |

## Affected modules

Daily Report · Incident · QA/QC · Site Inspection · HR Lifecycle · HR Queue · Time-off · Asset Transfer · Dispatch · PO Requests · Constraint · Equipment · Driver Qualification · Sub/Vendor · Notifications Digest · Audit Log · FleetDVIR · Hubs (Hub.jsx, AdminHub.jsx, PmHub.jsx) · JHP

---

End of Top 25.
