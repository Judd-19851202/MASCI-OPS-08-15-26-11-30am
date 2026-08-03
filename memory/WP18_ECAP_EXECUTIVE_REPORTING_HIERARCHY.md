# WP18 ECAP Executive Reporting Hierarchy

Date: 2026-08-03

## Reporting law

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `SOURCE_VERIFIED` + `DOCUMENTED_ONLY`

Every executive KPI must have:

- one canonical source chain
- one formula
- one grain
- one freshness rule
- one confidence rule
- one drill-down path
- one owner
- one action expectation

No decorative executive number is allowed.

## Final rollup chains

| Domain | Final rollup chain | Proof label |
|---|---|---|
| Employee / labor | employee → crew/team → project → region/division → company | `SOURCE_VERIFIED` + `INFERENCE` |
| Equipment | equipment unit → fleet category/facility or project → region/division → company | `SOURCE_VERIFIED` + `INFERENCE` |
| Cost / quantity | cost code → work package / phase → project → region/division → company | `SOURCE_VERIFIED` + `INFERENCE` |
| Schedule | activity → work package / phase → project → region/division → company | `SOURCE_VERIFIED` + `INFERENCE` |
| Safety | event / inspection / meeting / action → project → division/company | `SOURCE_VERIFIED` + `INFERENCE` |
| QA/QC | inspection / deficiency / acceptance → project → division/company | `DOCUMENTED_ONLY` + `INFERENCE` |
| Transportation | assignment / haul cycle / fleet event → dispatch/facility/project → region/division/company | `SOURCE_VERIFIED` + `INFERENCE` |
| Shop | work order / repair event / unit status → facility/fleet → region/division/company | `SOURCE_VERIFIED` + `INFERENCE` |
| HR / qualification | employee qualification / lifecycle event → employee → department / project / company | `SOURCE_VERIFIED` + `INFERENCE` |
| Financial | transaction / budget line / commitment / actual / EV measure → cost code / phase → project → division/company | `PARTIAL_EVIDENCE` + `INFERENCE` |

## Executive reporting surface hierarchy

| Surface | Final role | Disposition | Proof label |
|---|---|---|---|
| Canonical KPI dictionary | formula and naming authority | `PRESERVE_AND_GOVERN` | `DOCUMENTED_ONLY` |
| ODS / executive intelligence | primary high-level executive rollup surface | `REFACTOR_IN_PLACE` | `SOURCE_VERIFIED` |
| Project Health | project-level derived drill-down and attention view | `PRESERVE_AND_GOVERN` | `SOURCE_VERIFIED` |
| Operational KPI routes | domain-specific drill-down consumers | `EXTEND` | `SOURCE_VERIFIED` |
| Legacy operational intelligence digest | deprecated duplicate lane | `RETIRE` | `SOURCE_VERIFIED` |

## KPI governance rules

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `DOCUMENTED_ONLY`

1. No KPI may mix financial truth with non-financial proxy fields under one label.
2. Every KPI must state its freshness, confidence, and limitations.
3. Every executive number must drill back to a governed detail path.
4. Executive reporting may summarize authority; it may not become authority.

## Authoritative dictionary

Authoritative KPI definitions live in `WP18_ECAP_EXECUTIVE_FINANCIAL_KPI_DICTIONARY.csv` for financial KPIs and in the accepted reporting hierarchy for non-financial rollups.