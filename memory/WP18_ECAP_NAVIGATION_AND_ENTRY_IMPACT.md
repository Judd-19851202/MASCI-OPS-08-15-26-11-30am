# WP18 ECAP Navigation and Entry Impact

Date: 2026-08-03

## Final decision

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `DOCUMENTED_ONLY`

WP-18C preserves the existing portal and shell structure.  
New controls functionality must enter through existing role-appropriate paths rather than spawning new parallel shells.

## Navigation rules

1. Budget, forecast, and EV views enter through existing PM, executive, finance/admin, and project-controls paths.
2. Field-facing users do not receive finance/control complexity beyond their role need.
3. Dispatch, shop, HR, safety, and QA/QC keep their current entry architecture.
4. Every new route must identify its parent shell, operator audience, completion state, and return path.

## No hidden capability rule

All new operator-visible capability must have:

- a discoverable entry path
- a governed role audience
- a return path
- testable screenshot proof during WP-18C acceptance

## Navigation impact summary

| Area | Impact |
|---|---|
| PM navigation | additive project-controls tabs / flows only |
| Executive navigation | hierarchy cleanup, not shell replacement |
| Admin / finance navigation | additive budget/actual/EV governance paths |
| Field / public navigation | preserved simple entry architecture |
| Dispatch / shop / HR / safety navigation | preserved existing shells with additive cross-links only |