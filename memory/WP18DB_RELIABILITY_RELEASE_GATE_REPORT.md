# WP-18DB Reliability Release Gate Report

## Gate result

- Target: `preview`
- Final decision in the closeout window: `PASS`
- Failed gates: `none`

## Permanent gate changes completed in WP-18DB

1. **Detached preview workspace source authority recognized safely**
   - Preview release gating now accepts a clean governed Emergent workspace pre-save candidate even when git branch identity is detached.

2. **WP-18DA performance budgets are now enforced**
   - `memory/WP18DA_PERFORMANCE_BUDGET_REGISTER.csv` is part of the permanent gate.
   - Missing required budget keys or any non-`PASS` budget row now blocks certification.

3. **Governed pre-save dirty inventory improved**
   - Pattern-based governed dirty entries now support runtime-created drill reports without invalidating preview source authority.

## Runtime evidence referenced by the gate bundle

- Health probe contract tests: passing
- Runtime reliability tests: passing
- Scheduler hardening tests: passing
- Restore certification evidence tests: passing
- Preview smoke screenshot: passing (page loads, non-blank shell)

## Important note

The release gate is currently green even though preview backup trust remains `AMBER`; the amber condition is explicitly explained by runtime truth as a preview safety lock on hourly complete-R2 plus historical 7-day failure penalties, not by loss of the latest complete archive or restore proof.

## Conclusion

The preview reliability release gate is now permanently stricter than it was at the start of WP-18DB and passed in the final closeout evidence window.