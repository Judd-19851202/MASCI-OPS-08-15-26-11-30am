# WP18 ECAP Schedule, Lookahead, and Actuals Architecture

Date: 2026-08-03

## Final decision

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `SOURCE_VERIFIED` + `DOCUMENTED_ONLY`

The existing schedule engine is preserved and extended into a governed schedule/actuals architecture.

## Final schedule authority model

| Concept | Final rule |
|---|---|
| Master CPM authority | one canonical activity model per project |
| Imported vs native schedule | both allowed, but both must resolve to one canonical activity identifier set |
| Baseline schedule | immutable approved baseline snapshot |
| Current schedule | active reviewed current-state schedule |
| Forecast schedule | reviewed forecast derived from progress, constraints, and overrides |
| Activity identifiers | canonical `activity_id` / `cpm_activity_id` binding only |
| Work package binding | activities may bind to work package and cost-code context |

## Lookahead architecture

**Proof label:** `SOURCE_VERIFIED` + `INFERENCE`

Lookahead is extracted from the governed current / forecast schedule and must retain:

- week horizon
- responsible crew / role
- prerequisite constraints
- planned quantity / work package context
- commitment state
- field readiness notes

## Daily Reports to schedule rules

Daily Reports may contribute candidate evidence for:

- actual start
- actual finish
- installed quantity
- crew / equipment effort
- delay / impact notes
- field constraints
- candidate percent complete

### Non-overwrite law

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `DOCUMENTED_ONLY`

Daily Reports may **not** silently overwrite schedule truth.  
They feed the schedule review queue, and approved schedule updates are applied through governed review.

## Revision and audit rules

| Object | Rule |
|---|---|
| baseline revision | preserves previous baseline history |
| current schedule change | records who changed what and why |
| forecast change | preserved as forecast lineage |
| lookahead publication | versioned by week / review cycle |
| constraint impact | linked to the originating constraint event |

## Final schedule determination

Schedule authority is fully decided for WP-18C.  
The architecture extends the existing schedule engine rather than replacing it.