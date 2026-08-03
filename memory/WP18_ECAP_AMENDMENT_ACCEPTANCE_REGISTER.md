# WP18 ECAP Amendment Acceptance Register

Date: 2026-08-03

## Register purpose

**Proof label:** `DOCUMENTED_ONLY`

This register converts every required BR3 amendment into one explicit executive implementation contract decision.

## Amendment register

| Amendment ID | Title | Proof label | Exact issue | Required constitutional decision | Accepted disposition | What remains unchanged | What changes | Implementation impact | Operational impact | Affected domains | Dependencies | Risks | Acceptance criteria | Blocks WP-18C | Executive acceptance status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A01 | Enterprise hierarchy propagation | `SOURCE_VERIFIED` | governance knows enterprise scope but some readers still default to MASCI-only assumptions | extend existing governance hierarchy into downstream readers/config inheritance | `EXTEND` | governance registry, project identity, existing role portals | downstream readers must consume governed scope consistently | medium | high positive at enterprise scale | governance, ODS, KPI, AI, reporting | none | scope ambiguity if skipped | hierarchy constitution accepted; reporting consumers mapped; no duplicate hierarchy owner | Yes | `ACCEPTED` |
| A02 | Executive reporting hierarchy | `SOURCE_VERIFIED` | ODS, Project Health, KPI rollups, and legacy intelligence overlap | establish one reporting hierarchy and KPI dictionary; refactor readers in place | `REFACTOR_IN_PLACE` + `RETIRE` (legacy digest) | upstream facts and readers remain | one hierarchy governs formulas, freshness, drill-down, and visibility | medium | high positive for executive trust | executive reporting, KPI, ops intelligence | A01 | semantic drift if skipped | reporting hierarchy accepted; KPI dictionary accepted; legacy lane explicitly retired | Yes | `ACCEPTED` |
| A03 | Budget Hierarchy | `PARTIAL_EVIDENCE` | no canonical budget baseline owner exists | build a net-new Budget Hierarchy over preserved upstream truth | `BUILD_NEW` | cost codes, P&L snapshot, PO workflow, daily reports, project identity remain | budget-specific ownership/versioning/rollups become explicit | high | very high positive for financial trust | finance, PM, exec, procurement | A01, A02 | fake budget truth if skipped | budget constitution accepted with ownership, hierarchy, formulas, permissions, and rollups | Yes | `ACCEPTED_WITH_CONDITIONS` |
| A04 | Earned Value | `NOT_FOUND` + `INFERENCE` | no EV engine exists | build EV only as derived layer after budget and source approvals exist | `BUILD_NEW` | schedule, cost-code, production, daily reports remain | EV metrics and exception handling become explicit | high | high positive for project controls | finance, PM, exec, controls | A03 | false precision if skipped or rushed | EV blueprint accepted; formulas/inputs/thresholds/drill-downs fixed | Yes | `ACCEPTED_WITH_CONDITIONS` |
| A05 | Resource federation | `SOURCE_VERIFIED` | demand, roster, and deployment are connected but semantically split | consolidate the federation contract without replacing existing subsystems | `CONSOLIDATE` | planning, roster, dispatch, portals remain | one resource meaning and escalation chain is documented | medium | high positive for operations | PM, dispatch, HR, field, exec | A01 | operator confusion if skipped | resource ownership, handoffs, and escalation model accepted | Yes | `ACCEPTED` |
| A06 | Constraint federation | `SOURCE_VERIFIED` | daily field constraints and standing blockers both exist | extend with one explicit dual-lane constraint model | `EXTEND` | both current capture lanes remain | downstream consumers must read both lanes correctly | medium | medium-high positive | PM, field, safety, exec | A05 | underreported delay/constraint truth | constraint model accepted; event flow and ownership documented | Yes | `ACCEPTED` |
| A07 | Preservation-first / no rebuild | `DOCUMENTED_ONLY` | future implementation could replace validated systems without evidence | protect identified subsystems unless reopening trigger is met | `PRESERVE_EXACTLY` / `PRESERVE_AND_GOVERN` | validated platform value | implementation is contractually constrained | low | very high positive | platform-wide | none | wasteful churn if skipped | no-rebuild register complete and accepted | Yes | `ACCEPTED` |
| A08 | AI authority boundary | `SOURCE_VERIFIED` + `DOCUMENTED_ONLY` | AI exists as assistive capability and must not silently become authority | define explicit allowed and forbidden AI actions | `PRESERVE_AND_GOVERN` | config, translation, briefing assist remain | AI authority boundary becomes explicit and auditable | low | high positive | AI, admin, exec, field, HR, safety | A02 | silent AI authority creep if skipped | AI authority constitution accepted | Yes | `ACCEPTED` |
| A09 | P&L / PO trust boundary | `SOURCE_VERIFIED` | P&L snapshot and PO amounts are useful but not budget authority | preserve both as inputs and derived views only | `PRESERVE_AND_GOVERN` | current pages/endpoints and workflows | financial truth boundary is explicit | low | medium positive | finance, PM, procurement | A03 | accidental duplicate budget owner if skipped | source-of-truth map accepted with PO/P&L boundaries | Yes | `ACCEPTED` |
| A10 | Legacy executive digest retirement | `SOURCE_VERIFIED` | legacy operational intelligence duplicates newer readers | retire after hierarchy acceptance | `RETIRE` | newer readers and upstream facts remain | old lane is marked deprecating/non-authoritative | low | medium positive | executive reporting | A02 | duplicated executive meaning if skipped | retirement register complete | No | `ACCEPTED` |

## Register result

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `DOCUMENTED_ONLY`

- blocking amendments accepted: `9`
- accepted with conditions: `2` (`Budget Hierarchy`, `Earned Value` sequencing conditions)
- unresolved blocking amendments: `0`

Therefore, the amendment register does **not** block WP-18C authorization.