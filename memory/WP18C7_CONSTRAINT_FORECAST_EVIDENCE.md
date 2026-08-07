# WP18C7 Constraint Forecast Evidence

## Authority
- `operational_constraints`

## C7 behavior
- Open constraints are surfaced as explicit forecast drivers.
- Constraint count is visible in FL constrained view.
- Weather remains excluded as a direct forecast driver when no governed weather source is linked.

## Truthfulness guardrail
- Constraint pressure lowers confidence; it does not silently rewrite commitments.
